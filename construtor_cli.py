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
import logging
import os
import re
import sys
import uuid
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger("construtor")

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

# Tags que indicam início/fim de componentes no .docx
COMPONENT_TAGS = {
    "citacao":    ("citacao", None),
    "atencao":    ("atencao", None),
    "carrossel":  ("carrossel", "carrosselslide"),
    "sanfona":    ("sanfona", "sanfonasecao"),
    "flipcards":  ("flipcards", "flipcard"),
    "topo":       ("topo", None),         # sub-tags opcionais: <titulotopico>, <tituloaula>
    "videoplayer": ("videoplayer", None),  # conteúdo = URL do embed
    "listacheck":  ("listacheck", None),    # envolve <ul> nativo do mammoth
    "listanumero": ("listanumero", None), # envolve <ol> nativo do mammoth
    "listaletra": ("listaletra", None),   # envolve <ol> nativo do mammoth
    "podcast":    ("podcast", None),      # sub-tags: <podcasturl>, <podcastnome>, <podcasttema>, <podcastsobre>, <podcastpdf> (opcional)
    "spanmodal":  ("spanmodal", None),    # sub-tags: <spanmodaltrigger>, <spanmodalcorpo>
    "imagem":     ("imagem", None),       # conteúdo = texto alt da imagem
    "modalcard":  ("modalcard", "modalcarditem"),  # sub-tags: <modalcardtitulo>, <modalcarddescricao>, <modalcardconteudo>
    "referencias": ("referencias", None),          # conteúdo = HTML das referências (parágrafos gerados pelo mammoth)
}

# Componentes inline: devem ser substituídos diretamente dentro do fluxo de texto
# sem quebrar parágrafos ao redor. O trigger (<span>) fica inline; o bloco modal
# (<div>) é içado para depois do parágrafo.
INLINE_COMPONENT_TAGS: set[str] = {"spanmodal"}

# Tag de tópico: <topico> delimita seções independentes do documento.
# O título de navegação é lido a partir de <titulotopico> dentro do componente <topo>.
TOPICO_TAG = "topico"


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
# SPLIT DE TÓPICOS
# =============================================================================

def split_topicos(html: str) -> list[dict]:
    """Divide o HTML em tópicos baseados nas tags <topico>.

    O título de cada tópico (usado na navegação) é lido a partir da tag
    <titulotopico> dentro do componente <topo>. Se não encontrado, usa
    "Tópico N" como fallback.

    Retorna lista de dicts com 'titulo', 'html' e 'index'.
    Se não houver tags <topico>, retorna lista com único item contendo o HTML
    completo e titulo=None.
    """
    pattern = rf'<{TOPICO_TAG}[^>]*>(.*?)</{TOPICO_TAG}>'
    matches = list(re.finditer(pattern, html, re.DOTALL | re.IGNORECASE))

    if not matches:
        return [{"titulo": None, "html": html, "index": 0}]

    result = []
    for i, m in enumerate(matches):
        conteudo = m.group(1).strip()

        titulo_match = re.search(
            r'<titulotopico[^>]*>(.*?)</titulotopico>',
            conteudo, re.DOTALL | re.IGNORECASE
        )
        titulo = titulo_match.group(1).strip() if titulo_match else f"Tópico {i + 1}"

        result.append({"titulo": titulo, "html": conteudo, "index": i})

    return result


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

    # Adiciona classe acesse-aqui e target="_blank" em todos os links gerados pelo mammoth.
    # A classe só terá efeito visual quando o CSS do profile a definir.
    html = re.sub(
        r'<a\s+href=',
        '<a class="acesse-aqui" target="_blank" href=',
        html
    )

    return html


# =============================================================================
# PROMPT PARA CLAUDE API
# =============================================================================

