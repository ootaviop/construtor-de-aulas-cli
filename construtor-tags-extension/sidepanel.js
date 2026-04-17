const TAGS = [
  {
    group: "Estrutura",
    icon: "⬛",
    items: [
       {
        name: "topico",
        label: "Tópico",
        desc: "Cada tópico da aula deve estar dentro de um componente <topico>",
        snippet: "<topico>\n" +
                  "<!-- Conteúdo do tópico -->" +
                "</topico>",
      },
      {
        name: "secao",
        label: "Seção",
        desc: "Divisão lógica da aula",
        snippet:
          "<secao>\n" +
          "<!-- Conteúdo da seção -->\n" +
          "</secao>",
      },{
        name: "topo",
        label: "Topo",
        desc: "Cabeçalho da aula com título do tópico e da aula",
        snippet:
          "<topo>\n" +
          "<titulotopico><!-- título do tópico --></titulotopico>\n" +
          "<tituloaula><!-- título da aula --></tituloaula>\n" +
          "</topo>",
      },
    ],
  },
  
  {
    group: "Texto & Destaque",
    icon: "📝",
    items: [
      {
        name: "citacao",
        label: "Citação",
        desc: "Bloco de citação destacado",
        snippet: "<citacao>\n" +
          "<citacaotexto><!-- texto da citação --></citacaotexto>\n" +
          "<citacaoautor><!-- autor da citação --></citacaoautor>\n" +
          "</citacao>",
      },
      {
        name: "atencao",
        label: "Atenção",
        desc: "Caixa de destaque; suporta componentes internos",
        snippet: "<atencao>\n" +
          "<atencaotitulo><!-- título do destaque --></atencaotitulo>\n" +
          "<atencaocorpo><!-- corpo do destaque --></atencaocorpo>\n" +
          "</atencao>",
      },
      {
        name: "referencias",
        label: "Referências",
        desc: "Botão que abre modal com itens bibliográficos",
        snippet: "<referencias>\n" +
          "<!-- item de referência -->\n" +
          "</referencias>",
      },
    ],
  },
  {
    group: "Mídia",
    icon: "🎬",
    items: [
      {
        name: "videoplayer",
        label: "Vídeo",
        desc: "Player de vídeo Vimeo embutido",
        snippet: "<videoplayer><!-- URL embed do Vimeo --></videoplayer>",
      },
      {
        name: "podcast",
        label: "Podcast",
        desc: "Player de áudio com modal de informações",
        snippet:
          "<podcast>\n" +
          "<podcasturl><!-- URL do áudio --></podcasturl>\n" +
          "<podcastnome><!-- nome do episódio --></podcastnome>\n" +
          "<podcasttema><!-- tema --></podcasttema>\n" +
          "<podcastsobre><!-- descrição --></podcastsobre>\n" +
          "</podcast>",
      },
      {
        name: "imagem",
        label: "Imagem",
        desc: "Imagem centralizada (src definido em pós-produção)",
        snippet: "<imagem><!-- texto alternativo --></imagem>",
      },
    ],
  },
  {
    group: "Listas",
    icon: "📋",
    items: [
      {
        name: "listacheck",
        label: "Lista com check",
        desc: "Lista com ícones de checkbox",
        snippet: "<listacheck>\n" +
          "<listacheckitem><!-- item 1 --></listacheckitem>\n" +
          "<listacheckitem><!-- item 2 --></listacheckitem>\n" +
          "</listacheck>",
      },
      {
        name: "listanumero",
        label: "Lista numerada",
        desc: "Lista com numeração",
        snippet: "<listanumero>\n" +
          "<listanumerodata><!-- item 1 --></listanumerodata>\n" +
          "<listanumerodata><!-- item 2 --></listanumerodata>\n" +
          "</listanumero>",
      },
      {
        name: "listaletra",
        label: "Lista com letras",
        desc: "Lista com índice alfabético",
        snippet: "<listaletra>\n" +
          "<listaletraitem><!-- item A --></listaletraitem>\n" +
          "<listaletraitem><!-- item B --></listaletraitem>\n" +
          "</listaletra>",
      },
    ],
  },
  {
    group: "Interativos",
    icon: "✨",
    items: [
      {
        name: "carrossel",
        label: "Carrossel",
        desc: "Slides navegáveis horizontalmente",
        snippet:
          "<carrossel>\n" +
          "<carrosselslide><!-- conteúdo do slide 1 --></carrosselslide>\n" +
          "<carrosselslide><!-- conteúdo do slide 2 --></carrosselslide>\n" +
          "</carrossel>",
      },
      {
        name: "sanfona",
        label: "Sanfona",
        desc: "Acordeão com seções expansíveis",
        snippet:
          "<sanfona>\n" +
          "<sanfonasecao>\n" +
          "<sanfonasecaocabecalho><!-- título da seção --></sanfonasecaocabecalho>\n" +
          "<sanfonasecaocorpo><!-- conteúdo da seção --></sanfonasecaocorpo>\n" +
          "</sanfonasecao>\n" +
          "</sanfona>",
      },
      {
        name: "flipcards",
        label: "Flip Cards",
        desc: "Cards com frente e verso giráveis",
        snippet:
          "<flipcards>\n" +
          "<flipcard>\n" +
          "<flipcardfront><!-- frente do card --></flipcardfront>\n" +
          "<flipcardback><!-- verso do card --></flipcardback>\n" +
          "</flipcard>\n" +
          "</flipcards>",
      },
      {
        name: "modalcard",
        label: "Modal Card",
        desc: "Grid de cards que abrem modal ao clicar",
        snippet:
          "<modalcard>\n" +
          "<modalcarditem>\n" +
          "<modalcardtitulo><!-- título do card --></modalcardtitulo>\n" +
          "<modalcarddescricao><!-- descrição --></modalcarddescricao>\n" +
          "<modalcardconteudo><!-- conteúdo do modal --></modalcardconteudo>\n" +
          "</modalcarditem>\n" +
          "</modalcard>",
      },
      {
        name: "spanmodal",
        label: "Span Modal",
        desc: "Palavra/frase que abre modal ao clicar (inline)",
        snippet:
          "<spanmodal>\n" +
          "<spanmodaltrigger><!-- texto do gatilho --></spanmodaltrigger>\n" +
          "<spanmodalcorpo><!-- conteúdo do modal --></spanmodalcorpo>\n" +
          "</spanmodal>",
      },
    ],
  },
 
];

