#!/usr/bin/env python3
"""
Construtor de Aulas CAEd - CLI
Pipeline: .docx → mammoth → Claude API → Jinja2 → HTML

Uso:
    python construtor_cli.py aula.docx --profile default -o aula.html
    python construtor_cli.py aula.docx --list-profiles
    python construtor_cli.py aula.docx --mock  # teste sem API
"""

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import mammoth
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Opcional: só importa anthropic se não estiver em modo mock
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
PROFILES_DIR = BASE_DIR / "profiles"

# Componentes suportados nesta versão
SUPPORTED_COMPONENTS = ["citacao", "atencao", "carrossel", "sanfona", "flipcards"]

# Tags que indicam início/fim de componentes no .docx
COMPONENT_TAGS = {
    "citacao": ("citacao", None),
    "atencao": ("atencao", None),
    "carrossel": ("carrossel", "carrosselslide"),
    "sanfona": ("sanfona", "sanfonasecao"),
    "flipcards": ("flipcards", "flipcard"),
}


# =============================================================================
# CARREGAMENTO DE PROFILES
# =============================================================================

def list_profiles() -> list[str]:
    """Lista todos os profiles disponíveis."""
    profiles = []
    for f in PROFILES_DIR.glob("*.json"):
        profiles.append(f.stem)
    return sorted(profiles)