EXTRACTION_PROMPT = '''Analise o HTML de um documento educacional e extraia seus elementos na ORDEM EXATA em que aparecem no documento.

TAG ESTRUTURAL:
- secao         — envolve um ou mais componentes para aplicar espaçamento padrão. Represente-a como um item de tipo "secao" no JSON de saída, com uma lista "itens" contendo todos os componentes e textos que estão dentro dela. <topo> nunca fica dentro de <secao>. <spanmodal> é inline e ignora <secao>.

COMPONENTES SUPORTADOS (tags canônicas):
- citacao       — bloco de citação
- atencao       — caixa de destaque "Atenção"
- carrossel     — slides navegáveis (subcomponente: <carrosselslide>)
- sanfona       — accordion expansível (subcomponentes: <sanfonasecao>, <sanfonasecaocabecalho>, <sanfonasecaocorpo>)
- flipcards     — cards que viram (subcomponentes: <flipcard>, <flipcardfront>, <flipcardback>)
- topo          — cabeçalho da aula (sub-tags opcionais: <titulotopico>, <tituloaula>)
- videoplayer   — player de vídeo Vimeo; o conteúdo da tag é a URL do embed
- listacheck     — lista com marcadores de check; envolve <ul><li>...</li></ul>
- listanumero   — lista numerada; envolve <ol><li>...</li></ol>
- listaletra    — lista com letras; envolve <ol><li>...</li></ul>
- podcast       — player de áudio SoundCloud com modal "sobre o especialista" (sub-tags: <podcasturl>, <podcastnome>, <podcasttema>, <podcastsobre>, e opcional <podcastpdf>)
- spanmodal     — span clicável inline que abre um modal Bootstrap (sub-tags: <spanmodaltrigger>, <spanmodalcorpo>)
- imagem        — imagem centralizada; o conteúdo da tag é o texto alt (src sempre "#", inserido na pós-produção)
- modalcard     — grade de cards que abrem modais ao clicar (subcomponentes: <modalcarditem>, cada um com <modalcardtitulo>, <modalcarddescricao>, <modalcardconteudo>)
- referencias   — botão que abre modal com lista de referências bibliográficas; o conteúdo da tag é o HTML dos parágrafos de referência


ETAPA 1 — VERIFICAÇÃO DE TAGS (faça isso ANTES de extrair qualquer conteúdo):
Varra o HTML em busca de todas as tags que parecem ser componentes personalizados (qualquer tag fora do HTML padrão).
Para cada tag encontrada, verifique se ela corresponde exatamente a uma tag canônica da lista acima.
Se a tag NÃO for exata, identifique a tag canônica mais próxima por similaridade (erros de digitação como "carossel", "citaçao", "flipcard" no lugar de "flipcards", "sanfona-secao" no lugar de "sanfonasecao", etc.) e trate-a como se fosse a tag canônica correta.
Exemplos de correções esperadas:
  "carossel"        → carrossel
  "carrosell"       → carrossel
  "citaçao"         → citacao
  "atençao"         → atencao
  "flipcard"        → flipcards (tag raiz)
  "flip-cards"      → flipcards
  "sanfona-secao"   → sanfonasecao
  "topico-titulo"   → titulotopico (sub-tag de topo)
  "topicotitulo"    → titulotopico (sub-tag de topo)
  "titulo-topico"   → titulotopico
  "titulo-aula"     → tituloaula
  "video"           → videoplayer
  "lista-check"     → listacheck
  "lista-chek"      → listacheck
  "listacheck"      → listacheck
  "lista-numero"    → listanumero
  "lista-letra"     → listaletra
  "pod-cast"        → podcast
  "podcast-url"     → podcasturl
  "podcast-nome"    → podcastnome
  "podcast-tema"    → podcasttema
  "podcast-sobre"   → podcastsobre
  "podcast-pdf"     → podcastpdf
  "span-modal"      → spanmodal
  "spanmodal-trigger" → spanmodaltrigger
  "spanmodal-corpo" → spanmodalcorpo
  "img"             → imagem
  "image"           → imagem
  "modal-card"      → modalcard
  "modalcard-item"  → modalcarditem
  "modalcard-titulo" → modalcardtitulo
  "modalcard-descricao" → modalcarddescricao
  "modalcard-conteudo" → modalcardconteudo
  "referencia"      → referencias
  "referências"     → referencias
  "refs"            → referencias
  "botaoreferencias" → referencias

Se uma tag de abertura existir sem sua tag de fechamento correspondente (ou vice-versa), considere o bloco válido e extraia o conteúdo disponível.

ETAPA 2 — EXTRAÇÃO:
Com as tags já corrigidas mentalmente, extraia os elementos na ordem em que aparecem.

REGRAS DE EXTRAÇÃO:
1. Preserve TODO o HTML interno dos componentes e dos blocos de texto (tags, classes, atributos)
2. Gere IDs únicos para componentes (formato: "tipo-xxxx")
3. Para componentes com subcomponentes, extraia a hierarquia completa
4. Blocos de texto entre componentes devem ser incluídos na lista como itens do tipo "texto"
5. A lista "itens" deve refletir a sequência real do documento — não agrupe texto separado
6. COMPONENTES ANINHADOS: componentes podem conter outros componentes e parágrafos livremente. Quando isso ocorrer, preserve o conteúdo interno EXATAMENTE como está (tags de componente incluídas) na string do campo correspondente (ex: "conteudo"). NÃO mova componentes internos para a lista raiz. NÃO converta tags de componente em HTML genérico. O sistema renderizará os componentes internos automaticamente na ordem em que aparecem.
   Exemplo: um <atencao> com dois <citacao>, três parágrafos e um <carrossel> dentro deve ter "conteudo" igual à string HTML completa com todas essas tags preservadas.

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
      "tipo": "secao",
      "id": "secao-001",
      "itens": [
        {{
          "tipo": "citacao",
          "id": "citacao-001",
          "dados": {{
            "conteudo": "<p>Texto da citação...</p>"
          }}
        }},
        {{
          "tipo": "texto",
          "html": "<p>Parágrafo entre componentes dentro da seção...</p>"
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
        }}
      ]
    }},
    {{
      "tipo": "atencao",
      "id": "atencao-001",
      "dados": {{
        "conteudo": "<citacao>Trecho importante.</citacao><p>Parágrafo dentro do atenção.</p><listanumero><ol><li>Primeiro passo</li><li>Segundo passo</li></ol></listanumero><carrossel><carrosselslide><p>Slide A</p></carrosselslide><carrosselslide><p>Slide B</p></carrosselslide></carrossel>"
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
    }},
    {{
      "tipo": "topo",
      "id": "topo-001",
      "dados": {{
        "titulo_topico": "Texto da etiqueta do tópico (ou null se ausente)",
        "titulo_aula": "Título principal da aula (ou null se ausente)"
      }}
    }},
    {{
      "tipo": "videoplayer",
      "id": "videoplayer-001",
      "dados": {{
        "src": "https://player.vimeo.com/video/123456789"
      }}
    }},
    {{
      "tipo": "listacheck",
      "id": "listacheck-001",
      "dados": {{
        "items": ["Texto do item 1", "Texto do item 2", "Texto do item 3"]
      }}
    }},
    {{
      "tipo": "listanumero",
      "id": "listanumero-001",
      "dados": {{
        "items": ["Primeiro item", "Segundo item"]
      }}
    }},
    {{
      "tipo": "listaletra",
      "id": "listaletra-001",
      "dados": {{
        "items": ["Item a", "Item b"]
      }}
    }},
    {{
      "tipo": "podcast",
      "id": "podcast-001",
      "dados": {{
        "soundcloud_url": "https://w.soundcloud.com/player/?url=...",
        "nome": "Nome do palestrante",
        "tema": "Tema do podcast",
        "sobre": "Bio do especialista para o modal",
        "pdf_url": "https://exemplo.com/transcricao.pdf"
      }}
    }},
    {{
      "tipo": "spanmodal",
      "id": "spanmodal-001",
      "dados": {{
        "texto": "Decreto nº 47.758",
        "conteudo": "<p>Texto explicativo que aparece no corpo do modal...</p>"
      }}
    }},
    {{
      "tipo": "imagem",
      "id": "imagem-001",
      "dados": {{
        "alt": "Descrição da imagem"
      }}
    }},
    {{
      "tipo": "modalcard",
      "id": "modalcard-001",
      "dados": {{
        "cards": [
          {{
            "titulo": "Título do card",
            "descricao": "Texto curto da face traseira",
            "conteudo": "<p>Conteúdo HTML do modal...</p>"
          }}
        ]
      }}
    }},
    {{
      "tipo": "referencias",
      "id": "referencias-001",
      "dados": {{
        "conteudo": "<p class=\"text-break\">AUTOR, A. <strong>Título da obra</strong>. Cidade: Editora, 2024.</p>"
      }}
    }}
  ]
}}
'''


