# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Converts `.docx` files with custom educational component tags into HTML pages with interactive components. Pipeline: `.docx` → mammoth (HTML extraction) → Claude API (structured data extraction) → Jinja2 (template rendering) → HTML output.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-..."
```

## Common commands

```bash
# Basic conversion (uses default profile)
python construtor_cli.py aula.docx

# With specific profile
python construtor_cli.py aula.docx --profile DP90h -o saida.html

# Mock mode (no Claude API call, uses regex-based extraction)
python construtor_cli.py aula.docx --mock -v

# Validate profile + templates
python construtor_cli.py --validate --profile DP90h

# List available profiles
python construtor_cli.py --list-profiles

# Run test scripts
python tests/test_templates.py    # Tests all Jinja2 templates with mock data
python tests/test_pipeline.py     # Tests full pipeline using examples/test_input.html
python tests/test_profiles.py     # Compares rendering across profiles

# Convert a rendered HTML component into a Jinja2 template
python tools/gerar_template.py componente.html -o templates/carrossel/m1v2.html
python tools/gerar_template.py componente.html --preview
```

## Architecture

### Pipeline (`construtor_cli.py`)
1. `load_profile()` — reads `profiles/<name>.json` to get component model/version/asset config
2. `extract_html_from_docx()` — uses mammoth to convert `.docx` to HTML, then unescapes shortcode tags wrapped in `<p>` tags
3. `extract_with_claude()` / `extract_mock()` — parses component tags into structured JSON; Claude API returns the full structured payload, mock uses regex
4. `render_component()` — renders `templates/<tipo>/<model><version>.html` via Jinja2; falls back to `m1v1.html` if the specified version doesn't exist
5. `build_html_page()` — assembles final HTML with CSS/JS assets from the profile config

### Profiles (`profiles/*.json`)
Each profile has a top-level `css` and `js` bundle (loaded for the whole page) plus a `componentes` map that controls which template variant each component uses. Example: `DP90h` uses `carrossel/m1v2.html` while `default` uses `carrossel/m1v1.html`. The bundle approach means a single request loads all CSS/JS needed for all components in that course.

### Templates (`templates/<tipo>/<model><version>.html`)
Jinja2 templates for each component type and version. Template variables follow a per-type schema:
- `citacao`, `atencao`: `{ id, conteudo }`
- `carrossel`: `{ id, slides: [{conteudo}] }`
- `sanfona`: `{ id, secoes: [{cabecalho, corpo}], fonte? }`
- `flipcards`: `{ id, cards: [{frente, verso, aria_label}] }`

All HTML content in template variables must be rendered with `| safe` (content comes from trusted `.docx` source).

### Component tags (used inside `.docx`)
The `.docx` author wraps content in custom XML-like tags that mammoth passes through:
`<citacao>`, `<atencao>`, `<carrossel>/<carrosselslide>`, `<sanfona>/<sanfonasecao>/<sanfonasecaocabecalho>/<sanfonasecaocorpo>`, `<flipcards>/<flipcard>/<flipcardfront>/<flipcardback>`

### Adding a new component version
1. Create `templates/<tipo>/m1v<N>.html` (use `gerar_template.py` to convert a rendered HTML sample)
2. Add/update a profile JSON to point `"version": "v<N>"` for that component
3. Run `python test_templates.py` to validate

### Adding a new profile
Create `profiles/<name>.json` following the structure of `default.json`. Run `python construtor_cli.py --validate --profile <name>` to check template availability.
