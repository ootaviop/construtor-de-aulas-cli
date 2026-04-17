# Construtor de Aulas CAEd — Documentação Técnica

Pipeline de conversão de arquivos `.docx` com tags customizadas em páginas HTML com componentes interativos.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Instalação e Configuração](#2-instalação-e-configuração)
3. [Interface Web e API](#3-interface-web-e-api)
4. [Uso da CLI](#4-uso-da-cli)
5. [Pipeline Interno](#5-pipeline-interno)
6. [Tags de Componentes (no .docx)](#6-tags-de-componentes-no-docx)
7. [Sistema de Profiles](#7-sistema-de-profiles)
8. [Sistema de Templates](#8-sistema-de-templates)
9. [Schemas de Dados por Componente](#9-schemas-de-dados-por-componente)
10. [Extração via Claude API vs. Mock](#10-extração-via-claude-api-vs-mock)
11. [Testes](#11-testes)
12. [Ferramenta gerar_template.py](#12-ferramenta-gerar_templatepy)
13. [Estrutura de Diretórios](#13-estrutura-de-diretórios)
14. [Como Adicionar um Novo Componente](#14-como-adicionar-um-novo-componente)
15. [Como Adicionar um Novo Profile](#15-como-adicionar-um-novo-profile)
16. [Como Adicionar uma Nova Versão de Template](#16-como-adicionar-uma-nova-versão-de-template)

---

## 1. Visão Geral

O Construtor de Aulas é uma ferramenta Python que transforma documentos Word (`.docx`) em páginas HTML educacionais interativas. Pode ser usada via **interface web** (modo recomendado, serve a partir de um container Docker) ou diretamente pela **CLI** (modo desenvolvimento).

O autor do `.docx` usa tags XML-like customizadas para marcar componentes (carrossel, sanfona, flipcards etc.) e o construtor converte isso em HTML renderizado via templates Jinja2.

**Fluxo resumido:**

```
aula.docx
  → mammoth (extrai HTML bruto)
  → Claude API ou mock (interpreta tags, retorna JSON estruturado)
  → Jinja2 (renderiza cada componente com seu template)
  → HTML final (com CSS/JS do profile do curso)
```

**Modos de uso:**

| Modo | Ponto de entrada | Indicado para |
|---|---|---|
| Interface web | `docker compose up` → http://localhost:8000 | Uso geral, produção |
| CLI direta | `python construtor_cli.py aula.docx` | Desenvolvimento, scripts, CI |

**Dependências principais:**

| Pacote | Versão mínima | Função |
|---|---|---|
| `mammoth` | 1.6.0 | Extração de HTML do `.docx` |
| `jinja2` | 3.1.0 | Renderização de templates |
| `anthropic` | 0.39.0 | Claude API (opcional em modo mock) |
| `fastapi` | — | Servidor web e endpoints REST |
| `uvicorn` | — | Servidor ASGI para o FastAPI |
| `python-dotenv` | — | Leitura do arquivo `.env` |

---

## 2. Instalação e Configuração

### Opção A — Docker (recomendado)

**Pré-requisito:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

1. Crie um arquivo `.env` na raiz do projeto com sua chave de API:

```
ANTHROPIC_API_KEY=sk-ant-...
```

2. Construa a imagem:

```bash
docker compose build
```

3. Suba o servidor:

```bash
docker compose up
```

4. Acesse **http://localhost:8000** no navegador.

Para parar: `Ctrl+C` ou `docker compose down`.

> O `docker-compose.yml` mapeia a porta 8000 e injeta o `.env` automaticamente no container. O `Dockerfile` usa `python:3.11-slim` e inicia o servidor com `uvicorn api:app --host 0.0.0.0 --port 8000`.

---

### Opção B — Local sem Docker (desenvolvimento)

```bash
pip install -r requirements.txt
```

Para usar a extração via Claude API, exporte a chave:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

A chave também pode ser passada diretamente via `--api-key` na chamada da CLI.

Para subir o servidor web localmente:

```bash
uvicorn api:app --reload --port 8000
```

**Versão Python:** o projeto usa `.python-version` (pyenv). Recomendado Python 3.11+, pois o código usa anotações de tipo como `str | None` e `list[str]`.

---

## 3. Interface Web e API

O servidor web é implementado em `api.py` usando **FastAPI** e exposto na porta 8000.

### Interface web

A rota raiz (`GET /`) serve `web/index.html` diretamente. A interface oferece uma navegação por sidebar com as seguintes seções:

**Seção Principal:**
- **Gerar Aula** — conversão de `.docx`:
  - Upload de arquivo `.docx` (com drag & drop)
  - Seleção de profile (carregados dinamicamente da API)
  - Ativação do modo teste (sem chamada à Claude API)
  - Loading screen premium com frases rotativas
  - Preview do HTML gerado em um `<iframe>` responsivo
  - Download do arquivo `.html` resultante
  - Confetti de celebração ao término bem-sucedido

**Seção Configuração:**
- **Profiles** — visualização das configurações de cada profile
- **Templates** — galeria de componentes e suas versões disponíveis
- **Galeria** — visualização interativa de todos os componentes com seletor de profile
- **Sobre** — informações sobre o sistema

Arquivos estáticos em `web/` são servidos sob o prefixo `/web` via `StaticFiles`.

### Endpoints

#### `GET /health`

Verifica se o servidor está no ar.

```json
{ "status": "ok" }
```

#### `GET /api/profiles`

Retorna a lista de todos os profiles disponíveis em `profiles/`.

**Resposta:**

```json
[
  { "name": "default",   "label": "Default",    "descricao": "..." },
  { "name": "DP90h",     "label": "DP 90h",     "descricao": "..." },
  { "name": "PROSA40h",  "label": "PROSA 40h",  "descricao": "..." }
]
```

Profiles cujo JSON falhe ao carregar são silenciosamente omitidos da lista.

#### `POST /api/convert`

Executa a conversão de um `.docx` e retorna o HTML resultante.

**Body (multipart/form-data):**

| Campo | Tipo | Padrão | Descrição |
|---|---|---|---|
| `file` | `UploadFile` | — | Arquivo `.docx` a converter (obrigatório) |
| `profile` | `string` | `"default"` | Nome do profile a usar |
| `mock` | `string` | `"false"` | `"true"` para usar extração por regex sem API |

**Resposta (sucesso — 200):**

HTML completo com os headers:
```
Content-Type: text/html; charset=utf-8
Content-Disposition: attachment; filename="<nome-do-arquivo>.html"
```

O header `Content-Disposition: attachment` permite que o frontend use o mesmo blob tanto no `<iframe>` (preview) quanto como link de download.

**Erros:**

| Código | Situação |
|---|---|
| 400 | Arquivo não é `.docx`, está vazio ou o profile não existe |
| 422 | Erro de validação no conteúdo do documento |
| 500 | Erro inesperado no pipeline |

#### `GET /api/gallery/{profile_name}`

Retorna todos os componentes suportados renderizados com dados de exemplo realistas para um profile específico.

**Parâmetros:**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `profile_name` | `string` | Nome do profile (ex: `"default"`, `"SERDOCENTE"`) |

**Resposta (sucesso — 200):**

```json
{
  "components": [
    {
      "tipo": "topo",
      "label": "Topo da Aula",
      "html": "<div class=\"topo-m1v1\" id=\"topo-001\">...</div>"
    },
    {
      "tipo": "citacao",
      "label": "Citação",
      "html": "<blockquote class=\"citacao-m1v1\" id=\"citacao-001\">...</blockquote>"
    },
    ...
  ],
  "assets": {
    "css": "/projetos/cursos/...",
    "js": "/projetos/cursos/...",
    ...
  }
}
```

**Erros:**

| Código | Situação |
|---|---|
| 404 | Profile não existe |
| 500 | Erro na renderização de algum componente |

**Uso no frontend:**

O frontend injetar o HTML de cada componente em um `<iframe>` com `srcdoc` contendo:
1. Bootstrap CSS (se o profile tiver)
2. CSS do profile
3. HTML do componente
4. jQuery (se necessário)
5. Bootstrap JS
6. JS do profile

Isso garante isolamento completo de CSS/JS e renderização idêntica à de uma aula real.

**Dados de Exemplo (Fixtures):**

Os `COMPONENT_FIXTURES` em `api.py` contêm dados realistas para cada componente (temática Ser Docente / Prática Pedagógica):

- `topo` — título de tópico e aula
- `citacao` — citação de Paulo Freire
- `atencao` — aviso sobre planejamento pedagógico
- `carrossel` — 3 slides sobre competências, aprendizagem ativa e avaliação formativa
- `sanfona` — seções expansíveis sobre planejamento pedagógico
- `flipcards` — cards sobre metodologias de ensino
- `listacheck` — checklist de atividades pedagógicas
- `listanumero` — passos para implementação de estratégia
- `listaletra` — itens indexados por letra
- `spanmodal` — termo com explicação em modal inline
- `modalcard` — grid de cards com conteúdo modal
- `referencias` — referências bibliográficas
- `imagem` — placeholder de imagem
- `videoplayer` — embed Vimeo
- `podcast` — reprodutor de áudio com metadados

O dicionário `COMPONENT_LABELS` mapeia nomes técnicos para rótulos amigáveis em português exibidos na interface.

---

**Chave de API:**

A chave Anthropic é lida de `os.environ["ANTHROPIC_API_KEY"]`, que no Docker é injetada pelo `docker-compose.yml` via `.env`. Em modo local, exportar a variável de ambiente ou usar um `.env` na raiz do projeto (carregado via `python-dotenv`).

---

## 4. Uso da CLI

O ponto de entrada é `construtor_cli.py`.

### Conversão básica

```bash
python construtor_cli.py aula.docx
```

Gera `aula.html` no mesmo diretório usando o profile `default`.

### Flags disponíveis

| Flag | Descrição |
|---|---|
| `aula.docx` | Arquivo `.docx` de entrada (posicional) |
| `-p`, `--profile <nome>` | Nome do profile a usar (padrão: `default`) |
| `-o`, `--output <arquivo>` | Caminho do HTML de saída |
| `--mock` | Usa extração por regex, sem chamar a Claude API |
| `-v`, `--verbose` | Exibe progresso detalhado com emojis no terminal |
| `--api-key <chave>` | Chave Anthropic (alternativa à variável de ambiente) |
| `--list-profiles` | Lista todos os profiles disponíveis e sai |
| `--validate` | Valida o profile e os templates sem processar nenhum arquivo |
| `--dry-run` | Executa o pipeline completo mas não salva o arquivo de saída |

### Exemplos

```bash
# Com profile específico e output customizado
python construtor_cli.py aula.docx --profile DP90h -o saida.html

# Modo desenvolvimento sem API
python construtor_cli.py aula.docx --mock --verbose

# Verificar se um profile e seus templates estão OK
python construtor_cli.py --validate --profile DP90h

# Listar todos os profiles
python construtor_cli.py --list-profiles

# Simular processamento sem salvar
python construtor_cli.py aula.docx --mock --dry-run
```

---

## 5. Pipeline Interno

A função principal é `process_document()` em `construtor_cli.py`. Ela orquestra as etapas na sequência:

### Etapa 1 — Carregamento do Profile

```python
profile = load_profile(profile_name)
```

Lê `profiles/<nome>.json`. Define quais bundles CSS/JS serão incluídos na página e qual versão de template cada componente usará.

### Etapa 2 — Extração do HTML do .docx

```python
html_raw = extract_html_from_docx(docx_path)
```

Usa `mammoth.convert_to_html()`. O mammoth preserva as tags customizadas (`<citacao>`, `<carrossel>` etc.) como strings dentro do HTML gerado. O problema é que o Word envolve cada parágrafo em `<p>`, então um shortcode fica como `<p>&lt;citacao&gt;</p>`. A função `clean_shortcode_wrappers()` remove esses wrappers e `html.unescape()` converte as entidades de volta para tags reais.

### Etapa 3 — Extração de Dados Estruturados

**Com Claude API (padrão):**
```python
dados = extract_with_claude(html_raw, api_key)
```
Envia o HTML para `claude-sonnet-4-20250514` com um prompt que instrui o modelo a retornar JSON com todos os componentes identificados e seus dados internos.

**Com mock (flag `--mock`):**
```python
dados = extract_mock(html_raw)
```
Usa regex para identificar componentes e `parse_component_content()` para extrair a hierarquia interna (slides, seções, cards etc.).

Ambos retornam o mesmo schema:

```json
{
  "componentes": [
    { "tipo": "carrossel", "id": "carrossel-001", "dados": { ... } }
  ],
  "html_solto": "<p>Texto fora de componentes</p>",
  "ordem": ["html_solto", "carrossel-001"]
}
```

### Etapa 4 — Renderização com Jinja2

```python
html = render_component(env, tipo, model, version, comp_dados)
```

Para cada componente, busca o template em `templates/<tipo>/<model><version>.html`. Se não existir, faz fallback para `templates/<tipo>/m1v1.html` (com aviso em `--verbose`). Lança erro se o fallback também não existir.

### Etapa 5 — Montagem da Página Final

```python
html_final = build_html_page(componentes_html, html_solto, profile, titulo)
```

Gera a página HTML completa com:
- `<link>` para o CSS do profile
- `<script>` para o JS do profile
- `<main class="conteudo-aula">` contendo o `html_solto` e todos os componentes renderizados

### Etapa 6 — Escrita do Arquivo

Salva em `output_path` (ou no mesmo diretório do `.docx` com extensão `.html`).

---

## 6. Tags de Componentes (no .docx)

O autor usa tags XML-like diretamente no documento Word. Mammoth as passa adiante como texto no HTML gerado.

### citacao

```xml
<citacao>
  <p>Texto da citação aqui.</p>
</citacao>
```

### atencao

```xml
<atencao>
  <p>Mensagem de atenção para o aluno.</p>
</atencao>
```

### carrossel

```xml
<carrossel>
  <carrosselslide>
    <p>Conteúdo do slide 1.</p>
  </carrosselslide>
  <carrosselslide>
    <p>Conteúdo do slide 2.</p>
  </carrosselslide>
</carrossel>
```

### sanfona (accordion)

```xml
<sanfona>
  <sanfonasecao>
    <sanfonasecaocabecalho>Título da seção</sanfonasecaocabecalho>
    <sanfonasecaocorpo>
      <p>Conteúdo expandido da seção.</p>
    </sanfonasecaocorpo>
  </sanfonasecao>
</sanfona>
```

Tag opcional de fonte, colocada dentro de `<sanfona>` mas fora das seções:

```xml
<sanfonafonte>Adaptado de: Fonte bibliográfica.</sanfonafonte>
```

### flipcards

```xml
<flipcards>
  <flipcard>
    <flipcardfront>Título do card (frente)</flipcardfront>
    <flipcardback><p>Descrição no verso do card.</p></flipcardback>
  </flipcard>
</flipcards>
```

---

## 7. Sistema de Profiles

Profiles são arquivos JSON em `profiles/`. Cada curso/turma tem seu próprio profile.

### Estrutura do JSON

```json
{
  "nome": "PROSA40h",
  "descricao": "PROSA 40 horas - versões base para todos componentes",
  "css": "/projetos/cursos/PROSA/40H/2026-1/bundle.css",
  "js": "/projetos/cursos/PROSA/40H/2026-1/bundle.js",
  "componentes": {
    "citacao":   { "model": "m1", "version": "v1" },
    "atencao":   { "model": "m1", "version": "v1" },
    "carrossel": { "model": "m1", "version": "v1" },
    "sanfona":   { "model": "m1", "version": "v1" },
    "flipcards": { "model": "m1", "version": "v1" }
  }
}
```

| Campo | Descrição |
|---|---|
| `nome` | Identificador legível (informativo) |
| `descricao` | Descrição exibida em `--list-profiles` |
| `css` | URL do bundle CSS carregado na `<head>` |
| `js` | URL do bundle JS carregado antes de `</body>` |
| `componentes.<tipo>.model` | Prefixo do modelo do template (ex: `"m1"`) |
| `componentes.<tipo>.version` | Versão do template (ex: `"v2"`) |

A combinação `model + version` aponta para o arquivo `templates/<tipo>/<model><version>.html`.

### Profiles disponíveis

| Profile | Descrição |
|---|---|
| `default` | Todos os componentes em m1v1 |
| `DP90h` | Diretores e Professores 90h — carrossel usa m1v2 |
| `PROSA40h` | PROSA 40h — todos em m1v1, bundle próprio |
| `teste_fallback` | Sanfona configurada como m2v1 (inexistente) para testar fallback |

### Lógica de fallback de template

Quando o template `<tipo>/<model><version>.html` não existe, o sistema usa `<tipo>/m1v1.html` como fallback. Se o fallback também não existir, lança `TemplateNotFound`.

---

## 8. Sistema de Templates

Templates ficam em `templates/<tipo>/<model><version>.html` e são arquivos Jinja2.

### Convenção de nomenclatura

- `m1` = modelo 1 (poderá existir `m2`, etc. no futuro)
- `v1`, `v2`... = versões progressivas com melhorias visuais ou estruturais

### Templates existentes

| Arquivo | Componente | Diferencial |
|---|---|---|
| `citacao/m1v1.html` | Citação | Layout Bootstrap com `p-citacao` |
| `atencao/m1v1.html` | Atenção | Box com cabeçalho, ícone e corpo |
| `carrossel/m1v1.html` | Carrossel | Bootstrap Carousel básico com links prev/next e bullets |
| `carrossel/m1v2.html` | Carrossel | + Contador de slides, botões com aria-label, teclado habilitado |
| `sanfona/m1v1.html` | Sanfona | Accordion com aria-controls/aria-expanded e fonte opcional |
| `flipcards/m1v1.html` | Flipcards | Cards com frente/verso, imagem textura e pluralização automática |

### Variáveis disponíveis nos templates

Cada template recebe as chaves do `dados` do componente diretamente como variáveis Jinja2, mais o `id` adicionado automaticamente pelo pipeline.

O HTML interno nunca é escapado — sempre usar `| safe`, pois o conteúdo vem de uma fonte confiável (o `.docx`).

Exemplo de cabeçalho de template:

```jinja2
{# Template: carrossel/m1v2.html #}
{# Dados esperados: {
     id: string,
     slides: [ { conteudo: string (HTML) }, ... ]
   }
#}
```

### Ambiente Jinja2

```python
Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=False,   # Conteúdo vem de fonte confiável
    trim_blocks=True,
    lstrip_blocks=True,
)
```

---

## 9. Schemas de Dados por Componente

Dados que o pipeline injeta em cada template. Todos recebem `id` automaticamente.

### citacao

```json
{
  "id": "citacao-001",
  "conteudo": "<p>Texto HTML da citação.</p>"
}
```

### atencao

```json
{
  "id": "atencao-001",
  "conteudo": "<p>Texto HTML do aviso.</p>"
}
```

### carrossel

```json
{
  "id": "carrossel-001",
  "slides": [
    { "conteudo": "<p>HTML do slide 1</p>" },
    { "conteudo": "<p>HTML do slide 2</p>" }
  ]
}
```

### sanfona

```json
{
  "id": "sanfona-001",
  "secoes": [
    {
      "cabecalho": "<p>Título da seção</p>",
      "corpo": "<p>Conteúdo expandido</p>"
    }
  ],
  "fonte": "<p>Fonte opcional (pode ser omitida)</p>"
}
```

### flipcards

```json
{
  "id": "flipcards-001",
  "cards": [
    {
      "frente": "<p>Texto da frente</p>",
      "verso": "<p>Texto do verso</p>",
      "aria_label": "Descrição acessível do card"
    }
  ]
}
```

> O template `flipcards/m1v1.html` também aceita `imagem_textura` (URL). Se omitido, usa uma imagem padrão hardcoded.

---

## 10. Extração via Claude API vs. Mock

### Claude API (`extract_with_claude`)

- Modelo: `claude-sonnet-4-20250514`
- `max_tokens`: 8192
- Envia o HTML completo do `.docx` com um prompt detalhado (`EXTRACTION_PROMPT`)
- Retorna JSON estruturado com todos os componentes, seus dados e o `html_solto`
- Lida com wrappers de markdown (``````json`) antes de fazer o parse

**Quando usar:** produção, documentos reais.

### Mock (`extract_mock`)

- Usa regex para identificar componentes (`<citacao>`, `<carrossel>` etc.)
- Chama `parse_component_content()` para detalhar a estrutura interna de cada tipo
- Gera IDs aleatórios com `uuid4().hex[:6]`
- Remove componentes encontrados do HTML para derivar o `html_solto`

**Quando usar:** desenvolvimento, testes, CI sem API Key.

**Limitação do mock:** o parser regex é simplificado — não suporta tags aninhadas de mesmo tipo ou atributos complexos. Para conteúdo real, prefira a extração via API.

---

## 11. Testes

Todos os scripts de teste ficam em `tests/` e podem ser executados diretamente:

### test_templates.py

```bash
python tests/test_templates.py
```

Renderiza cada componente com dados mock predefinidos (`TEST_DATA`) e verifica:
- ID presente no HTML renderizado
- Grid Bootstrap (`container` + `row`)
- Contagem de slides/seções/cards correta
- Pluralização de flipcards
- Presença de aria-controls na sanfona

Gera arquivos de exemplo em `output/<componente>_exemplo.html` para inspeção visual.

### test_pipeline.py

```bash
python tests/test_pipeline.py
```

Testa o pipeline completo usando `examples/test_input.html` como entrada (sem precisar de `.docx`). Verifica:
- DOCTYPE presente
- Wrapper `<main class="conteudo-aula">`
- Presença de cada tipo de componente no HTML final
- Links de CSS e scripts JS

Gera `output/pipeline_test.html`.

### test_profiles.py

```bash
python tests/test_profiles.py
```

Compara a renderização do carrossel entre os profiles `default` (m1v1) e `DP90h` (m1v2), validando diferenças estruturais entre as versões. Gera `output/carrossel_default.html` e `output/carrossel_DP90h.html`.

---

## 12. Ferramenta gerar_template.py

Utilitário em `tools/gerar_template.py` que usa a Claude API para converter um HTML de componente renderizado em um template Jinja2.

```bash
# Converter e salvar direto no diretório de templates
python tools/gerar_template.py componente.html -o templates/carrossel/m1v3.html

# Ver preview sem salvar
python tools/gerar_template.py componente.html --preview

# Ler de stdin
cat componente.html | python tools/gerar_template.py - --preview
```

O script envia o HTML para `claude-sonnet-4-20250514` com instruções para:
1. Identificar partes dinâmicas (IDs, conteúdos, listas)
2. Substituir por variáveis Jinja2 (`{{ id }}`, `{{ conteudo | safe }}`, `{% for %}`)
3. Adicionar comentário de cabeçalho com dados esperados
4. Usar `{{ id }}-header-{{ loop.index0 }}` para IDs correlacionados

---

## 13. Estrutura de Diretórios

```
construtor/
├── construtor_cli.py          # Pipeline principal e CLI
├── api.py                     # Servidor FastAPI (web + endpoints REST)
├── requirements.txt           # Dependências Python
├── .python-version            # Versão Python (pyenv)
├── Dockerfile                 # Imagem Python 3.11-slim + uvicorn
├── docker-compose.yml         # Sobe o serviço na porta 8000 com .env
├── .env                       # Chave ANTHROPIC_API_KEY (não commitado)
│
├── web/
│   └── index.html             # Interface web (upload, preview, download)
│
├── profiles/                  # Configurações por curso
│   ├── default.json
│   ├── DP90h.json
│   ├── PROSA40h.json
│   └── teste_fallback.json
│
├── templates/                 # Templates Jinja2 por componente
│   ├── atencao/
│   │   └── m1v1.html
│   ├── carrossel/
│   │   ├── m1v1.html
│   │   └── m1v2.html
│   ├── citacao/
│   │   └── m1v1.html
│   ├── flipcards/
│   │   └── m1v1.html
│   └── sanfona/
│       └── m1v1.html
│
├── examples/                  # Arquivos de exemplo
│   ├── aula.docx
│   ├── aula.html
│   └── test_input.html        # HTML de entrada para test_pipeline.py
│
├── tests/                     # Scripts de teste
│   ├── test_templates.py
│   ├── test_pipeline.py
│   └── test_profiles.py
│
├── tools/                     # Utilitários de desenvolvimento
│   └── gerar_template.py
│
├── output/                    # Saídas geradas pelos testes (não commitado)
│   ├── citacao_exemplo.html
│   ├── atencao_exemplo.html
│   ├── carrossel_exemplo.html
│   ├── sanfona_exemplo.html
│   ├── flipcards_exemplo.html
│   └── pipeline_test.html
│
└── documentation/             # Esta documentação
    └── documentacao.md
```

---

## 14. Como Adicionar um Novo Componente

**Exemplo:** adicionar o componente `tabs`.

### Passo 1 — Registrar a tag em `construtor_cli.py`

```python
SUPPORTED_COMPONENTS = ["citacao", "atencao", "carrossel", "sanfona", "flipcards", "tabs"]

COMPONENT_TAGS = {
    ...
    "tabs": ("tabs", "tab"),  # tag-pai, tag-filha
}
```

### Passo 2 — Adicionar parser no mock (`parse_component_content`)

```python
elif tipo == "tabs":
    abas = []
    for match in re.finditer(r'<tab[^>]*>(.*?)</tab>', conteudo, re.DOTALL | re.IGNORECASE):
        abas.append({"conteudo": match.group(1).strip()})
    return {"abas": abas}
```

### Passo 3 — Atualizar o prompt do Claude (`EXTRACTION_PROMPT`)

Adicionar exemplo de JSON para o novo componente no prompt.

### Passo 4 — Criar o template

```
templates/tabs/m1v1.html
```

```jinja2
{# Template: tabs/m1v1.html #}
{# Dados esperados: { id: string, abas: [{conteudo: string}] } #}

<div class="container secao tabs-m1v1" id="{{ id }}">
  ...
</div>
```

### Passo 5 — Adicionar ao profile `default.json`

```json
"tabs": { "model": "m1", "version": "v1" }
```

### Passo 6 — Adicionar dados de teste em `tests/test_templates.py`

```python
TEST_DATA["tabs"] = {
    "id": "tabs-test-001",
    "abas": [{"conteudo": "<p>Aba 1</p>"}, {"conteudo": "<p>Aba 2</p>"}]
}
```

### Passo 7 — Validar

```bash
python tests/test_templates.py
python construtor_cli.py --validate --profile default
```

---

## 15. Como Adicionar um Novo Profile

1. Criar `profiles/<nome>.json` com a estrutura padrão:

```json
{
  "nome": "NovoCurso",
  "descricao": "Descrição do novo curso",
  "css": "/projetos/cursos/<caminho>/bundle.css",
  "js": "/projetos/cursos/<caminho>/bundle.js",
  "componentes": {
    "citacao":   { "model": "m1", "version": "v1" },
    "atencao":   { "model": "m1", "version": "v1" },
    "carrossel": { "model": "m1", "version": "v1" },
    "sanfona":   { "model": "m1", "version": "v1" },
    "flipcards": { "model": "m1", "version": "v1" }
  }
}
```

2. Validar:

```bash
python construtor_cli.py --validate --profile NovoCurso
```

Se algum template apontado não existir, o `--validate` reportará o fallback ou o erro.

---

## 16. Como Adicionar uma Nova Versão de Template

**Exemplo:** criar `carrossel/m1v3.html`.

### Opção A — Usar gerar_template.py (recomendado)

```bash
python tools/gerar_template.py carrossel_v3_mockup.html -o templates/carrossel/m1v3.html
```

### Opção B — Criar manualmente

1. Copiar `templates/carrossel/m1v1.html` como base
2. Fazer as modificações desejadas
3. Manter o comentário de cabeçalho atualizado

### Apontar o profile para a nova versão

Em `profiles/<nome>.json`:

```json
"carrossel": { "model": "m1", "version": "v3" }
```

### Validar e testar

```bash
python construtor_cli.py --validate --profile <nome>
python tests/test_profiles.py
```