def extract_with_claude(html: str, api_key: str | None = None, verbose: bool = False) -> dict:  # noqa: ARG001
    """Usa Claude API para extrair dados estruturados do HTML."""
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("Módulo 'anthropic' não instalado. Use: pip install anthropic")

    logger.info("── HTML ──\n%s\n── FIM ──", html)
    
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

    logger.info("── RESPOSTA BRUTA DO CLAUDE ──\n%s\n── FIM ──", response_text)

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


def _build_items(segment: str) -> list[dict]:
    """Parseia componentes e textos de um segmento HTML (sem tags <secao>).

    Coleta todos os componentes com suas posições, ordena por posição de
    início e intercala os segmentos de texto entre eles.
    """
    patterns = {
        tipo: rf'<{tipo}[^>]*>(.*?)</{tipo}>'
        for tipo in COMPONENT_TAGS
    }

    all_matches: list[tuple[int, int, str, str]] = []
    for tipo, pattern in patterns.items():
        for m in re.finditer(pattern, segment, re.DOTALL | re.IGNORECASE):
            all_matches.append((m.start(), m.end(), tipo, m.group(1)))

    all_matches.sort(key=lambda x: x[0])

    items: list[dict] = []
    cursor = 0

    for start, end, tipo, conteudo in all_matches:
        if start < cursor:
            # Este match está aninhado dentro de um componente já processado — ignora.
            continue
        text_before = segment[cursor:start].strip()
        if text_before:
            items.append({"tipo": "texto", "html": text_before})
        dados = parse_component_content(tipo, conteudo)
        items.append({
            "tipo": tipo,
            "id": f"{tipo}-{uuid.uuid4().hex[:6]}",
            "dados": dados,
        })
        cursor = end

    text_after = segment[cursor:].strip()
    if text_after:
        items.append({"tipo": "texto", "html": text_after})

    return items


