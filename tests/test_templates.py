#!/usr/bin/env python3
"""
Teste dos templates Jinja2 com dados mock.
Valida que cada template renderiza corretamente.
"""

import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

def create_jinja_env():
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

# Dados de teste para cada componente
TEST_DATA = {
    "citacao": {
        "id": "citacao-test-001",
        "conteudo": "<p>Esta é uma <strong>citação</strong> de exemplo para testar o template.</p>"
    },
    
    "atencao": {
        "id": "atencao-test-001",
        "conteudo": "<p>Este é um aviso <em>importante</em> que requer atenção do leitor.</p>"
    },
    
    "carrossel": {
        "id": "carrossel-test-001",
        "slides": [
            {"conteudo": "<p>Conteúdo do <strong>Slide 1</strong></p><p>Mais texto aqui.</p>"},
            {"conteudo": "<p>Conteúdo do <strong>Slide 2</strong></p><ul><li>Item A</li><li>Item B</li></ul>"},
            {"conteudo": "<p>Conteúdo do <strong>Slide 3</strong></p><p>Último slide.</p>"}
        ]
    },
    
    "sanfona": {
        "id": "sanfona-test-001",
        "secoes": [
            {
                "cabecalho": "<p>Seção 1: Introdução</p>",
                "corpo": "<p>Este é o conteúdo expandido da primeira seção.</p><p>Com múltiplos parágrafos.</p>"
            },
            {
                "cabecalho": "<p>Seção 2: Desenvolvimento</p>",
                "corpo": "<p>Conteúdo da segunda seção com <strong>formatação</strong>.</p>"
            },
            {
                "cabecalho": "<p>Seção 3: Conclusão</p>",
                "corpo": "<ul><li>Ponto 1</li><li>Ponto 2</li><li>Ponto 3</li></ul>"
            }
        ],
        "fonte": "<p>Fonte: Adaptado de exemplo didático.</p>"
    },
    
    "flipcards": {
        "id": "flipcards-test-001",
        "cards": [
            {
                "frente": "<p>Coordenador de Local</p>",
                "verso": "<p>Responsável pela <strong>logística</strong> do local de aplicação.</p>",
                "aria_label": "Informações sobre Coordenador de Local"
            },
            {
                "frente": "<p>Aplicador</p>",
                "verso": "<p>Aplica as provas em sala conforme <em>orientações</em>.</p>",
                "aria_label": "Informações sobre Aplicador"
            }
        ]
    }
}


def test_template(env, component_name: str, data: dict) -> tuple[bool, str]:
    """Testa um template e retorna (sucesso, html_ou_erro)."""
    template_path = f"{component_name}/m1v1.html"
    
    try:
        template = env.get_template(template_path)
        html = template.render(**data)
        return True, html
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("TESTE DE TEMPLATES JINJA2")
    print("=" * 60)
    
    env = create_jinja_env()
    
    results = []
    
    for component, data in TEST_DATA.items():
        print(f"\n📦 Testando: {component}")
        print("-" * 40)
        
        success, result = test_template(env, component, data)
        
        if success:
            print(f"✅ Template renderizado com sucesso")
            print(f"   Tamanho: {len(result)} caracteres")
            
            # Validações básicas
            checks = []
            
            # Verifica se ID está presente
            if f'id="{data["id"]}"' in result:
                checks.append("✓ ID presente")
            else:
                checks.append("✗ ID ausente")
            
            # Verifica estrutura Bootstrap
            if 'class="container' in result and 'class="row"' in result:
                checks.append("✓ Grid Bootstrap")
            else:
                checks.append("✗ Grid Bootstrap ausente")
            
            # Verificações específicas por componente
            if component == "carrossel":
                slide_count = result.count('class="carousel-item')
                indicator_count = result.count('data-slide-to=')
                if slide_count == len(data["slides"]):
                    checks.append(f"✓ {slide_count} slides")
                else:
                    checks.append(f"✗ Slides: esperado {len(data['slides'])}, encontrado {slide_count}")
                if indicator_count == len(data["slides"]):
                    checks.append(f"✓ {indicator_count} indicadores")
                else:
                    checks.append(f"✗ Indicadores: esperado {len(data['slides'])}, encontrado {indicator_count}")
            
            elif component == "sanfona":
                secao_count = result.count('class="accordion-item"')
                if secao_count == len(data["secoes"]):
                    checks.append(f"✓ {secao_count} seções")
                else:
                    checks.append(f"✗ Seções: esperado {len(data['secoes'])}, encontrado {secao_count}")
                if 'aria-controls=' in result:
                    checks.append("✓ aria-controls presente")
            
            elif component == "flipcards":
                card_count = result.count('class="flip-card"')
                if card_count == len(data["cards"]):
                    checks.append(f"✓ {card_count} cards")
                else:
                    checks.append(f"✗ Cards: esperado {len(data['cards'])}, encontrado {card_count}")
                # Verifica pluralização
                if len(data["cards"]) > 1 and "os cards" in result:
                    checks.append("✓ Pluralização correta")
                elif len(data["cards"]) == 1 and "o card" in result:
                    checks.append("✓ Singular correto")
            
            for check in checks:
                print(f"   {check}")
            
            results.append((component, True, checks))
        else:
            print(f"❌ Erro: {result}")
            results.append((component, False, [result]))
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"\n{'✅' if passed == total else '⚠️'} {passed}/{total} templates OK")
    
    if passed < total:
        print("\nFalhas:")
        for comp, success, info in results:
            if not success:
                print(f"  • {comp}: {info[0]}")
    
    # Gera arquivo de exemplo
    print("\n" + "=" * 60)
    print("GERANDO EXEMPLO DE SAÍDA")
    print("=" * 60)
    
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(exist_ok=True)
    
    for component, data in TEST_DATA.items():
        success, html = test_template(env, component, data)
        if success:
            output_file = output_dir / f"{component}_exemplo.html"
            
            # Wrapa em HTML básico para visualização
            full_html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Exemplo: {component}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <h1>Exemplo: {component}</h1>
    <hr>
    {html}
</body>
</html>'''
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(full_html)
            print(f"  📄 {output_file.name}")
    
    print(f"\n📁 Exemplos salvos em: {output_dir}")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
