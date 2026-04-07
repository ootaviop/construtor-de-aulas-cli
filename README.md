# Construtor de Aulas CAEd

Converte `.docx` com tags customizadas em HTML com componentes interativos.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Básico (usa profile default)
python construtor_cli.py aula.docx

# Com profile específico
python construtor_cli.py aula.docx --profile DP90h

# Modo mock (sem Claude API)
python construtor_cli.py aula.docx --mock

# Output customizado
python construtor_cli.py aula.docx -o saida.html

# Verbose
python construtor_cli.py aula.docx --mock -v
```

## Comandos úteis

```bash
--list-profiles    # Lista profiles disponíveis
--validate         # Valida profile e templates
--dry-run          # Simula sem salvar
--help             # Ajuda completa
```

## Tags suportadas

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

## Estrutura

```
construtor/
├── construtor_cli.py      # CLI principal
├── profiles/*.json        # Configurações por curso
├── templates/*/*.html     # Templates Jinja2
├── examples/              # Arquivos de exemplo (aula.docx, aula.html)
├── tests/                 # Scripts de teste
└── tools/                 # Utilitários (gerar_template.py)
```

## API Key

```bash
export ANTHROPIC_API_KEY="sk-..."
# ou
python construtor_cli.py aula.docx --api-key "sk-..."
```
# construtor-de-aulas-cli