def extract_mock(html: str) -> dict:
    """Extração mock para testes sem API.

    Cada bloco <secao>...</secao> é emitido como um item de tipo "secao"
    com uma lista "itens" contendo os componentes e textos internos.
    Componentes fora de qualquer <secao> são emitidos como itens de nível raiz.
    """
    secao_pattern = re.compile(r'<secao[^>]*>(.*?)</secao>', re.DOTALL | re.IGNORECASE)

    itens: list[dict] = []
    cursor = 0

    for m in secao_pattern.finditer(html):
        before = html[cursor:m.start()].strip()
        if before:
            itens.extend(_build_items(before))

        sub_itens = _build_items(m.group(1))
        itens.append({
            "tipo": "secao",
            "id": f"secao-{uuid.uuid4().hex[:6]}",
            "itens": sub_itens,
        })
        cursor = m.end()

    remaining = html[cursor:].strip()
    if remaining:
        itens.extend(_build_items(remaining))

    return {"itens": itens}


def _extract_subtag(tag: str, conteudo: str) -> str | None:
    """Extrai o conteúdo de uma sub-tag dentro de um bloco HTML."""
    m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', conteudo, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else None


def _parse_citacao(conteudo: str) -> dict:
    return {"conteudo": conteudo.strip()}


def _parse_atencao(conteudo: str) -> dict:
    return {"conteudo": conteudo.strip()}


def _parse_carrossel(conteudo: str) -> dict:
    slides = [
        {"conteudo": m.group(1).strip()}
        for m in re.finditer(r'<carrosselslide[^>]*>(.*?)</carrosselslide>', conteudo, re.DOTALL | re.IGNORECASE)
    ]
    return {"slides": slides} if slides else {"slides": [{"conteudo": conteudo.strip()}]}


def _parse_sanfona(conteudo: str) -> dict:
    secoes = []
    for m in re.finditer(r'<sanfonasecao[^>]*>(.*?)</sanfonasecao>', conteudo, re.DOTALL | re.IGNORECASE):
        secao = m.group(1)
        secoes.append({
            "cabecalho": _extract_subtag("sanfonasecaocabecalho", secao) or "",
            "corpo":     _extract_subtag("sanfonasecaocorpo", secao) or "",
        })
    result: dict = {"secoes": secoes}
    fonte = _extract_subtag("sanfonafonte", conteudo)
    if fonte:
        result["fonte"] = fonte
    return result


