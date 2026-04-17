#!/usr/bin/env python3
"""
FastAPI web server para o Construtor de Aulas CAEd.
Expõe o pipeline CLI como endpoints HTTP e serve a interface web.
"""

import logging
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

load_dotenv()

# Configura logging — use LOG_LEVEL=DEBUG no .env para ver a resposta bruta do Claude
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(levelname)s  %(name)s  %(message)s",
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from construtor_cli import (
    create_jinja_env,
    list_profiles,
    load_profile,
    process_document,
    render_component,
)

COMPONENT_LABELS: dict[str, str] = {
    "atencao": "Atenção",
    "carrossel": "Carrossel",
    "citacao": "Citação",
    "flipcards": "Flip Cards",
    "imagem": "Imagem",
    "listacheck": "Lista de Verificação",
    "listaletra": "Lista por Letras",
    "listanumero": "Lista Numerada",
    "modalcard": "Modal Cards",
    "podcast": "Podcast",
    "referencias": "Referências",
    "sanfona": "Sanfona (Acordeão)",
    "spanmodal": "Span Modal",
    "topo": "Topo da Aula",
    "videoplayer": "Vídeo Player",
}

COMPONENT_FIXTURES: dict[str, dict] = {
    "topo": {
        "titulo_topico": "Tópico 1",
        "titulo_aula": "Fundamentos da Prática Docente",
    },
    "citacao": {
        "conteudo": (
            "<p>Ensinar não é transferir conhecimento, mas criar as possibilidades "
            "para a sua própria produção ou a sua construção.</p>"
            "<p><em>— Paulo Freire</em></p>"
        ),
    },
    "atencao": {
        "conteudo": (
            "<p><strong>Ponto de atenção!</strong> O planejamento pedagógico é um processo "
            "contínuo e reflexivo. Ele não termina na elaboração do plano de aula — "
            "inclui a observação, a avaliação e a revisão constante da prática docente.</p>"
        ),
    },
    "carrossel": {
        "slides": [
            {
                "conteudo": (
                    "<p><strong>Competências do Século XXI</strong></p>"
                    "<p>Pensamento crítico, criatividade, colaboração e comunicação "
                    "são os quatro pilares da educação contemporânea.</p>"
                )
            },
            {
                "conteudo": (
                    "<p><strong>Aprendizagem Ativa</strong></p>"
                    "<p>O aluno como protagonista: construindo conhecimento a partir "
                    "da experiência, da reflexão e da interação com os pares.</p>"
                )
            },
            {
                "conteudo": (
                    "<p><strong>Avaliação Formativa</strong></p>"
                    "<p>Avaliar para aprender, não apenas para medir — o feedback "
                    "contínuo transforma a prática pedagógica e impulsiona o aprendizado.</p>"
                )
            },
        ],
    },
    "sanfona": {
        "secoes": [
            {
                "cabecalho": "O que é planejamento pedagógico?",
                "corpo": (
                    "<p>É o processo de organização e sistematização das ações educativas, "
                    "garantindo coerência entre objetivos, conteúdos, metodologias e avaliação.</p>"
                ),
            },
            {
                "cabecalho": "Por que planejar é essencial?",
                "corpo": (
                    "<p>O planejamento permite antecipar situações, otimizar o tempo em sala "
                    "de aula e garantir que todos os alunos tenham acesso ao aprendizado.</p>"
                ),
            },
            {
                "cabecalho": "Como elaborar um bom plano de aula?",
                "corpo": (
                    "<p>Defina objetivos claros, escolha metodologias adequadas ao perfil da "
                    "turma e estabeleça critérios de avaliação alinhados aos objetivos.</p>"
                ),
            },
        ],
        "fonte": None,
    },
    "flipcards": {
        "cards": [
            {
                "frente": "<p>Metodologia Ativa</p>",
                "verso": (
                    "<p>Abordagem pedagógica que coloca o aluno no centro do processo "
                    "de aprendizagem, incentivando sua participação ativa e protagonismo.</p>"
                ),
            },
            {
                "frente": "<p>Avaliação Diagnóstica</p>",
                "verso": (
                    "<p>Instrumento utilizado para identificar os conhecimentos prévios "
                    "dos alunos antes do início de um novo conteúdo ou unidade temática.</p>"
                ),
            },
            {
                "frente": "<p>Diferenciação Pedagógica</p>",
                "verso": (
                    "<p>Prática de adaptar o ensino às necessidades, ritmos e estilos "
                    "de aprendizagem individuais dos alunos da turma.</p>"
                ),
            },
        ],
        "imagem_textura": None,
    },
    "listacheck": {
        "items": [
            "Planejar as aulas com antecedência",
            "Definir objetivos de aprendizagem claros",
            "Preparar materiais e recursos didáticos",
            "Elaborar instrumentos de avaliação formativos",
        ],
    },
    "listanumero": {
        "items": [
            "Identifique os objetivos de aprendizagem da unidade",
            "Selecione os conteúdos mais relevantes para o contexto",
            "Escolha metodologias adequadas ao perfil da turma",
            "Defina os critérios e instrumentos de avaliação",
        ],
    },
    "listaletra": {
        "items": [
            "Protagonismo estudantil e autonomia",
            "Aprendizagem colaborativa em grupo",
            "Avaliação formativa e feedback contínuo",
            "Reflexão crítica sobre a prática docente",
        ],
    },
    "spanmodal": {
        "texto": "avaliação formativa",
        "conteudo": (
            "<p><strong>Avaliação Formativa</strong></p>"
            "<p>A avaliação formativa é um processo contínuo de monitoramento do "
            "aprendizado, com o objetivo de identificar lacunas e ajustar o ensino "
            "em tempo real, antes da avaliação somativa final.</p>"
        ),
    },
    "modalcard": {
        "cards": [
            {
                "titulo": "Planejamento",
                "descricao": "Organização das ações pedagógicas",
                "conteudo": (
                    "<p>O planejamento pedagógico envolve a definição de objetivos, "
                    "seleção de conteúdos e escolha de metodologias adequadas ao perfil dos alunos.</p>"
                ),
            },
            {
                "titulo": "Execução",
                "descricao": "Implementação das estratégias em sala",
                "conteudo": (
                    "<p>A execução pedagógica requer flexibilidade para adaptar as "
                    "estratégias planejadas às demandas reais e dinâmicas da turma.</p>"
                ),
            },
            {
                "titulo": "Avaliação",
                "descricao": "Verificação dos resultados obtidos",
                "conteudo": (
                    "<p>A avaliação deve ser contínua e formativa, fornecendo feedback "
                    "para professores e alunos sobre o progresso no aprendizado.</p>"
                ),
            },
        ],
    },
    "referencias": {
        "conteudo": (
            "<ul>"
            "<li>FREIRE, Paulo. <strong>Pedagogia do Oprimido</strong>. "
            "Rio de Janeiro: Paz e Terra, 1987.</li>"
            "<li>TARDIF, Maurice. <strong>Saberes Docentes e Formação Profissional</strong>. "
            "Petrópolis: Vozes, 2002.</li>"
            "<li>PERRENOUD, Philippe. <strong>10 Novas Competências para Ensinar</strong>. "
            "Porto Alegre: Artmed, 2000.</li>"
            "</ul>"
        ),
    },
    "imagem": {
        "alt": "Sala de aula com alunos engajados em atividade colaborativa",
    },
    "videoplayer": {
        "src": "https://player.vimeo.com/video/76979871",
    },
    "podcast": {
        "soundcloud_url": "https://soundcloud.com/caed-ufv/podcast-educacao-demo",
        "nome": "Episódio 01 — A importância do planejamento pedagógico",
        "tema": "Prática Docente",
        "sobre": (
            "Neste episódio, especialistas em educação discutem estratégias de "
            "planejamento pedagógico para professores da educação básica, "
            "abordando desde a definição de objetivos até a avaliação formativa."
        ),
        "pdf_url": None,
    },
}