// ── Render ────────────────────────────────────────────────

function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function buildList(items) {
  return items
    .map(
      (tag) =>
        `<div class="tag-item" data-name="${tag.name}" data-snippet="${escHtml(tag.snippet)}" role="button" tabindex="0" aria-label="Copiar snippet ${tag.label}">
          <div class="tag-info">
            <span class="tag-name">&lt;${tag.name}&gt;</span>
            <span class="tag-label">${tag.label}</span>
            <span class="tag-desc">${tag.desc}</span>
          </div>
          <span class="btn-copy">Copiar</span>
        </div>`
    )
    .join("");
}

function render(filterText) {
  const query = filterText.trim().toLowerCase();
  const container = document.getElementById("tags-container");

  const sections = TAGS.map((group) => {
    const filtered = query
      ? group.items.filter(
          (t) =>
            t.name.includes(query) ||
            t.label.toLowerCase().includes(query) ||
            t.desc.toLowerCase().includes(query)
        )
      : group.items;

    if (filtered.length === 0) return "";

    return `<section class="tag-group">
      <h2 class="group-title">${group.icon} ${group.group}</h2>
      <div class="tag-list">${buildList(filtered)}</div>
    </section>`;
  }).join("");

  container.innerHTML =
    sections ||
    `<p class="empty-state">Nenhuma tag encontrada para "<strong>${escHtml(query)}</strong>".</p>`;
}

// ── Copy ──────────────────────────────────────────────────

function copySnippet(item) {
  navigator.clipboard.writeText(item.dataset.snippet).then(() => {
    const badge = item.querySelector(".btn-copy");
    badge.textContent = "Copiado!";
    item.classList.add("copied");
    setTimeout(() => {
      badge.textContent = "Copiar";
      item.classList.remove("copied");
    }, 2000);
  });
}

// ── Init ──────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  render("");

  const search = document.getElementById("search");
  search.addEventListener("input", () => render(search.value));

  document.getElementById("tags-container").addEventListener("click", (e) => {
    const item = e.target.closest(".tag-item");
    if (!item) return;
    copySnippet(item);
  });

  document.getElementById("tags-container").addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const item = e.target.closest(".tag-item");
    if (!item) return;
    e.preventDefault();
    copySnippet(item);
  });
});
