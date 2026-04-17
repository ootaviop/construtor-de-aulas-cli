# Ser Docente — Importação de Componentes

Este documento descreve o progresso de importação dos componentes do curso **Ser Docente** para o sistema Construtor de Aulas CAEd. Use-o para retomar o trabalho em uma nova conversa.

---

## Contexto

O objetivo é criar todos os templates Jinja2 dos componentes do curso Ser Docente e registrá-los no pipeline. O fluxo de trabalho para cada componente é:

1. Usuário fornece o HTML final do componente + explicação contextual
2. Claude propõe estrutura de variáveis Jinja2
3. Usuário confirma (ou ajusta)
4. Claude cria o template em `templates/<componente>/m1v1.html`
5. Ao final (quando todos estiverem prontos): atualizar `construtor_cli.py` e `profiles/SERDOCENTE.json`

### Como rodar o script auxiliar de geração (quando necessário)

```bash
# Escreve o HTML bruto em /tmp/input.html, depois:
export $(cat .env | xargs) && ~/.pyenv/shims/python tools/gerar_template.py /tmp/input.html --preview
```

> **Nota:** Use `~/.pyenv/shims/python` (Python 3.11 via pyenv), não `python3` do sistema (3.12, sem `anthropic` instalado).

---

## Status dos componentes

### ✅ Já implementados (templates criados)

| Componente    | Arquivo                           | Observações                |
| ------------- | --------------------------------- | -------------------------- |
| `citacao`     | `templates/citacao/m1v1.html`     | Existia antes desta sessão |
| `atencao`     | `templates/atencao/m1v1.html`     | Existia antes desta sessão |
| `carrossel`   | `templates/carrossel/m1v1.html`   | Existia antes desta sessão |
| `sanfona`     | `templates/sanfona/m1v1.html`     | Existia antes desta sessão |
| `flipcards`   | `templates/flipcards/m1v1.html`   | Existia antes desta sessão |
| `topo`        | `templates/topo/m1v1.html`        | Criado nesta sessão        |
| `videoplayer` | `templates/videoplayer/m1v1.html` | Criado nesta sessão        |
| `listacheck`  | `templates/listacheck/m1v1.html`  | Criado nesta sessão        |
| `listanumero` | `templates/listanumero/m1v1.html` | Criado nesta sessão        |
| `listaletra`  | `templates/listaletra/m1v1.html`  | Criado nesta sessão        |
| `podcast`     | `templates/podcast/m1v1.html`     | Criado nesta sessão        |
| `spanmodal`   | `templates/spanmodal/m1v1.html`   | Criado nesta sessão        |
| `imagem`      | `templates/imagem/m1v1.html`      | Criado nesta sessão        |
| `modalcard`   | `templates/modalcard/m1v1.html`   | Criado nesta sessão        |
| `referencias` | `templates/referencias/m1v1.html` | Criado nesta sessão        |

#### Detalhes dos templates criados nesta sessão

**`topo/m1v1.html`**

- Variáveis: `id`, `titulo_topico` (opcional), `titulo_aula` (opcional)
- A URL da imagem de topo está **hardcoded** (é sempre a mesma para o Ser Docente)
- Tag no docx: `<titulotopico>` e `<tituloaula>` dentro do bloco `<topo>`
- Se ambas as variáveis estiverem ausentes, renderiza apenas a imagem

**`spanmodal/m1v1.html`**

- Variáveis: `id`, `texto` (texto do span clicável e título do modal), `conteudo` (HTML do corpo do modal)
- Sem wrapper `container/row/col` — é inline por natureza
- Modal usa `modal-lg modal-dialog-centered`
- Tags no docx: `<spanmodal>` com sub-tags `<spanmodaltrigger>` e `<spanmodalcorpo>`
- `conteudo` pode ter múltiplos `<p>` — renderizado com `| safe`

**`podcast/m1v1.html`**

- Variáveis: `id`, `soundcloud_url`, `nome`, `tema`, `sobre`, `pdf_url` (opcional)
- Label "Especialista" está hardcoded (sempre igual no Ser Docente)
- Imagem do palestrante: `src="#"` — será inserida na pós-produção
- Modal usa `id="modal-{{ id }}"` / `data-target="#modal-{{ id }}"` para evitar colisão
- `{% if pdf_url %}` omite o botão de download quando o PDF não foi informado
- Tags no docx: `<podcast>` com sub-tags `<podcasturl>`, `<podcastnome>`, `<podcasttema>`, `<podcastsobre>`, `<podcastpdf>` (opcional)

**`videoplayer/m1v1.html`**