app = FastAPI(title="Construtor de Aulas", version="1.0.0")

BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"
TEMPLATES_DIR = BASE_DIR / "templates"

app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve a interface web principal."""
    return HTMLResponse(content=(WEB_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/profiles")
async def get_profiles():
    """Retorna todos os profiles disponíveis com dados completos."""
    profiles = []
    for name in list_profiles():
        try:
            data = load_profile(name)
            profiles.append({
                "name": name,
                "label": data.get("nome", name),
                "descricao": data.get("descricao", ""),
                "css": data.get("css", ""),
                "js": data.get("js", ""),
                "componentes": data.get("componentes", {}),
            })
        except Exception:
            pass
    return JSONResponse(content=profiles)


@app.get("/api/templates")
async def get_templates():
    """Lista templates disponíveis agrupados por tipo de componente."""
    result = {}
    if TEMPLATES_DIR.exists():
        for tipo_dir in sorted(TEMPLATES_DIR.iterdir()):
            if tipo_dir.is_dir():
                versions = sorted([f.stem for f in tipo_dir.glob("*.html")])
                if versions:
                    result[tipo_dir.name] = versions
    return JSONResponse(content=result)


@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    profile: str = Form("default"),
    mock: str = Form("false"),
):
    """
    Converte um .docx em HTML.

    Retorna JSON:
    {
        "stem": "nome-do-arquivo",
        "topicos": [
            {"titulo": str | null, "html": str, "index": int},
            ...
        ],
        "html_completo": str
    }
    """
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Apenas arquivos .docx são suportados.")

    try:
        load_profile(profile)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    docx_bytes = await file.read()
    if len(docx_bytes) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    use_mock = mock.lower() == "true"
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(docx_bytes)
            tmp_path = tmp.name

        api_key = os.environ.get("ANTHROPIC_API_KEY")

        result = process_document(
            docx_path=tmp_path,
            profile_name=profile,
            output_path=None,
            use_mock=use_mock,
            api_key=api_key,
            verbose=False,
            split_by_topico=True,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {e}")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    stem = Path(file.filename).stem

    return JSONResponse(content={
        "stem": stem,
        "topicos": result["topicos"],
        "html_completo": result["html_completo"],
    })


@app.get("/api/gallery/{profile_name}")
async def get_gallery(profile_name: str):
    """
    Renderiza todos os componentes do perfil com dados de exemplo.

    Retorna:
    {
        "components": [{"tipo": str, "label": str, "html": str}, ...],
        "assets": {"css_bootstrap": str, "css": str, "js_bootstrap": str, "j_query": str, "js": str, "encapsulation_class": str}
    }
    """
    try:
        profile = load_profile(profile_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    env = create_jinja_env()
    componentes_config: dict = profile.get("componentes", {})
    components = []

    for tipo, fixture_dados in COMPONENT_FIXTURES.items():
        if tipo not in componentes_config:
            continue
        comp_cfg = componentes_config[tipo]
        model = comp_cfg.get("model", "m1")
        version = comp_cfg.get("version", "v1")
        try:
            html = render_component(
                env=env,
                tipo=tipo,
                model=model,
                version=version,
                dados={**fixture_dados, "id": f"gallery-{tipo}"},
            )
            components.append({
                "tipo": tipo,
                "label": COMPONENT_LABELS.get(tipo, tipo),
                "html": html,
            })
        except Exception as exc:
            components.append({
                "tipo": tipo,
                "label": COMPONENT_LABELS.get(tipo, tipo),
                "html": f'<p style="color:red">Erro ao renderizar: {exc}</p>',
            })

    assets = {
        "css_bootstrap": profile.get("css-bootstrap", ""),
        "css": profile.get("css", ""),
        "js_bootstrap": profile.get("js-bootstrap", ""),
        "j_query": profile.get("j-query", ""),
        "js": profile.get("js", ""),
        "encapsulation_class": profile.get("encapsulation-class", ""),
    }

    return JSONResponse(content={"components": components, "assets": assets})
