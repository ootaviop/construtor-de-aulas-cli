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

Após subir o servidor, a interface oferece:

### Navegação por abas

- **Gerar Aula** — converter `.docx` em HTML interativo
- **Profiles** — visualizar configurações de cada profile (componentes, assets, metadados)
- **Templates** — galeria de componentes e suas versões disponíveis
- **Sobre** — informações sobre o sistema

### Funcionalidades no conversor

- Upload do arquivo `.docx` (drag-and-drop ou clique)
- Seleção de profile (por curso/projeto)
- Modo teste sem API Claude (modo mock)
- Preview do HTML gerado por tópico
- **Downloads:**
  - Baixar tópico individual → `{nome}-{titulo}.html`
  - **Baixar completo** → `.zip` contendo um `.html` por tópico, nomeados como `{nome}-{titulo-slug}.html`

---

## Tags suportadas no .docx

### Componentes principais

```html
<citacao>texto da citação</citacao>

<atencao>
  texto com atenção
  <!-- pode conter outros componentes aninhados -->
</atencao>

<carrossel>
  <carrosselslide>slide 1</carrosselslide>
  <carrosselslide>slide 2</carrosselslide>
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

### Componentes adicionais

```html
<topo>
  <titulotopico>Identificador do tópico (opcional)</titulotopico>
  <tituloaula>Título principal da aula (opcional)</tituloaula>
</topo>

<videoplayer>https://player.vimeo.com/video/123456789</videoplayer>

<listacheck>
  <ul>
    <li>Item 1</li>
    <li>Item 2</li>
  </ul>
</listacheck>

<listanumero>
  <ol>
    <li>Primeiro passo</li>
    <li>Segundo passo</li>
  </ol>
</listanumero>

<listaletra>
  <ol>
    <li>Item A</li>
    <li>Item B</li>
  </ol>
</listaletra>

<podcast>
  <podcasturl>https://w.soundcloud.com/player/?url=...</podcasturl>
  <podcastnome>Nome do palestrante</podcastnome>
  <podcasttema>Tema do episódio</podcasttema>
  <podcastsobre>Bio ou descrição do especialista</podcastsobre>
  <podcastpdf>https://exemplo.com/transcricao.pdf</podcastpdf>
  <!-- opcional -->
</podcast>

<spanmodal>
  <spanmodaltrigger>Texto clicável</spanmodaltrigger>
  <spanmodalcorpo>Conteúdo do modal</spanmodalcorpo>
</spanmodal>

<imagem>Descrição alternativa da imagem</imagem>

<modalcard>
  <modalcarditem>
    <modalcardtitulo>Título do card</modalcardtitulo>
    <modalcarddescricao>Descrição breve</modalcarddescricao>
    <modalcardconteudo>Conteúdo completo do modal</modalcardconteudo>
  </modalcarditem>
</modalcard>

<referencias>
  <p><strong>AUTOR, A.</strong> Título da obra. Cidade: Editora, 2024.</p>
  <p><strong>OUTRO, B.</strong> Outra obra. Cidade: Editora, 2024.</p>
</referencias>

<secao>
  <!-- agrupar componentes com espaçamento padrão -->
</secao>

<topico>
  <!-- delimita uma seção independente do documento -->
</topico>
```

### Sobre componentes aninhados

Componentes como `<atencao>` podem conter outros componentes e parágrafos internamente:

```html
<atencao>
  <citacao>Citação importante dentro do atenção</citacao>
  <p>Parágrafo de contexto.</p>
  <listanumero
    ><ol>
      <li>Passo 1</li>
      <li>Passo 2</li>
    </ol></listanumero
  >
  <carrossel>
    <carrosselslide>Slide 1</carrosselslide>
    <carrosselslide>Slide 2</carrosselslide>
  </carrossel>
</atencao>
```

O sistema renderizará os componentes internos automaticamente na ordem em que aparecem.

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

# Roadmap

## Em andamento

- [ ] Finalizar todos os componentes do Ser Docente (templates + registro no profile)
- [ ] Melhorar UI/UX da navegação entre tópicos após conversão

## Próximas modificações

- [ ] Construir menu de opções na interface (listar profiles, criar aula)
- [ ] Rodar LLM localmente (sem API Claude)
- [x] Separar por tópico (`<topico></topico>`)
- [x] Prompt instrui IA a corrigir tags digitadas incorretamente

## MyBuilder (futuro)

Integração de um segundo módulo ao sistema — responsável pela criação da identidade visual e geração dos assets de cada projeto/curso:

- **Criação de projeto**: nome, paleta de cores, caminhos de imagens, versão de cada componente
- **Build de assets**: geração automática da estrutura de pastas e dos bundles CSS/JS buildados
- **Preview por componente**: visualização da versão escolhida com a paleta do projeto
- **Download**: backend Python entrega o pacote pronto (estrutura de pastas + arquivos buildados)

O sistema se tornaria multi-página: uma página para **construir aulas** (atual) e outra para **gerar a identidade do projeto** (MyBuilder).

O arquivo `profiles/*.json` é o contrato entre os dois módulos — o MyBuilder escreve, o Construtor lê.

## Melhorias futuras

- [ ] Extensão no navegador para ajudar com o nome dos componentes (tags no docx)
- [ ] Suporte a múltiplos projetos com banco de dados

# Doing

## Separação por tag tópico

- [/] Deixar o sistema perfeito para fazer a aula do Ser Docente.
  - [x] Terminar de importar todos os componentes do Ser Docente como as primeiras versões de
        cada componente.
  - [x] Associar no JSON "SERDOCENTE.json" todos os componentes do Ser Docente.
  - [ ] Associar no JSON "default.json" todos os componentes do Ser Docente.

- [x] Implementar um loading melhor para quando a aula estiver sendo gerada. O
      texto deve ser mais descritivo. Ou pode ser algo mais lúdico como por exemplo
      ficar exibindo mensagens criativas enquanto a aula está sendo gerada.
