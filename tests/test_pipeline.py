#!/usr/bin/env python3
"""
Testa o pipeline completo usando HTML simulado (sem precisar de .docx real).
"""

import sys
from pathlib import Path

# Adiciona o diretório ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from construtor_cli import (
    extract_mock,
    create_jinja_env,
    render_component,
    build_html_page,
    load_profile,
)

def main():
    print("=" * 60)
    print("TESTE DO PIPELINE COMPLETO")
    print("=" * 60)
    
    # 1. Carrega HTML de teste
    html_path = Path(__file__).parent.parent / "examples" / "test_input.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html_raw = f.read()
    
    print(f"\n📄 HTML de entrada: {len(html_raw)} caracteres")
    
    # 2. Extrai dados com parser mock
    print("\n🔧 Extraindo dados (modo mock)...")
    dados = extract_mock(html_raw)

    itens = dados.get('itens', [])
    componentes = [i for i in itens if i['tipo'] != 'texto']
    print(f"   Componentes encontrados: {len(componentes)}")
    for item in componentes:
        print(f"   • {item['tipo']}: {item['id']}")

    # 3. Carrega profile
    print("\n📋 Carregando profile: default")
    profile = load_profile("default")

    # 4. Renderiza itens na ordem do documento
    print("\n🎨 Renderizando componentes...")
    env = create_jinja_env()
    partes_html = []

    for item in itens:
        if item['tipo'] == 'texto':
            partes_html.append(item['html'])
            continue

        tipo = item['tipo']
        comp_id = item['id']
        comp_dados = {**item['dados'], 'id': comp_id}

        comp_config = profile.get('componentes', {}).get(tipo, {})
        model = comp_config.get('model', 'm1')
        version = comp_config.get('version', 'v1')

        try:
            html = render_component(env, tipo, model, version, comp_dados)
            partes_html.append(html)
            print(f"   ✓ {tipo} ({model}{version}) - {len(html)} chars")
        except Exception as e:
            print(f"   ✗ {tipo}: {e}")
            return 1

    # 5. Monta página final
    print("\n📦 Montando página final...")
    html_final = build_html_page(
        partes_html,
        profile,
        "Aula de Teste"
    )
    
    print(f"   Tamanho total: {len(html_final)} caracteres")
    
    # 6. Salva resultado
    output_path = Path(__file__).parent.parent / "output" / "pipeline_test.html"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_final)
    
    print(f"\n💾 Salvo em: {output_path}")
    
    # 7. Validações
    print("\n" + "=" * 60)
    print("VALIDAÇÕES")
    print("=" * 60)
    
    checks = []
    
    # Verifica estrutura HTML básica
    if "<!DOCTYPE html>" in html_final:
        checks.append(("DOCTYPE", True))
    else:
        checks.append(("DOCTYPE", False))
    
    if "<main class=\"conteudo-aula\">" in html_final:
        checks.append(("Main wrapper", True))
    else:
        checks.append(("Main wrapper", False))
    
    # Verifica componentes
    for tipo in ["citacao", "atencao", "carrossel", "sanfona", "flipcards"]:
        if f'{tipo}-' in html_final:
            checks.append((f"Componente {tipo}", True))
        else:
            checks.append((f"Componente {tipo}", False))
    
    # Verifica assets
    if '<link rel="stylesheet"' in html_final:
        checks.append(("CSS links", True))
    else:
        checks.append(("CSS links", False))
    
    if '<script src=' in html_final:
        checks.append(("JS scripts", True))
    else:
        checks.append(("JS scripts", False))
    
    passed = 0
    for name, ok in checks:
        status = "✓" if ok else "✗"
        print(f"   {status} {name}")
        if ok:
            passed += 1
    
    print(f"\n{'✅' if passed == len(checks) else '⚠️'} {passed}/{len(checks)} validações OK")
    
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