- Variáveis: `id`, `src` (URL do embed Vimeo, vai direto no `iframe src`)
- Tag no docx: `<videoplayer>URL_DO_VIMEO</videoplayer>`

**`listacheck/m1v1.html`**, **`listanumero/m1v1.html`**, **`listaletra/m1v1.html`**

- Variáveis: `id`, `items` (array de strings — conteúdo de cada `<li>`)
- Tags no docx: `<listacheck>`, `<listanumero>`, `<listaletra>` envolvendo o `<ul>`/`<ol>` nativo que o mammoth gera
- `listacheck` → `<ul class="lista-check">`
- `listanumero` → `<ol class="lista-numero">`
- `listaletra` → `<ol class="lista-letra">`

**Links (`<a class="acesse-aqui">`)**

- **Não há template** — links são processados diretamente pelo mammoth + post-processing
- Em `construtor_cli.py`, função `extract_html_from_docx`, foi adicionado:
  ```python
  html = re.sub(r'<a\s+href=', '<a class="acesse-aqui" target="_blank" href=', html)
  ```
- Hyperlinks nativos do Google Docs/Word já viram `<a href>` via mammoth; a regex injeta a classe e o `target="_blank"` automaticamente

---

### ✅ Todos os componentes do Ser Docente estão implementados (15/15)

---

## O que ainda precisa ser feito após criar todos os templates

### 1. Atualizar `profiles/SERDOCENTE.json`

Adicionar cada novo componente na seção `componentes`:

```json
"listacheck":        { "model": "m1", "version": "v1" },
"listanumero":      { "model": "m1", "version": "v1" },
"listaletra":       { "model": "m1", "version": "v1" },
"botaoreferencias": { "model": "m1", "version": "v1" },
"imagem":           { "model": "m1", "version": "v1" },
"podcast":          { "model": "m1", "version": "v1" },
"modalcard":        { "model": "m1", "version": "v1" },
"spanmodal":        { "model": "m1", "version": "v1" }
```

> `topo` e `videoplayer` já foram adicionados ao JSON nesta sessão.

### 2. Atualizar `construtor_cli.py`

Há três lugares a atualizar:

**a) `SUPPORTED_COMPONENTS`** (linha ~43) — adicionar os novos tipos:

```python
SUPPORTED_COMPONENTS = [
    "citacao", "atencao", "carrossel", "sanfona", "flipcards",
    "topo", "videoplayer",
    "listacheck", "listanumero", "listaletra",
    "botaoreferencias", "imagem", "podcast", "modalcard", "spanmodal",
]
```

**b) `COMPONENT_TAGS`** (linha ~46) — mapear tag → (tag_raiz, sub_tag):

```python
"topo":             ("topo", None),
"videoplayer":      ("videoplayer", None),
"listacheck":        ("listacheck", None),
"listanumero":      ("listanumero", None),
"listaletra":       ("listaletra", None),
# + os demais quando forem definidos
```

**c) `EXTRACTION_PROMPT`** (linha ~170) — adicionar os novos componentes na lista de "COMPONENTES SUPORTADOS" e os exemplos de JSON esperado na seção "RETORNE APENAS JSON VÁLIDO"

**d) `extract_mock`** (linha ~315) — adicionar regex patterns para os novos componentes (usado em modo `--mock`)

---

## Estado atual do `construtor_cli.py` que precisa ser corrigido

O arquivo ainda está **desatualizado** em relação aos templates criados. As constantes `SUPPORTED_COMPONENTS`, `COMPONENT_TAGS`, o `EXTRACTION_PROMPT` e `extract_mock` **não incluem** `topo`, `videoplayer`, `listacheck`, `listanumero` nem `listaletra`. Isso precisa ser feito em bloco quando todos os templates estiverem prontos.

---

## Estrutura de pastas de templates (estado atual)

```
templates/
├── atencao/m1v1.html
├── carrossel/m1v1.html
├── carrossel/m1v2.html
├── citacao/m1v1.html
├── flipcards/m1v1.html
├── listacheck/m1v1.html
├── listaletra/m1v1.html
├── listanumero/m1v1.html
├── podcast/m1v1.html        ← novo
├── sanfona/m1v1.html
├── topo/m1v1.html
└── videoplayer/m1v1.html
```

---

## Referências rápidas

- Profile do Ser Docente: `profiles/SERDOCENTE.json`
- Pipeline principal: `construtor_cli.py`
- Script de geração de templates: `tools/gerar_template.py`
- Servidor: `uvicorn api:app --reload --port 8001`
- Arquitetura completa: `CLAUDE.md`