def _parse_flipcards(conteudo: str) -> dict:
    cards = []
    for m in re.finditer(r'<flipcard[^>]*>(.*?)</flipcard>', conteudo, re.DOTALL | re.IGNORECASE):
        card = m.group(1)
        cards.append({
            "frente":     _extract_subtag("flipcardfront", card) or "",
            "verso":      _extract_subtag("flipcardback", card) or "",
            "aria_label": "Card informativo",
        })
    return {"cards": cards}


def _parse_topo(conteudo: str) -> dict:
    return {
        "titulo_topico": _extract_subtag("titulotopico", conteudo),
        "titulo_aula":   _extract_subtag("tituloaula", conteudo),
    }


def _parse_videoplayer(conteudo: str) -> dict:
    return {"src": conteudo.strip()}


def _parse_lista(conteudo: str) -> dict:
    items = [
        m.group(1).strip()
        for m in re.finditer(r'<li[^>]*>(.*?)</li>', conteudo, re.DOTALL | re.IGNORECASE)
    ]
    return {"items": items}


def _parse_podcast(conteudo: str) -> dict:
    result = {
        "soundcloud_url": _extract_subtag("podcasturl", conteudo) or "",
        "nome":           _extract_subtag("podcastnome", conteudo) or "",
        "tema":           _extract_subtag("podcasttema", conteudo) or "",
        "sobre":          _extract_subtag("podcastsobre", conteudo) or "",
    }
    pdf_url = _extract_subtag("podcastpdf", conteudo)
    if pdf_url:
        result["pdf_url"] = pdf_url
    return result


def _parse_spanmodal(conteudo: str) -> dict:
    return {
        "texto":    _extract_subtag("spanmodaltrigger", conteudo) or "",
        "conteudo": _extract_subtag("spanmodalcorpo", conteudo) or "",
    }


def _parse_imagem(conteudo: str) -> dict:
    return {"alt": conteudo.strip()}


def _parse_modalcard(conteudo: str) -> dict:
    cards = []
    for m in re.finditer(r'<modalcarditem[^>]*>(.*?)</modalcarditem>', conteudo, re.DOTALL | re.IGNORECASE):
        item = m.group(1)
        cards.append({
            "titulo":    _extract_subtag("modalcardtitulo", item) or "",
            "descricao": _extract_subtag("modalcarddescricao", item) or "",
            "conteudo":  _extract_subtag("modalcardconteudo", item) or "",
        })
    return {"cards": cards}


def _parse_referencias(conteudo: str) -> dict:
    return {"conteudo": conteudo.strip()}


_COMPONENT_PARSERS: dict[str, Callable[[str], dict]] = {
    "citacao":    _parse_citacao,
    "atencao":    _parse_atencao,
    "carrossel":  _parse_carrossel,
    "sanfona":    _parse_sanfona,
    "flipcards":  _parse_flipcards,
    "topo":       _parse_topo,
    "videoplayer": _parse_videoplayer,
    "listacheck":  _parse_lista,
    "listanumero": _parse_lista,
    "listaletra": _parse_lista,
    "podcast":    _parse_podcast,
    "spanmodal":  _parse_spanmodal,
    "imagem":     _parse_imagem,
    "modalcard":  _parse_modalcard,
    "referencias": _parse_referencias,
}


def parse_component_content(tipo: str, conteudo: str) -> dict:
    """Parse do conteúdo interno de cada tipo de componente."""
    parser = _COMPONENT_PARSERS.get(tipo)
    if parser:
        return parser(conteudo)
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
    css_bootstrap = profile.get("css-bootstrap", "")
    js_bootstrap = profile.get("js-bootstrap", "")
    j_query = profile.get("j-query", "")
    font_awesome = profile.get("fontawesome", "")

    css_tags = f'<link rel="stylesheet" href="{css_bootstrap}">' if css_bootstrap else ""
    css_tags += f'<link rel="stylesheet" href="{font_awesome}">' if font_awesome else ""
    css_tags += f'<link rel="stylesheet" href="{css}">' if css else ""
    js_tags = f'<script src="{j_query}"></script>' if j_query else ""
    js_tags += f'<script src="{js_bootstrap}"></script>' if js_bootstrap else ""
    js_tags += f'<script src="{js}"></script>' if js else ""

    
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
<body data-bs-theme="{profile.get("theme", 'light')}">
    <div class="conteudo-aula {profile.get("encapsulation-class", '')}">
        {conteudo}
    </div>
    {js_tags}
