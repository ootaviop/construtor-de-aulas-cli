# Relatório: Galeria de Componentes
**Data:** 2026-04-16
**Branch:** feat/sidebar-navigation

---

## Objetivo

Criar uma Galeria de Componentes no sistema para apresentação à chefia, mostrando todos os componentes interativos que o sistema consegue gerar, renderizados com dados de exemplo realistas.

---

## Alterações realizadas

### `api.py`

- **Adicionados imports:** `create_jinja_env` e `render_component` importados de `construtor_cli`
- **Adicionado `COMPONENT_LABELS`:** dicionário mapeando nome técnico → nome amigável em português para os 15 tipos de componente
- **Adicionado `COMPONENT_FIXTURES`:** dicionário com dados de exemplo realistas de conteúdo educacional (temática Ser Docente / Prática Pedagógica) para cada um dos 15 tipos:
  - `topo`, `citacao`, `atencao`, `carrossel`, `sanfona`, `flipcards`
  - `listacheck`, `listanumero`, `listaletra`
  - `spanmodal`, `modalcard`, `referencias`
  - `imagem`, `videoplayer`, `podcast`
- **Novo endpoint `GET /api/gallery/{profile_name}`:** renderiza cada componente do perfil usando `render_component()` com os fixtures e retorna `{components: [{tipo, label, html}], assets: {css, js, ...}}`. Reutiliza 100% do pipeline existente — zero código novo de renderização.

**Por quê:** A galeria precisa de dados de exemplo para renderizar componentes sem um documento `.docx`. O endpoint centraliza a lógica no backend e devolve HTML pronto para o frontend exibir.

---

### `web/index.html`

- **Novo item na sidebar:** botão "Galeria" com ícone de grade (4 quadrados), posicionado na seção Configuração após "Templates"
- **Nova section `#view-gallery`:** contém:
  - Header com título "Galeria de Componentes" e subtítulo dinâmico com contagem
  - Seletor de perfil (`<select id="gallery-profile-select">`) para trocar o perfil em tempo real
  - Div `#gallery-loading` para estado de carregamento
  - Div `#gallery-grid` para os cards renderizados

**Por quê:** A navegação por sidebar já existe; basta adicionar o novo item e a view correspondente seguindo o padrão existente.

---

### `web/assets/css/style.css`

Adicionados ao final do arquivo (~90 linhas):

- `.gallery-header` — layout flex com título à esquerda e seletor à direita
- `.gallery-controls` / `.gallery-profile-select` — estilo do dropdown de seleção de perfil
- `.gallery-grid` — CSS Grid de 2 colunas com `gap: 1.25rem`
- `.gallery-card` — card com borda, radius, sombra sutil; começa invisível (`opacity: 0; transform: translateY(12px)`) e anima com `animation: gallery-card-in`
- `@keyframes gallery-card-in` — fade-in + slide-up suave
- `.gallery-card-header` — flex row com nome amigável e badge técnico
- `.gallery-card-name` — nome em destaque (`font-weight: 600`)
- `.gallery-card-tipo` — badge monospace com fundo cinza claro
- `.gallery-card-body iframe` — largura 100%, altura inicial 300px, sem borda
- **Media query mobile** — 1 coluna em telas ≤ 640px

**Por quê:** Os cards precisam de animação de entrada escalonada para o efeito visual da apresentação. O iframe por card isola o CSS/JS do componente do resto da interface.

---

### `web/assets/js/script.js`

- **Novos refs DOM:** `galleryGrid`, `galleryLoading`, `gallerySubtitle`, `galleryProfileSelect`
- **Novas flags:** `galleryLoaded = false` e `galleryCurrentProfile = null` (seguindo padrão de `profilesLoaded` / `templatesLoaded`)
- **Hook no nav:** adicionado `if (viewId === "view-gallery" && !galleryLoaded) loadGallery()` no loop de navegação
- **`loadGallery(profileName)`:**
  - Na primeira carga, faz fetch de `/api/profiles` para popular o `<select>` de perfil
  - Faz fetch de `/api/gallery/{profile}`, mostra/oculta loading state
  - Atualiza subtítulo com contagem de componentes
  - Chama `renderGalleryCards()`
- **`renderGalleryCards(components, assets)`:**
  - Para cada componente, cria um `<iframe srcdoc="...">` com Bootstrap CSS + CSS do perfil + HTML do componente + jQuery + Bootstrap JS + JS do perfil injetados no `srcdoc`
  - Cada card recebe `animation-delay: i * 80ms` para a animação escalonada
  - `onload` no iframe ajusta a altura para o `scrollHeight` do conteúdo
  - `ResizeObserver` observa o body do iframe para reajuste dinâmico de altura
- **Seletor de perfil:** listener `change` no `galleryProfileSelect` reseta `galleryLoaded` e chama `loadGallery()` com o novo perfil

**Por quê:** O padrão `srcdoc` isola completamente cada componente com todas as suas dependências CSS/JS, garantindo renderização idêntica à de uma aula real. O `ResizeObserver` elimina scrollbars indesejadas nos iframes.

---

## Como testar

```bash
docker compose up --build
```

1. Abrir `http://localhost:8001`
2. Clicar "Galeria" na sidebar
3. Verificar: componentes do perfil SERDOCENTE renderizados com animação de entrada escalonada
4. Trocar perfil no dropdown e verificar que os componentes atualizam
