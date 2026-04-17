# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web server (development)
uvicorn api:app --reload --port 8001

# Run via Docker (recommended for production/demo)
docker compose up

# CLI usage
python construtor_cli.py aula.docx --profile default --verbose
python construtor_cli.py aula.docx --mock               # no API call
python construtor_cli.py --list-profiles
python construtor_cli.py aula.docx --validate           # check profile + templates

# Run tests (these are standalone scripts, not pytest)
python tests/test_pipeline.py
python tests/test_profiles.py
python tests/test_templates.py

# Debug Claude API responses (shows raw HTML in/out)
LOG_LEVEL=DEBUG uvicorn api:app --reload --port 8001
```

## Architecture

**Pipeline**: `.docx → mammoth → HTML → Claude API (or mock) → JSON → Jinja2 templates → HTML output`

The two main entry points are:

- `construtor_cli.py` — CLI and the entire pipeline logic
- `api.py` — FastAPI server that wraps the CLI pipeline and serves `web/index.html`

### Key pipeline stages in `construtor_cli.py`

1. **`extract_html_from_docx`** — mammoth converts `.docx` to raw HTML; shortcode wrappers (`<p>&lt;tag&gt;</p>`) are cleaned and HTML entities decoded. All links are automatically decorated with `class="acesse-aqui"` and `target="_blank"`.
2. **`split_topicos`** — splits the raw HTML at `<topico>` tags. Each tópico may have a `<topicotitulo>` child for its label. Returns a list of `{titulo, html, index}`.
3. **`extract_with_claude` / `extract_mock`** — sends the per-tópico HTML to Claude (`claude-sonnet-4-20250514`) or the regex mock. Both return `{"itens": [...]}` where each item is either `{tipo: "texto", html}` or `{tipo, id, dados}`. **IMPORTANT: The extraction prompt (Rule 6) now supports nested components — any component can contain other components and paragraphs. The `conteudo` or `dados` fields preserve inner component tags as-is, and the rendering layer recursively renders them.**
4. **`_render_html_fragment`** — recursively renders nested components found within HTML fragments. Handles inline components (e.g., `spanmodal`) separately from block components. Hoists modal overlays after the main content.
5. **`render_component`** — resolves the Jinja2 template at `templates/<tipo>/<model><version>.html`. Falls back to `m1v1` if the profile-specified version doesn't exist.
6. **`build_html_page`** — wraps the ordered list of rendered parts in a full HTML page, injecting CSS/JS from the profile.

### Profiles (`profiles/*.json`)

Profiles select which template version to use per component and which CSS/JS bundles to inject. Fields:

- `nome`, `descricao`
- `css`, `js`, `css-bootstrap`, `js-bootstrap`, `j-query` — asset URLs
- `encapsulation-class` — CSS class added to the root wrapper `div`
- `componentes` — maps component name → `{model, version}` (e.g. `"m1"`, `"v1"`)

### Templates (`templates/<tipo>/<model><version>.html`)

Jinja2 templates. Each template receives the `dados` dict from the extraction step plus `id`. Template variable shapes are documented in comments at the top of each template file.

### Supported components and their tag hierarchy

| Component      | Root tag         | Sub-tags / Description                                             |
| -------------- | ---------------- | ------------------------------------------------------------------ |
| citacao        | `<citacao>`      | Block quote                                                        |
| atencao        | `<atencao>`      | Highlight box; **supports nested components**                     |
| carrossel      | `<carrossel>`    | Slides; sub-tag: `<carrosselslide>`                               |
| sanfona        | `<sanfona>`      | Accordion; sub-tags: `<sanfonasecao>`, `<sanfonasecaocabecalho>`, `<sanfonasecaocorpo>` |
| flipcards      | `<flipcards>`    | Flip cards; sub-tags: `<flipcard>`, `<flipcardfront>`, `<flipcardback>` |
| topo           | `<topo>`         | Lesson header; optional sub-tags: `<titulotopico>`, `<tituloaula>` |
| videoplayer    | `<videoplayer>`  | Vimeo embed; content is the embed URL                             |
| listacheck     | `<listacheck>`   | Checkbox list; wraps native `<ul>` from mammoth                   |
| listanumero    | `<listanumero>`  | Numbered list; wraps native `<ol>` from mammoth                   |
| listaletra     | `<listaletra>`   | Letter-indexed list; wraps native `<ol>` from mammoth             |
| podcast        | `<podcast>`      | Audio player + modal; sub-tags: `<podcasturl>`, `<podcastnome>`, `<podcasttema>`, `<podcastsobre>`, `<podcastpdf>` (optional) |
| spanmodal      | `<spanmodal>`    | Inline trigger + modal; **inline component**; sub-tags: `<spanmodaltrigger>`, `<spanmodalcorpo>` |
| imagem         | `<imagem>`       | Centered image; content is the alt text (src is `#`, set in post-production) |
| modalcard      | `<modalcard>`    | Card grid with modals; sub-tag: `<modalcarditem>` containing `<modalcardtitulo>`, `<modalcarddescricao>`, `<modalcardconteudo>` |
| referencias    | `<referencias>`  | Bibliography modal button; content is the HTML of reference items |

The Claude prompt (in `EXTRACTION_PROMPT`) intentionally corrects typos in these tag names before extraction. **Component nesting:** Components marked with "supports nested components" can contain other components and paragraphs inside their content fields. The rendering pipeline (`_render_html_fragment`) recursively processes these nested tags.

### Web interface (`web/`)

Single-page app served at `/`. Uses vanilla JS in `web/assets/js/script.js`. The UI features:

- **Sidebar navigation** with three sections:
  - **Gerar Aula** — main converter view (default)
  - **Profiles** — lists available profiles with component configuration details
  - **Templates** — showcases all template directories and their versions
  - **Sobre** — about/help section

- **Converter view** — accepts `.docx` upload, profile selection, and mock mode toggle
- **After conversion** — API returns `{stem, topicos, html_completo}`:
  - Renders a tab/navigation per tópico
  - Injects each tópico's HTML into a preview iframe
  - **Download options:**
    - Single tópico: downloads `{stem}-{titulo}.html`
    - **"Baixar completo"** — downloads a ZIP file named `{stem}.zip` containing one `.html` per tópico, each named `{stem}-{slug}.html` where `{slug}` is the tópico title sanitized. ZIP generation is client-side using JSZip CDN.

### API endpoints

| Method | Path             | Purpose                                                                       |
| ------ | ---------------- | ----------------------------------------------------------------------------- |
| GET    | `/`              | Serves `web/index.html`                                                       |
| GET    | `/api/profiles`  | Lists profiles with metadata (name, label, description, components config)    |
| GET    | `/api/templates` | Lists template directories grouped by component type with available versions  |
| POST   | `/api/convert`   | Converts `.docx` → JSON with `{stem, topicos, html_completo}`                |

**Response shapes:**

- `/api/profiles`: `[{name, label, descricao, css, js, componentes: {tipo: {model, version}}, ...}, ...]`
- `/api/templates`: `{tipo: ["m1v1", "m1v2", ...], ...}` (grouped by component type)
- `/api/convert`: `{stem: string, topicos: [{titulo, html, index}, ...], html_completo: string}`

### Environment

- `ANTHROPIC_API_KEY` — required for real conversion (can use `--mock` / `mock=true` without it)
- `LOG_LEVEL` — set to `DEBUG` to log raw Claude responses

## Planned architecture evolution

The system is currently a single-page app focused on one course (Ser Docente). The planned evolution has two tracks:

### Track 1 — More courses (near term)

Add new profiles (`profiles/<CURSO>.json`) and their component templates. A database may be needed once the number of projects grows beyond a handful of JSON files.

### Track 2 — MyBuilder integration (future)

A second section of the web app (multi-page) dedicated to **project identity and asset generation**. The MyBuilder concept:

- User provides project name, color palette, image paths, and selects a component version per component type
- Backend generates the full folder structure for the course assets
- Backend builds CSS and JS bundles (one per project) from per-component source files
- Built assets are served for download (targeting the user's Downloads folder)
- Preview of each component version rendered with the chosen palette

This turns the system from a lesson-conversion tool into a full course-asset pipeline: **MyBuilder** (build the design system) → **Construtor de Aulas** (author lessons using that design system).

When implementing MyBuilder, keep these constraints in mind:

- The profile JSON is the contract between both tools — MyBuilder writes it, Construtor reads it
- Component versioning (`m1v1`, `m1v2`, …) maps directly to `templates/<tipo>/<model><version>.html`
- CSS/JS build output paths must match what the profile JSON references under `css` and `js`

## CSS gotchas

- `.info-card` e `.info-card-title` já existem na view "Sobre" — novos componentes devem usar prefixo próprio (ex: `.infog-*`) para evitar colisão
- `transform: scale()` não remove elemento do fluxo de layout; iframes escalados precisam de `position: absolute` dentro de container com `overflow: hidden` para evitar scrollbar horizontal
- `appendChild` em elemento já presente no DOM o move para o fim — útil para reordenação sem re-render