</body>
</html>
'''


# =============================================================================
# RENDERIZAÇÃO RECURSIVA
# =============================================================================

def _prerender_dados_fields(value, env: Environment, profile: dict, verbose: bool):
    """Percorre recursivamente os dados e pré-renderiza campos que contêm HTML com componentes."""
    if isinstance(value, str):
        return _render_html_fragment(value, env, profile, verbose)
    if isinstance(value, dict):
        return {k: _prerender_dados_fields(v, env, profile, verbose) for k, v in value.items()}
    if isinstance(value, list):
        return [_prerender_dados_fields(v, env, profile, verbose) for v in value]
    return value


def _render_html_fragment(html: str, env: Environment, profile: dict, verbose: bool) -> str:
    """Renderiza componentes aninhados encontrados dentro de um fragmento HTML.

    Passo 1 — inline: componentes em INLINE_COMPONENT_TAGS (ex.: spanmodal) são
    substituídos diretamente no fluxo do texto. O trigger (<span>) fica inline; o
    bloco modal (<div>) é içado para depois do conteúdo principal.

    Passo 2 — bloco: demais componentes são processados via _build_items e renderizados
    como itens separados. Se não houver componentes de bloco, o HTML é retornado intacto.
    """
    hoisted: list[str] = []

    # Passo 1: inline components
    processed = html
    for tipo in INLINE_COMPONENT_TAGS:
        pattern = re.compile(rf'<{tipo}[^>]*>(.*?)</{tipo}>', re.DOTALL | re.IGNORECASE)

        def _replace_inline(m, _tipo=tipo):
            dados = parse_component_content(_tipo, m.group(1))
            comp_id = f"{_tipo}-{uuid.uuid4().hex[:6]}"
            comp_config = profile.get("componentes", {}).get(_tipo, {})
            model = comp_config.get("model", "m1")
            version = comp_config.get("version", "v1")
            full = render_component(env, _tipo, model, version, {**dados, "id": comp_id}, fallback=True, verbose=verbose)
            if full is None:
                return dados.get("texto", "")
            # O template spanmodal gera <span>...</span>\n<div>...</div>.
            # Separa o trigger inline do bloco modal pelo primeiro \n<div.
            split_idx = full.find("\n<div")
            if split_idx >= 0:
                hoisted.append(full[split_idx:].strip())
                return full[:split_idx].strip()
            return full

        processed = pattern.sub(_replace_inline, processed)

    # Passo 2: block components
    items = _build_items(processed)
    if all(i["tipo"] == "texto" for i in items):
        result = processed
    else:
        parts: list[str] = []
        for item in items:
            if item["tipo"] == "texto":
                parts.append(item["html"])
                continue
            prerendered = _prerender_dados_fields(item["dados"], env, profile, verbose)
            comp_dados = {**prerendered, "id": item["id"]}
            comp_config = profile.get("componentes", {}).get(item["tipo"], {})
            model = comp_config.get("model", "m1")
            version = comp_config.get("version", "v1")
            rendered = render_component(env, item["tipo"], model, version, comp_dados, fallback=True, verbose=verbose)
            if rendered is not None:
                parts.append(rendered)
        result = "\n".join(parts)

    if hoisted:
        result += "\n" + "\n".join(hoisted)

    return result


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def _render_topico_html(
    html: str,
    profile: dict,
    env: Environment,
    use_mock: bool,
    api_key: str | None,
    verbose: bool,
) -> list[str]:
    """Extrai e renderiza os componentes de um único bloco de HTML (tópico).

    Retorna lista ordenada de strings HTML prontas para montar a página.
    """
    if use_mock:
        dados = extract_mock(html)
    else:
        dados = extract_with_claude(html, api_key, verbose=verbose)

    def _count_components(itens: list[dict]) -> int:
        count = 0
        for i in itens:
            if i["tipo"] == "texto":
                continue
            elif i["tipo"] == "secao":
                count += _count_components(i.get("itens", []))
            else:
                count += 1
        return count

    n_componentes = _count_components(dados.get("itens", []))
    if verbose:
        print(f"   → {n_componentes} componentes encontrados")

    def _render_item(item: dict) -> str | None:
        """Renderiza um item de componente. Retorna None para tipo desconhecido."""
        tipo = item["tipo"]
        comp_id = item["id"]
        prerendered = _prerender_dados_fields(item["dados"], env, profile, verbose)
        comp_dados = {**prerendered, "id": comp_id}

        comp_config = profile.get("componentes", {}).get(tipo, {})
        model = comp_config.get("model", "m1")
        version = comp_config.get("version", "v1")

        rendered = render_component(env, tipo, model, version, comp_dados, fallback=True, verbose=verbose)
        if verbose:
            print(f"   ✓ {tipo} ({model}{version})")
        return rendered

    partes_html: list[str] = []
    for item in dados.get("itens", []):
        if item["tipo"] == "texto":
            partes_html.append(item["html"])
            continue

        if item["tipo"] == "secao":
            # Renderiza todos os sub-itens e agrupa em UM único wrapper de seção
            secao_parts: list[str] = []
            for sub in item.get("itens", []):
                if sub["tipo"] == "texto":
                    secao_parts.append(sub["html"])
                else:
                    rendered_sub = _render_item(sub)
                    if rendered_sub is not None:
                        secao_parts.append(rendered_sub)
            inner = "\n".join(secao_parts)
            partes_html.append(
                f'<div class="container secao" id="{item["id"]}">\n'
                f'    <div class="row">\n'
                f'        <div class="col-sm-12 col-md-11 col-lg-11 col-xl-9 m-auto">\n'
                f'{inner}\n'
                f'        </div>\n'
                f'    </div>\n'
                f'</div>'
            )
            continue

        rendered = _render_item(item)
        if rendered is not None:
            if item["tipo"] not in ("topo", "spanmodal"):
                rendered = (
                    f'<div class="container secao" id="{item["id"]}">\n'
                    f'    <div class="row">\n'
                    f'        <div class="col-sm-12 col-md-11 col-lg-11 col-xl-9 m-auto">\n'
                    f'{rendered}\n'
                    f'        </div>\n'
                    f'    </div>\n'
                    f'</div>'
                )
            partes_html.append(rendered)

    return partes_html


def process_document(
    docx_path: str,
    profile_name: str = "default",
    output_path: str | None = None,
    use_mock: bool = False,
    api_key: str | None = None,
    verbose: bool = False,
    split_by_topico: bool = False,
) -> "str | dict":
    """Pipeline completo: .docx → HTML.

    Quando split_by_topico=True retorna dict:
        {
            "topicos": [{"titulo": str|None, "html": str, "index": int}, ...],
            "html_completo": str,
        }
    Caso contrário retorna string HTML (comportamento original).
    """

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

    if use_mock and verbose:
        print("🔧 Usando extração mock (sem API)")
    elif not use_mock and verbose:
        print("🤖 Extraindo dados via Claude API...")

    # 3. Divide em tópicos (pode ser lista de 1 se não houver <topico>)
    topicos_raw = split_topicos(html_raw)
    tem_topicos = len(topicos_raw) > 1 or topicos_raw[0]["titulo"] is not None

    if verbose and tem_topicos:
        print(f"📑 {len(topicos_raw)} tópico(s) encontrado(s)")

    # 4. Processa cada tópico
    if verbose:
        print("🎨 Renderizando templates...")

    env = create_jinja_env()
    doc_titulo = Path(docx_path).stem

    topicos_result: list[dict] = []
    all_partes: list[str] = []

    for topico in topicos_raw:
        if verbose and tem_topicos:
            print(f"\n── Tópico {topico['index'] + 1}: {topico['titulo'] or '(sem título)'}")

        try:
            partes = _render_topico_html(
                topico["html"], profile, env, use_mock, api_key, verbose
            )
        except Exception as e:
            print(f"   ✗ Erro no tópico {topico['index'] + 1}: {e}", file=sys.stderr)
            raise

        titulo_pagina = topico["titulo"] or doc_titulo
        topico_html = build_html_page(partes, profile, titulo_pagina)

        topicos_result.append({
            "titulo": topico["titulo"],
            "html": topico_html,
            "index": topico["index"],
        })
        all_partes.extend(partes)

    # 5. Monta página completa (todos os tópicos em sequência)
    html_completo = build_html_page(all_partes, profile, doc_titulo)

    # 6. Salva ou retorna
    if split_by_topico:
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_completo)
            if verbose:
                print(f"💾 Salvo em: {output_path}")
        return {
            "topicos": topicos_result,
            "html_completo": html_completo,
        }

    # Comportamento original: retorna apenas o HTML completo
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_completo)
        if verbose:
            print(f"💾 Salvo em: {output_path}")

    return html_completo


# =============================================================================
# CLI
# =============================================================================

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Construtor de Aulas CAEd - Converte .docx em HTML com componentes interativos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python construtor_cli.py aula.docx
  python construtor_cli.py aula.docx --profile DP90h -o aula.html
  python construtor_cli.py aula.docx --mock --verbose
  python construtor_cli.py --list-profiles
        """,
    )
    parser.add_argument("docx", nargs="?", help="Arquivo .docx de entrada")
    parser.add_argument("-p", "--profile", default="default", help="Nome do profile a usar (default: default)")
    parser.add_argument("-o", "--output", help="Arquivo HTML de saída (default: mesmo nome do .docx)")
    parser.add_argument("--mock", action="store_true", help="Usa extração mock (sem Claude API)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostra progresso detalhado")
    parser.add_argument("--list-profiles", action="store_true", help="Lista profiles disponíveis e sai")
    parser.add_argument("--api-key", help="Chave da API Anthropic (ou use ANTHROPIC_API_KEY)")
    parser.add_argument("--validate", action="store_true", help="Valida profile e templates sem processar")
    parser.add_argument("--dry-run", action="store_true", help="Simula processamento sem salvar arquivo")
    return parser


def _cmd_list_profiles() -> int:
    profiles = list_profiles()
    print("Profiles disponíveis:")
    for p in profiles:
        profile = load_profile(p)
        print(f"  • {p}: {profile.get('descricao', '')}")
    return 0


def _cmd_validate(profile_name: str) -> int:
    try:
        profile = load_profile(profile_name)
        print(f"✅ Profile '{profile_name}' válido")
        print(f"   Componentes configurados: {len(profile.get('componentes', {}))}")

        env = create_jinja_env()
        templates_ok = 0
        templates_missing = []

        for comp_name, comp_config in profile.get("componentes", {}).items():
            model = comp_config.get("model", "m1")
            version = comp_config.get("version", "v1")
            template_path = f"{comp_name}/{model}{version}.html"

            try:
                env.get_template(template_path)
                templates_ok += 1
                print(f"   ✓ {comp_name}: {model}{version}")
            except TemplateNotFound:
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

        print(f"\n✅ Todos os {templates_ok} templates disponíveis")
        return 0

    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1


def _cmd_convert(args: argparse.Namespace, output: Path | None) -> int:
    try:
        html_result = process_document(
            docx_path=args.docx,
            profile_name=args.profile,
            output_path=str(output) if output else None,
            use_mock=args.mock,
            api_key=args.api_key,
            verbose=args.verbose,
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


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list_profiles:
        return _cmd_list_profiles()

    if args.validate:
        return _cmd_validate(args.profile)

    if not args.docx:
        parser.error("Arquivo .docx é obrigatório (use --list-profiles para ver profiles)")
    if not os.path.exists(args.docx):
        parser.error(f"Arquivo não encontrado: {args.docx}")

    output: Path | None = None if args.dry_run else (args.output or Path(args.docx).with_suffix(".html"))
    if args.dry_run:
        print("🔍 Modo dry-run: não salvará arquivo")

    return _cmd_convert(args, output)


if __name__ == "__main__":
    sys.exit(main())
