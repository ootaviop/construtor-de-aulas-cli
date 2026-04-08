# Construtor de Aulas CAEd

Converte `.docx` com tags customizadas em HTML com componentes interativos.

## Uso com Docker (recomendado)

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado

### Configuração

1. Crie um arquivo `.env` na raiz do projeto com sua chave de API:

```
ANTHROPIC_API_KEY=sk-...
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

---

## Interface web

Após subir o servidor, a interface permite:

- Upload do arquivo `.docx`
- Seleção de profile (por curso)
- Modo teste sem API Claude (modo mock)
- Preview do HTML gerado
- Download do arquivo `.html`

---

## Tags suportadas no .docx

```html
<citacao>texto</citacao>

<atencao>texto</atencao>

<carrossel>
  <carrosselslide>conteúdo</carrosselslide>
  <carrosselslide>conteúdo</carrosselslide>
</carrossel>

<sanfona>
  <sanfonasecao>
    <sanfonasecaocabecalho>título</sanfonasecaocabecalho>
    <sanfonasecaocorpo>conteúdo</sanfonasecaocorpo>
  </sanfonasecao>
</sanfona>

<flipcards>
  <flipcard>
    <flipcardfront>frente</flipcardfront>
    <flipcardback>verso</flipcardback>
  </flipcard>
</flipcards>
```

---

## Estrutura

```
construtor/
├── construtor_cli.py      # Pipeline principal
├── api.py                 # Servidor FastAPI (web + endpoints)
├── web/index.html         # Interface web
├── profiles/*.json        # Configurações por curso
├── templates/*/*.html     # Templates Jinja2
├── Dockerfile
├── docker-compose.yml
├── .env                   # Chave de API (não commitado)
├── examples/              # Arquivos de exemplo
├── tests/                 # Scripts de teste
└── tools/                 # Utilitários (gerar_template.py)
```

---

## Uso via CLI (desenvolvimento)

```bash
pip install -r requirements.txt

# Básico (usa profile default)
python construtor_cli.py aula.docx

# Com profile específico
python construtor_cli.py aula.docx --profile DP90h

# Modo mock (sem Claude API)
python construtor_cli.py aula.docx --mock

# Outros flags
--list-profiles    # Lista profiles disponíveis
--validate         # Valida profile e templates
--dry-run          # Simula sem salvar
--verbose          # Progresso detalhado
```

## Servidor local sem Docker

```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```
