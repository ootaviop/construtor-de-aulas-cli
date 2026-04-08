#!/usr/bin/env python3
"""
FastAPI web server para o Construtor de Aulas CAEd.
Expõe o pipeline CLI como endpoints HTTP e serve a interface web.
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

load_dotenv()
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from construtor_cli import list_profiles, load_profile, process_document

app = FastAPI(title="Construtor de Aulas", version="1.0.0")

BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"

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
    """Retorna todos os profiles disponíveis com nome, label e descrição."""
    profiles = []
    for name in list_profiles():
        try:
            data = load_profile(name)
            profiles.append({
                "name": name,
                "label": data.get("nome", name),
                "descricao": data.get("descricao", ""),
            })
        except Exception:
            pass
    return JSONResponse(content=profiles)


@app.post("/api/convert")
async def convert(
    file: UploadFile = File(...),
    profile: str = Form("default"),
    mock: str = Form("false"),
):
    """
    Converte um .docx em HTML.
    Retorna o HTML com Content-Disposition: attachment para que o
    frontend possa usar o blob tanto no preview (iframe) quanto no download.
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

        html_result = process_document(
            docx_path=tmp_path,
            profile_name=profile,
            output_path=None,
            use_mock=use_mock,
            api_key=api_key,
            verbose=False,
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
    download_name = f"{stem}.html"

    return HTMLResponse(
        content=html_result,
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "Content-Type": "text/html; charset=utf-8",
        },
    )
