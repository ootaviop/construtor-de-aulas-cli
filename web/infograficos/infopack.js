/**
 * infopack.js
 */

(function (global) {
  "use strict";

  const BASE_URL =
    "https://recursos-moodle.caeddigital.net/projetos/componentes/infopack";
  const MOBILE_BREAKPOINT = 768;

  // ============================================
  // INICIALIZAÇÃO
  // ============================================

  function init() {
    const nodes = document.querySelectorAll("[data-infografico]");

    if (nodes.length === 0) {
      console.warn("Nenhum data-infografico encontrado");
      return;
    }

    nodes.forEach(initInfografico);
  }

  // ============================================
  // CARREGAMENTO DE RECURSOS
  // ============================================

  async function initInfografico(el) {
    const id = el.getAttribute("data-infografico");
    const forcedMode = el.getAttribute("data-mode");
    const isMobile = forcedMode
      ? forcedMode === "mob"
      : window.innerWidth <= MOBILE_BREAKPOINT;

    try {
      const resources = await loadResources(id, isMobile);

      // Injeta CSS no <head>
      const style = document.createElement("style");
      style.dataset.infopack = id;
      style.textContent = resources.cssText;
      document.head.appendChild(style);

      // Cria wrapper e injeta HTML
      const wrapper = document.createElement("div");
      wrapper.className = `infopack-wrapper infopack-${id}`;
      wrapper.innerHTML = resources.htmlText;
      el.replaceWith(wrapper);

      // Injeta modais no DOM
      if (resources.modalsHtml) {
        injectModals(resources.modalsHtml, id);
      }

      // Executa JavaScript do infográfico se existir
      if (resources.jsText) {
        executeScript(resources.jsText, id);
      }

      // Vincula modais legados via modalMap
      bindModals(wrapper, id);

      console.debug(`✅ Infográfico ${id} carregado`);
    } catch (err) {
      console.error(`❌ Erro ao carregar ${id}:`, err);
      if (window.parent !== window) {
        window.parent.postMessage({ type: "infopack-error", id }, "*");
      } else {
        displayError(el, id);
      }
    }
  }

  async function loadResources(id, isMobile) {
    const suffix = isMobile ? "mob" : "desk";

    // Tenta 1: Arquivo responsivo específico
    try {
      return await loadResponsiveResources(id, suffix);
    } catch (e) {
      console.debug(`Arquivo responsivo não encontrado para ${id}`);
    }

    // Tenta 2: Arquivo legado
    try {
      return await loadLegacyResources(id);
    } catch (e) {
      console.debug(`Arquivo legado não encontrado para ${id}`);
    }

    throw new Error(`Não foi possível carregar recursos para ${id}`);
  }

  async function loadResponsiveResources(id, suffix) {
    const [htmlText, cssText, modalsHtml, jsText] = await Promise.all([
      fetchText(`${BASE_URL}/${id}/${id}-${suffix}.html`),
      fetchText(`${BASE_URL}/${id}/${id}.css`),
      fetchModalWithFallback(id, suffix),
      fetchTextOptional(`${BASE_URL}/${id}/${id}.js`),
    ]);

    return { htmlText, cssText, modalsHtml, jsText };
  }

  async function loadLegacyResources(id) {
    const [htmlText, cssText, modalsHtml, jsText] = await Promise.all([
      fetchText(`${BASE_URL}/${id}/${id}.html`),
      fetchText(`${BASE_URL}/${id}/${id}.css`),
      fetchModalWithFallback(id, null),
      fetchTextOptional(`${BASE_URL}/${id}/${id}.js`),
    ]);

    return { htmlText, cssText, modalsHtml, jsText };
  }

  async function fetchModalWithFallback(id, suffix) {
    // Novo padrão: pasta modais/
    try {
      return await fetchText(`${BASE_URL}/${id}/modais/modais.html`);
    } catch (e) {}

    // Legado responsivo
    if (suffix) {
      try {
        return await fetchText(`${BASE_URL}/${id}/${id}-${suffix}-modais.html`);
      } catch (e) {}
    }

    // Legado genérico
    try {
      return await fetchText(`${BASE_URL}/${id}/${id}-modais.html`);
    } catch (e) {}

    return null;
  }

  async function fetchText(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${url}`);
    return response.text();
  }

  async function fetchTextOptional(url) {
    try {
      return await fetchText(url);
    } catch (e) {
      return null;
    }
  }

  // ============================================
  // MODAIS
  // ============================================

  function injectModals(modalsHtml, id) {
    const container = document.querySelector(".container-pai") || document.body;
    const wrapper = document.createElement("div");
    wrapper.id = `infopack-modals-${id}`;
    wrapper.innerHTML = modalsHtml;
    container.appendChild(wrapper);
  }

  function bindModals(wrapper, infograficoId) {
    // Legado: vincula botões via modalMap
    const map = modalMap[infograficoId];
    if (!map) return;

    Object.entries(map).forEach(([btnId, modalId]) => {
      const btn = wrapper.querySelector(`#${btnId}`);
      if (!btn) return;

      btn.style.cursor = "pointer";
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        openModal(modalId);
      });
    });
  }

  function openModal(modalId) {
    if (typeof jQuery !== "undefined" && jQuery.fn.modal) {
      const $modal = jQuery(`#${modalId}`);
      if ($modal.length) {
        $modal.modal("show");
        return;
      }
    }

    // Fallback vanilla
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.style.display = "block";
      modal.classList.add("show");
    }
  }

  // ============================================
  // EXECUÇÃO DE SCRIPT
  // ============================================

  function executeScript(jsText, id) {
    try {
      const script = document.createElement("script");
      script.textContent = jsText;
      document.head.appendChild(script);
    } catch (error) {
      console.error(`Erro ao executar script para ${id}:`, error);
    }
  }

  // ============================================
  // UTILITÁRIOS
  // ============================================

  function displayError(el, id) {
    el.innerHTML = `
      <div style="
        padding: 20px;
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        text-align: center;
        color: #6c757d;
      ">
        <p>⚠️ Não foi possível carregar o infográfico <strong>${id}</strong></p>
        <small>Verifique a conexão de rede ou contate o suporte.</small>
      </div>
    `;
  }

  // ============================================
  // MODAL MAP LEGADO
  // ============================================

  const modalMap = {
    infografico1: {
      "btn-inf-bncc-1": "btn-inf-bncc-1-modal",
      "btn-inf-bncc-2": "btn-inf-bncc-2-modal",
      "btn-inf-bncc-3": "btn-inf-bncc-3-modal",
      "btn-inf-bncc-4": "btn-inf-bncc-4-modal",
      "btn-inf-bncc-5": "btn-inf-bncc-5-modal",
      "btn-inf-bncc-6": "btn-inf-bncc-6-modal",
      "btn-inf-bncc-7": "btn-inf-bncc-7-modal",
      "btn-inf-bncc-8": "btn-inf-bncc-8-modal",
      "btn-inf-bncc-9": "btn-inf-bncc-9-modal",
      "btn-inf-bncc-10": "btn-inf-bncc-10-modal",
    },
    infografico2: {
      "plus-projetos-escolares": "plus-projetos-escolares-modal",
      "plus-proposta-pedagogica-curricular":
        "plus-proposta-pedagogica-curricular-modal",
      "plus-projeto-politico-pedagogico":
        "plus-projeto-politico-pedagogico-modal",
      "plus-plano-de-ensino": "plus-plano-de-ensino-modal",
    },
    infografico3: {
      "plus-projetos-escolares-p": "plus-projetos-escolares-modal",
      "plus-proposta-pedagogica-curricular-p":
        "plus-proposta-pedagogica-curricular-modal",
      "plus-projeto-politico-pedagogico-p":
        "plus-projeto-politico-pedagogico-modal",
      "plus-plano-de-ensino-p": "plus-plano-de-ensino-modal",
    },
    infografico4: {
      diagnostica: "btn-av-diagnostica",
      somativa: "btn-av-somativa",
      formativa: "btn-av-formativa",
    },
    infografico5: {
      "btn-1-grande": "modal-data-wise-btn-1",
      "btn-2-grande": "modal-data-wise-btn-2",
      "btn-3-4-5-grande": "modal-data-wise-btn-3-4-5",
      "btn-6-grande": "modal-data-wise-btn-6",
      "btn-7-grande": "modal-data-wise-btn-7",
      "btn-8-grande": "modal-data-wise-btn-8",
    },
    infografico6: {
      avaliacao: "avaliacao-modal",
      "gestao-curriculo": "gestao-curriculo-modal",
      "avaliacao-evidencias": "avaliacao-evidencias-modal",
    },
    infografico7: {
      "avaliacao-p": "avaliacao-modal",
      "gestao-curriculo-p": "gestao-curriculo-modal",
      "avaliacao-evidencias-p": "avaliacao-evidencias-modal",
    },
    infografico8: {
      "planejamento-maior": "planejamento-modal",
      "conhecendo-maior": "conhecendo-modal",
      "concretizando-maior": "concretizando-modal",
    },
    infografico9: {
      "planejamento-menor": "planejamento-modal",
      "conhecendo-menor": "conhecendo-modal",
      "concretizando-menor": "concretizando-modal",
    },
    infografico10: {
      "decidir-maior": "decidir-modal",
      "entrar-maior": "entrar-modal",
      "formalizar-maior": "formalizar-modal",
      "acompanhamento-maior": "acompanhamento-modal",
    },
    infografico11: {
      "decidir-menor": "decidir-modal",
      "entrar-menor": "entrar-modal",
      "formalizar-menor": "formalizar-modal",
      "acompanhamento-menor": "acompanhamento-modal",
    },
    infografico12: {
      h6: "modal-h6",
      h7: "modal-h7",
      h8: "modal-h8",
      h9: "modal-h9",
    },
    infografico13: {
      "habilidade-esfera_1-p": "habilidade-esfera_1-modal",
      "habilidade-esfera_2-p": "habilidade-esfera_2-modal",
      "habilidade-esfera_3-p": "habilidade-esfera_3-modal",
      "habilidade-esfera_4-p": "habilidade-esfera_4-modal",
      "habilidade-esfera_5-p": "habilidade-esfera_5-modal",
      "habilidade-esfera_6-p": "habilidade-esfera_6-modal",
      "habilidade-esfera_7-p": "habilidade-esfera_7-modal",
    },
    infografico14: {
      "habilidade-esfera_1": "habilidade-esfera_1-modal",
      "habilidade-esfera_2": "habilidade-esfera_2-modal",
      "habilidade-esfera_3": "habilidade-esfera_3-modal",
      "habilidade-esfera_4": "habilidade-esfera_4-modal",
      "habilidade-esfera_5": "habilidade-esfera_5-modal",
      "habilidade-esfera_6": "habilidade-esfera_6-modal",
      "habilidade-esfera_7": "habilidade-esfera_7-modal",
    },
    infografico15: {
      "habilidade_1-p": "habilidade_1-modal",
      "habilidade_2-p": "habilidade_2-modal",
      "habilidade_3-p": "habilidade_3-modal",
      "habilidade_4-p": "habilidade_4-modal",
    },
    infografico16: {
      habilidade_1: "habilidade_1-modal",
      habilidade_2: "habilidade_2-modal",
      habilidade_3: "habilidade_3-modal",
      habilidade_4: "habilidade_4-modal",
    },
    infografico17: {
      "number-1": "number-1-modal",
      "number-2": "number-2-modal",
      "number-3": "number-3-modal",
      "number-4": "number-4-modal",
      "number-5": "number-5-modal",
      "number-6": "number-6-modal",
      "number-7": "number-7-modal",
      "number-8": "number-8-modal",
      "number-9": "number-9-modal",
      "number-10": "number-10-modal",
      "number-11": "number-11-modal",
      "number-12": "number-12-modal",
    },
    infografico18: {
      "btn-item_1": "enunciado",
      "btn-item_2": "suporte",
      "btn-item_3": "gabarito",
      "btn-item_4": "distratores",
      "btn-item_5": "comando",
    },
    infografico19: {
      "btn-ensinar": "btn-ensinar-modal",
      "btn-ensinar-p": "btn-ensinar-modal",
      "btn-estrutura": "btn-estrutura-modal",
      "btn-estrutura-p": "btn-estrutura-modal",
      "btn-como": "btn-como-modal",
      "btn-como-p": "btn-como-modal",
    },
    infografico20: {
      opcao1: "bloco-0-modal",
      opcao2: "bloco-1-modal",
      opcao3: "bloco-2-modal",
      opcao4: "bloco-3-modal",
      opcao5: "bloco-4-modal",
      opcao6: "bloco-5-modal",
      opcao7: "bloco-6-modal",
    },
    infografico21: {
      "transcritor-d": "transcritor-modal",
      "ledor-d": "ledor-modal",
      "leitura-labial-d": "leitura-labial-modal",
      "guia-interprete-d": "guia-interprete-modal",
      "libras-d": "libras-modal",
      "transcritor-m": "transcritor-modal",
      "ledor-m": "ledor-modal",
      "leitura-labial-m": "leitura-labial-modal",
      "guia-interprete-m": "guia-interprete-modal",
      "libras-m": "libras-modal",
    },
    infografico22: {
      "btn-1": "btn-1-modal",
      "btn-2": "btn-2-modal",
      "btn-3": "btn-3-modal",
      "btn-4": "btn-4-modal",
      "btn-5": "btn-5-modal",
      "btn-6": "btn-6-modal",
      "btn-7": "btn-7-modal",
      "btn-8": "btn-8-modal",
    },
    infografico23: {
      "concretizando-as-acoes": "concretizando-as-acoes-modal",
      "conhecendo-a-realidade": "conhecendo-a-realidade-modal",
      "planejando-as-mudancas": "planejando-as-mudancas-modal",
    },
    infografico24: {
      "contexto-educacional": "contexto-educacional-modal",
      confianca: "confianca-modal",
      "clima-escolar": "clima-escolar-modal",
      "sistemas-gestao": "sistemas-gestao-modal",
      "suporte-acesso": "suporte-acesso-modal",
      "formacao-uso": "formacao-uso-modal",
      "racionalidade-diretor": "racionalidade-diretor-modal",
      "lideranca-diretor": "lideranca-diretor-modal",
    },
    infografico25: {
      "btn-1-grande": "modal-data-wise-btn-1",
      "btn-2-grande": "modal-data-wise-btn-2",
      "btn-3-grande": "modal-data-wise-btn-3",
      "btn-4-grande": "modal-data-wise-btn-4",
      "btn-5-grande": "modal-data-wise-btn-5",
      "btn-6-grande": "modal-data-wise-btn-6",
      "btn-7-grande": "modal-data-wise-btn-7",
      "btn-8-grande": "modal-data-wise-btn-8",
    },
    infografico26: {
      avaliacao: "avaliacao-modal",
      "avaliacao-evidencias": "avaliacao-evidencias-modal",
      "gestao-curriculo": "gestao-curriculo-modal",
    },
    infografico27: {
      h6: "modal-h6",
      h7: "modal-h7",
      h8: "modal-h8",
      h9: "modal-h9",
    },
    infografico28: {
      "btn-inf-bncc-1": "btn-inf-bncc-1-modal",
      "btn-inf-bncc-2": "btn-inf-bncc-2-modal",
      "btn-inf-bncc-3": "btn-inf-bncc-3-modal",
      "btn-inf-bncc-4": "btn-inf-bncc-4-modal",
      "btn-inf-bncc-5": "btn-inf-bncc-5-modal",
      "btn-inf-bncc-6": "btn-inf-bncc-6-modal",
      "btn-inf-bncc-7": "btn-inf-bncc-7-modal",
      "btn-inf-bncc-8": "btn-inf-bncc-8-modal",
      "btn-inf-bncc-9": "btn-inf-bncc-9-modal",
      "btn-inf-bncc-10": "btn-inf-bncc-10-modal",
    },
    infografico29: {
      "plus-projetos-escolares": "plus-projetos-escolares-modal",
      "plus-proposta-pedagogica-curricular":
        "plus-proposta-pedagogica-curricular-modal",
      "plus-projeto-politico-pedagogico":
        "plus-projeto-politico-pedagogico-modal",
      "plus-plano-de-ensino": "plus-plano-de-ensino-modal",
    },
  };

  // ============================================
  // API PÚBLICA
  // ============================================

  global.infopack = {
    init,
  };
})(window);
