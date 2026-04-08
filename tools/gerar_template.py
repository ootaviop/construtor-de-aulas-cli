#!/usr/bin/env python3
"""
gerar_template.py - Converte HTML de componente em template Jinja2

Uso:
    python gerar_template.py componente.html -o templates/nome/m1v1.html
    python gerar_template.py componente.html --preview
    cat componente.html | python gerar_template.py - --preview
"""



import argparse
import sys
from pathlib import Path

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

PROMPT = '''Converta este HTML de componente React/renderizado em um template Jinja2.

HTML DO COMPONENTE:
```html
{html}
```

REGRAS:
1. Identifique partes dinâmicas:
   - IDs únicos → {{ id }}
   - Conteúdo que varia → {{ conteudo | safe }}
   - Listas/repetições → {{% for item in items %}}
   - Primeiro item ativo → {{% if loop.first %}}active{{% endif %}}

2. Mantenha estrutura HTML exata (classes, atributos, aria-*)

3. Adicione comentário no topo documentando dados esperados:
   {{# Template: nome/versao.html #}}
   {{# Dados esperados: {{ id: string, items: [...] }} #}}

4. Para IDs correlacionados (ex: aria-controls):
   - Use {{ id }}-header-{{ loop.index0 }}
   - Use {{ id }}-content-{{ loop.index0 }}

5. Preserve indentação e formatação

RETORNE APENAS O TEMPLATE JINJA2, sem explicações ou markdown.
'''


def convert_to_jinja(html: str, api_key: str | None = None) -> str:
    """Usa Claude para converter HTML em template Jinja2."""
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("Instale: pip install anthropic")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": PROMPT.format(html=html)}
        ]
    )
    
    result = message.content[0].text.strip()
    
    # Remove possíveis wrappers de markdown
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Converte HTML de componente em template Jinja2"
    )
    parser.add_argument(
        "input",
        help="Arquivo HTML ou - para stdin"
    )
    parser.add_argument(
        "-o", "--output",
        help="Arquivo de saída (default: stdout)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Mostra preview sem salvar"
    )
    parser.add_argument(
        "--api-key",
        help="Chave da API Anthropic"
    )
    
    args = parser.parse_args()
    
    # Lê HTML
    if args.input == "-":
        html = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            html = f.read()
    
    print("🔄 Convertendo HTML → Jinja2...", file=sys.stderr)
    
    try:
        template = convert_to_jinja(html, args.api_key)
    except Exception as e:
        print(f"❌ Erro: {e}", file=sys.stderr)
        return 1
    
    # Output
    if args.preview or not args.output:
        print("\n" + "=" * 60)
        print("TEMPLATE GERADO:")
        print("=" * 60)
        print(template)
    
    if args.output and not args.preview:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(template)
        print(f"✅ Salvo: {args.output}", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
