FROM python:3.11-slim

WORKDIR /app

# Instala dependências primeiro (aproveita cache de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia apenas arquivos necessários em runtime
COPY construtor_cli.py .
COPY api.py .
COPY profiles/ profiles/
COPY templates/ templates/
COPY web/ web/

EXPOSE 8001

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
