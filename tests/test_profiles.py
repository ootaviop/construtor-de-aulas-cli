#!/usr/bin/env python3
"""
Compara saída entre profiles diferentes.
Demonstra que o sistema de versionamento funciona.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from construtor_cli import (
    extract_mock,
    create_jinja_env,
    render_component,
    load_profile,
)

def main():
    print("=" * 60)
    print("COMPARAÇÃO DE PROFILES")
    print("=" * 60)
    
    # HTML de teste com carrossel
    html_test = """
    <carrossel>
    <carrosselslide><p>Slide 1: Introdução</p></carrosselslide>
    <carrosselslide><p>Slide 2: Desenvolvimento</p></carrosselslide>
    <carrosselslide><p>Slide 3: Conclusão</p></carrosselslide>
    </carrossel>
    """
    
    # Extrai dados
    dados = extract_mock(html_test)
    comp = dados['componentes'][0]
    
    env = create_jinja_env()
    
    profiles = ['default', 'DP90h']
    
    for profile_name in profiles:
        print(f"\n{'─' * 60}")
        print(f"📋 Profile: {profile_name}")
        print('─' * 60)
        
        profile = load_profile(profile_name)
        
        comp_config = profile['componentes'].get('carrossel', {})
        model = comp_config.get('model', 'm1')
        version = comp_config.get('version', 'v1')
        
        print(f"   Versão: {model}{version}")
        print(f"   CSS: {profile.get('css', 'N/A')}")
        print(f"   JS: {profile.get('js', 'N/A')}")
        
        # Renderiza
        comp_dados = comp['dados'].copy()
        comp_dados['id'] = f"carrossel-{profile_name}"
        
        html = render_component(env, 'carrossel', model, version, comp_dados)
        
        print(f"\n   Tamanho HTML: {len(html)} caracteres")
        
        # Diferenças chave
        if version == 'v2':
            checks = [
                ('Contador de slides', 'slide-counter' in html),
                ('Total slides (3)', '3</span>' in html),
                ('Wrapper aprimorado', 'carrossel-wrapper' in html),
                ('Botões com aria-label', 'aria-label="Slide anterior"' in html),
            ]
        else:
            checks = [
                ('Estrutura básica', 'carousel-inner' in html),
                ('Indicadores', 'carousel-indicators' in html),
                ('Controles prev/next', 'carousel-control-prev' in html),
            ]
        
        print("\n   Validações:")
        for name, ok in checks:
            print(f"   {'✓' if ok else '✗'} {name}")
        
        # Salva para comparação visual
        output_dir = Path(__file__).parent.parent / "output"
        output_file = output_dir / f"carrossel_{profile_name}.html"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Carrossel - {profile_name}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ padding: 20px; background: #f0f0f0; }}
        .container {{ background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .carrossel-header {{ display: flex; justify-content: space-between; padding: 10px 0; }}
        .slide-counter {{ font-weight: bold; color: #666; }}
    </style>
</head>
<body>
    <h2>Profile: {profile_name} (carrossel {model}{version})</h2>
    <hr>
    {html}
</body>
</html>''')
        
        print(f"\n   📄 Salvo: {output_file.name}")
    
    print("\n" + "=" * 60)
    print("✅ Comparação concluída!")
    print("=" * 60)
    print("\nDiferenças principais entre v1 e v2:")
    print("  • v2 tem contador de slides (1 / 3)")
    print("  • v2 tem wrapper adicional para estilização")
    print("  • v2 usa buttons com aria-label (melhor acessibilidade)")
    print("  • v2 tem data-slide-index em cada slide")


if __name__ == "__main__":
    main()
