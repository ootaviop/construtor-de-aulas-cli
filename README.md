# Construtor de Aulas CAEd

Converte `.docx` com tags customizadas em HTML com componentes interativos.

## Uso (recomendado)

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado

### Iniciar

```bash
curl -O https://raw.githubusercontent.com/midiadigital123/construtor-de-aulas-cli/main/start.sh && bash start.sh
```

Na primeira execução o script cria o arquivo `.env` e pede para preencher a chave de API. Depois rode novamente:

```bash
bash start.sh
```

Acesse **http://localhost:8000** no navegador.

Para parar: `Ctrl+C` ou `docker compose down`.

---

## Solução de problemas

**`permission denied while trying to connect to the Docker daemon`**
O usuário não está no grupo `docker`. Execute:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Depois rode `bash start.sh` novamente.

---

**`unable to get image` / `pull access denied`**
A imagem no Docker Hub está privada. Acesse **hub.docker.com → repositório → Settings → Make Public**.

---

**`404: Not Found` ao baixar o script**
O repositório no GitHub está privado. Acesse **github.com → repositório → Settings → Danger Zone → Make public**.

---

## Uso com Docker (desenvolvimento)

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado
- Repositório clonado

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

# Próximas modificações

- [ ] Construir menu de opções na interface
  - [ ] Listar profiles
  - [ ] Criar aula

- [ ] Rodar LLM localmente (sem API Claude)