def load_profile(name: str) -> dict:
    """Carrega um profile por nome."""
    path = PROFILES_DIR / f"{name}.json"
    if not path.exists():
        available = list_profiles()
        raise FileNotFoundError(
            f"Profile '{name}' não encontrado.\n"
            f"Disponíveis: {', '.join(available) or 'nenhum'}"
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# EXTRAÇÃO DO DOCX
# =============================================================================

def extract_html_from_docx(docx_path: str) -> str:
    """Extrai HTML do .docx usando mammoth."""
    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(f)
    
    html = result.value
    
    # Limpa shortcodes envolvidos em <p> (mesmo tratamento do React)
    def clean_shortcode_wrappers(html: str) -> str:
        pattern = r'<p>(.*?)</p>'
        
        def replacer(match):
            content = match.group(1).strip()
            # Se é um shortcode (começa com < e termina com >), remove o <p>
            if content.startswith('&lt;') and content.endswith('&gt;'):
                return match.group(1)
            return match.group(0)
        
        return re.sub(pattern, replacer, html, flags=re.DOTALL)
    
    html = clean_shortcode_wrappers(html)
    
    # Decodifica entidades HTML
    import html as html_module
    html = html_module.unescape(html)
    
    return html


# =============================================================================
# PROMPT PARA CLAUDE API
# =============================================================================

EXTRACTION_PROMPT = '''Analise o HTML de um documento educacional e extraia seus elementos na ORDEM EXATA em que aparecem no documento.

COMPONENTES SUPORTADOS:
- citacao: bloco de citação
- atencao: caixa de destaque "Atenção"
- carrossel: slides navegáveis (contém <carrosselslide>)
- sanfona: accordion expansível (contém <sanfonasecao> com <sanfonasecaocabecalho> e <sanfonasecaocorpo>)
- flipcards: cards que viram (contém <flipcard> com <flipcardfront> e <flipcardback>)

REGRAS DE EXTRAÇÃO:
1. Preserve TODO o HTML interno dos componentes e dos blocos de texto (tags, classes, atributos)
2. Gere IDs únicos para componentes (formato: "tipo-xxxx")
3. Para componentes com subcomponentes, extraia a hierarquia completa
4. Blocos de texto entre componentes devem ser incluídos na lista como itens do tipo "texto"
5. A lista "itens" deve refletir a sequência real do documento — não agrupe texto separado

DOCUMENTO HTML:
```
{html_content}
```

RETORNE APENAS JSON VÁLIDO (sem markdown, sem explicações):
{{
  "itens": [
    {{
      "tipo": "texto",
      "html": "<p>Parágrafo antes do primeiro componente...</p>"
    }},
    {{
      "tipo": "citacao",
      "id": "citacao-001",
      "dados": {{
        "conteudo": "<p>Texto da citação...</p>"
      }}
    }},
    {{
      "tipo": "texto",
      "html": "<p>Parágrafo entre componentes...</p>"
    }},
    {{
      "tipo": "carrossel",
      "id": "carrossel-001",
      "dados": {{
        "slides": [
          {{"conteudo": "<p>Slide 1...</p>"}},
          {{"conteudo": "<p>Slide 2...</p>"}}
        ]
      }}
    }},
    {{
      "tipo": "texto",
      "html": "<p>Parágrafo após o último componente...</p>"
    }},
    {{
      "tipo": "sanfona",
      "id": "sanfona-001",
      "dados": {{
        "secoes": [
          {{
            "cabecalho": "<p>Título da seção</p>",
            "corpo": "<p>Conteúdo expandido...</p>"
          }}
        ],
        "fonte": "<p>Fonte opcional</p>"
      }}
    }},
    {{
      "tipo": "flipcards",
      "id": "flipcards-001",
      "dados": {{
        "cards": [
          {{
            "frente": "<p>Título do card</p>",
            "verso": "<p>Descrição do verso</p>",
            "aria_label": "Descrição acessível"
          }}
        ]
      }}
    }}
  ]
}}
'''


def extract_with_claude(html: str, api_key: str | None = None) -> dict:
    """Usa Claude API para extrair dados estruturados do HTML."""
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("Módulo 'anthropic' não instalado. Use: pip install anthropic")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = EXTRACTION_PROMPT.format(html_content=html)
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    # Limpa possíveis wrappers de markdown
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude retornou JSON inválido: {e}\nResposta: {response_text[:500]}...")


def extract_mock(html: str) -> dict:
    """Extração mock para testes sem API.

    Encontra todos os componentes com suas posições no HTML, ordena por
    posição de início e intercala os segmentos de texto entre eles —
    preservando a ordem exata do documento.
    """
    patterns = {
        "citacao":  r'<citacao[^>]*>(.*?)</citacao>',
        "atencao":  r'<atencao[^>]*>(.*?)</atencao>',
        "carrossel": r'<carrossel[^>]*>(.*?)</carrossel>',
        "sanfona":  r'<sanfona[^>]*>(.*?)</sanfona>',
        "flipcards": r'<flipcards[^>]*>(.*?)</flipcards>',
    }

    # Coleta todos os matches com posição no documento
    all_matches: list[tuple[int, int, str, str]] = []
    for tipo, pattern in patterns.items():
        for m in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
            all_matches.append((m.start(), m.end(), tipo, m.group(1)))

    # Ordena por posição de início — garante ordem do documento
    all_matches.sort(key=lambda x: x[0])

    itens: list[dict] = []
    cursor = 0

    for start, end, tipo, conteudo in all_matches:
        # Texto antes deste componente
        segmento = html[cursor:start].strip()
        if segmento:
            itens.append({"tipo": "texto", "html": segmento})

        dados = parse_component_content(tipo, conteudo)
        itens.append({
            "tipo": tipo,
            "id": f"{tipo}-{uuid.uuid4().hex[:6]}",
            "dados": dados,
        })
        cursor = end

    # Texto após o último componente
    segmento = html[cursor:].strip()
    if segmento:
        itens.append({"tipo": "texto", "html": segmento})

    return {"itens": itens}


def parse_component_content(tipo: str, conteudo: str) -> dict:
    """Parse do conteúdo interno de cada tipo de componente."""
    
    if tipo == "citacao":
        return {"conteudo": conteudo.strip()}
    
    elif tipo == "atencao":
        return {"conteudo": conteudo.strip()}
    
    elif tipo == "carrossel":
        slides = []
        for match in re.finditer(r'<carrosselslide[^>]*>(.*?)</carrosselslide>', conteudo, re.DOTALL | re.IGNORECASE):
            slides.append({"conteudo": match.group(1).strip()})
        return {"slides": slides} if slides else {"slides": [{"conteudo": conteudo.strip()}]}
    
    elif tipo == "sanfona":
        secoes = []
        for match in re.finditer(r'<sanfonasecao[^>]*>(.*?)</sanfonasecao>', conteudo, re.DOTALL | re.IGNORECASE):
            secao_content = match.group(1)
            
            cabecalho_match = re.search(r'<sanfonasecaocabecalho[^>]*>(.*?)</sanfonasecaocabecalho>', secao_content, re.DOTALL | re.IGNORECASE)
            corpo_match = re.search(r'<sanfonasecaocorpo[^>]*>(.*?)</sanfonasecaocorpo>', secao_content, re.DOTALL | re.IGNORECASE)
            
            secoes.append({
                "cabecalho": cabecalho_match.group(1).strip() if cabecalho_match else "",
                "corpo": corpo_match.group(1).strip() if corpo_match else ""
            })
        
        # Verifica se há fonte
        fonte_match = re.search(r'<sanfonafonte[^>]*>(.*?)</sanfonafonte>', conteudo, re.DOTALL | re.IGNORECASE)
        fonte = fonte_match.group(1).strip() if fonte_match else None
        
        result = {"secoes": secoes}
        if fonte:
            result["fonte"] = fonte
        return result
    
    elif tipo == "flipcards":
        cards = []
        for match in re.finditer(r'<flipcard[^>]*>(.*?)</flipcard>', conteudo, re.DOTALL | re.IGNORECASE):
            card_content = match.group(1)
            
            front_match = re.search(r'<flipcardfront[^>]*>(.*?)</flipcardfront>', card_content, re.DOTALL | re.IGNORECASE)
            back_match = re.search(r'<flipcardback[^>]*>(.*?)</flipcardback>', card_content, re.DOTALL | re.IGNORECASE)
            
            cards.append({
                "frente": front_match.group(1).strip() if front_match else "",
                "verso": back_match.group(1).strip() if back_match else "",
                "aria_label": "Card informativo"
            })
        return {"cards": cards}
    
    return {"conteudo": conteudo}


# =============================================================================
# RENDERIZAÇÃO COM JINJA2
# =============================================================================

def create_jinja_env() -> Environment:
    """Cria ambiente Jinja2 configurado."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,  # HTML é confiável (vem do docx)
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_component(
    env: Environment, 
    tipo: str, 
    model: str, 
    version: str, 
    dados: dict,
    fallback: bool = True,
    verbose: bool = False
) -> str:
    """Renderiza um componente usando o template apropriado.
    
    Se fallback=True e o template específico não existir,
    tenta m1v1 como fallback.
    """
    template_path = f"{tipo}/{model}{version}.html"
    fallback_path = f"{tipo}/m1v1.html"
    
    try:
        template = env.get_template(template_path)
    except TemplateNotFound:
        if fallback and template_path != fallback_path:
            # Tenta fallback para m1v1
            try:
                template = env.get_template(fallback_path)
                if verbose:
                    print(f"   ⚠️  {tipo}: {model}{version} não encontrado, usando m1v1")
            except TemplateNotFound:
                available = list((TEMPLATES_DIR / tipo).glob("*.html"))
                available_str = ", ".join(f.stem for f in available) or "nenhum"
                raise TemplateNotFound(
                    f"Template não encontrado: {template_path}\n"
                    f"Fallback também falhou: {fallback_path}\n"
                    f"Disponíveis para '{tipo}': {available_str}"
                )
        else:
            available = list((TEMPLATES_DIR / tipo).glob("*.html"))
            available_str = ", ".join(f.stem for f in available) or "nenhum"
            raise TemplateNotFound(
                f"Template não encontrado: {template_path}\n"
                f"Disponíveis para '{tipo}': {available_str}"
            )
    
    return template.render(**dados)


def build_html_page(
    partes: list[str],
    profile: dict,
    titulo: str = "Aula"
) -> str:
    """Monta a página HTML final com assets.

    `partes` é uma lista de strings HTML já na ordem correta do documento
    (blocos de texto e componentes intercalados).
    """
    # Lê bundle de assets do profile
    css = profile.get("css", "")
    js = profile.get("js", "")

    css_tags = f'<link rel="stylesheet" href="{css}">' if css else ""
    js_tags = f'<script src="{js}"></script>' if js else ""

    # Monta conteúdo na ordem recebida
    conteudo = "\n\n".join(partes)
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    {css_tags}
</head>
<body>
    <main class="conteudo-aula">
        {conteudo}
    </main>
    {js_tags}
</body>
</html>
'''


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def process_document(
    docx_path: str,
    profile_name: str = "default",
    output_path: str | None = None,
    use_mock: bool = False,
    api_key: str | None = None,
    verbose: bool = False
) -> str:
    """Pipeline completo: .docx → HTML."""
    
    # 1. Carrega profile
    if verbose:
        print(f"📋 Carregando profile: {profile_name}")
    profile = load_profile(profile_name)
    
    # 2. Extrai HTML do .docx
    if verbose:
        print(f"📄 Extraindo HTML de: {docx_path}")
    html_raw = extract_html_from_docx(docx_path)
    
    if verbose:
        print(f"   → {len(html_raw)} caracteres extraídos")
    
    # 3. Extrai dados estruturados
    if use_mock:
        if verbose:
            print("🔧 Usando extração mock (sem API)")
        dados = extract_mock(html_raw)
    else:
        if verbose:
            print("🤖 Extraindo dados via Claude API...")
        dados = extract_with_claude(html_raw, api_key)
    
    n_componentes = sum(1 for i in dados.get("itens", []) if i["tipo"] != "texto")
    if verbose:
        print(f"   → {n_componentes} componentes encontrados")

    # 4. Renderiza itens na ordem do documento
    if verbose:
        print("🎨 Renderizando templates...")

    env = create_jinja_env()
    partes_html: list[str] = []

    for item in dados.get("itens", []):
        if item["tipo"] == "texto":
            partes_html.append(item["html"])
            continue

        tipo = item["tipo"]
        comp_id = item["id"]
        comp_dados = {**item["dados"], "id": comp_id}

        comp_config = profile.get("componentes", {}).get(tipo, {})
        model = comp_config.get("model", "m1")
        version = comp_config.get("version", "v1")

        try:
            html = render_component(env, tipo, model, version, comp_dados, fallback=True, verbose=verbose)
            partes_html.append(html)
            if verbose:
                print(f"   ✓ {tipo} ({model}{version})")
        except Exception as e:
            print(f"   ✗ Erro em {tipo}: {e}", file=sys.stderr)
            raise

    # 5. Monta página final
    titulo = Path(docx_path).stem
    html_final = build_html_page(
        partes_html,
        profile,
        titulo
    )
    
    # 6. Salva ou retorna
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_final)
        if verbose:
            print(f"💾 Salvo em: {output_path}")
    
    return html_final


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Construtor de Aulas CAEd - Converte .docx em HTML com componentes interativos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python construtor_cli.py aula.docx
  python construtor_cli.py aula.docx --profile DP90h -o aula.html
  python construtor_cli.py aula.docx --mock --verbose
  python construtor_cli.py --list-profiles
        """
    )
    
    parser.add_argument(
        "docx",
        nargs="?",
        help="Arquivo .docx de entrada"
    )
    
    parser.add_argument(
        "-p", "--profile",
        default="default",
        help="Nome do profile a usar (default: default)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Arquivo HTML de saída (default: mesmo nome do .docx)"
    )
    
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Usa extração mock (sem Claude API)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mostra progresso detalhado"
    )
    
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="Lista profiles disponíveis e sai"
    )
    
    parser.add_argument(
        "--api-key",
        help="Chave da API Anthropic (ou use ANTHROPIC_API_KEY)"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Valida profile e templates sem processar"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula processamento sem salvar arquivo"
    )
    
    args = parser.parse_args()
    
    # Lista profiles
    if args.list_profiles:
        profiles = list_profiles()
        print("Profiles disponíveis:")
        for p in profiles:
            profile = load_profile(p)
            desc = profile.get("descricao", "")
            print(f"  • {p}: {desc}")
        return 0
    
    # Validação de profile
    if args.validate:
        try:
            profile = load_profile(args.profile)
            print(f"✅ Profile '{args.profile}' válido")
            print(f"   Componentes configurados: {len(profile.get('componentes', {}))}")
            
            env = create_jinja_env()
            templates_ok = 0
            templates_missing = []
            
            for comp_name, comp_config in profile.get('componentes', {}).items():
                model = comp_config.get('model', 'm1')
                version = comp_config.get('version', 'v1')
                template_path = f"{comp_name}/{model}{version}.html"
                
                try:
                    env.get_template(template_path)
                    templates_ok += 1
                    print(f"   ✓ {comp_name}: {model}{version}")
                except TemplateNotFound:
                    # Verifica fallback
                    fallback_path = f"{comp_name}/m1v1.html"
                    try:
                        env.get_template(fallback_path)
                        print(f"   ⚠️  {comp_name}: {model}{version} (fallback m1v1)")
                        templates_ok += 1
                    except TemplateNotFound:
                        templates_missing.append(f"{comp_name}/{model}{version}")
                        print(f"   ✗ {comp_name}: {model}{version} AUSENTE")
            
            if templates_missing:
                print(f"\n⚠️  Templates ausentes: {len(templates_missing)}")
                return 1
            else:
                print(f"\n✅ Todos os {templates_ok} templates disponíveis")
                return 0
                
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return 1
    
    # Valida entrada
    if not args.docx:
        parser.error("Arquivo .docx é obrigatório (use --list-profiles para ver profiles)")
    
    if not os.path.exists(args.docx):
        parser.error(f"Arquivo não encontrado: {args.docx}")
    
    # Define output
    output = args.output or Path(args.docx).with_suffix(".html")
    
    # Dry run
    if args.dry_run:
        output = None
        print("🔍 Modo dry-run: não salvará arquivo")
    
    # Processa
    try:
        html_result = process_document(
            docx_path=args.docx,
            profile_name=args.profile,
            output_path=str(output) if output else None,
            use_mock=args.mock,
            api_key=args.api_key,
            verbose=args.verbose
        )
        
        if args.dry_run:
            print(f"✅ Dry-run concluído: {len(html_result)} caracteres gerados")
        else:
            print(f"✅ Processamento concluído: {output}")
        return 0
    
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"❌ Erro: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
