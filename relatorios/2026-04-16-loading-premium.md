# Relatório: Loading Screen Premium
**Data:** 2026-04-16
**Branch:** feat/sidebar-navigation

---

## Objetivo

Substituir o spinner genérico de conversão por uma tela de loading premium com frases rotativas e tom irreverente, cobrindo apenas o container `#view-converter` (não fullscreen).

---

## Frases aprovadas pelo usuário

1. "Fazendo o que o estagiário faria em 3 horas…"
2. "Transformando Word em experiência de aprendizagem…"
3. "Relendo o documento com mais atenção do que qualquer aluno jamais leu…"
4. "Atualizando o Notion… brincadeira, isso é melhor que o Notion."
5. "Convertendo horas de planejamento em segundos…"

---

## Alterações realizadas

### `web/index.html`

- **`#view-converter`:** adicionado `style="position:relative"` para servir de âncora ao overlay absoluto
- **`#spinner`:** substituído o conteúdo antigo (card simples com anel + texto fixo) pelo novo overlay premium:
  - `.loading-overlay` — wrapper com `position: absolute; inset: 0`
  - `.loading-ring` — anel maior (64px)
  - `#loading-phrase` — parágrafo para a frase rotativa
  - `.loading-subtext` — texto fixo "Isso pode levar alguns segundos…"

**Por quê:** O spinner antigo era um card desconexo; o overlay ancorado ao container dá mais presença visual e contexto.

### `web/assets/css/style.css`

Adicionados após os estilos `.spinner-ring` existentes:

- `.loading-overlay` — `position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(255,255,255,0.95); backdrop-filter: blur(4px); z-index: 10`
- `.loading-ring` — anel de 64px com `border-top-color: var(--brand)` e animação `spin` existente
- `.loading-phrase` — fonte 0.9375rem, `color: var(--gray-700)`, `transition: opacity 0.35s ease`
- `.loading-phrase.fade-out` — `opacity: 0` (classe adicionada via JS para o efeito de transição)
- `.loading-subtext` — fonte pequena em `var(--gray-400)`

**Por quê:** A transição de `opacity` via classe CSS é mais limpa que animar via JS e respeita `prefers-reduced-motion` se adicionado futuramente.

### `web/assets/js/script.js`

- **`LOADING_PHRASES`:** array com as 5 frases, declarado no topo do IIFE
- **`loadingPhrase`:** nova ref DOM para `#loading-phrase`
- **`startPhraseRotation()`:** embaralha as frases aleatoriamente, exibe a primeira, e a cada 2800ms faz fade-out (classe `fade-out`) → aguarda 370ms (duração da transição CSS) → troca o texto → remove `fade-out`. Ao completar um ciclo, reembaralha.
- **`stopPhraseRotation()`:** limpa o interval e zera o texto
- **`setLoading(loading)`:** mantém comportamento anterior + chama `startPhraseRotation()` ao ligar e `stopPhraseRotation()` ao desligar

**Por quê:** O delay de 370ms entre `fade-out` e troca de texto garante que o usuário nunca veja a frase mudar enquanto está visível — a transição já completou quando o texto muda.

---

## Como testar

```bash
docker compose up
```

1. Abrir `http://localhost:8001`
2. Fazer upload de um `.docx` e clicar Converter
3. Verificar: overlay cobre o `#view-converter`, não o sidebar
4. Verificar: frases rotacionam com fade suave a cada ~2.8s
5. Verificar: ao terminar, overlay some e resultado aparece normalmente
6. Testar modo mock — garantir que mesmo em conversões rápidas o overlay funciona
