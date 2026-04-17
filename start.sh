#!/bin/bash
# Construtor de Aulas CAEd — Script de inicialização
# Uso: bash start.sh
set -e

# ── docker-compose.yml ───────────────────────────────────────
if [ ! -f docker-compose.yml ]; then
  cat > docker-compose.yml <<'EOF'
services:
  construtor:
    image: midiadigital/construtor-aulas:latest
    ports:
      - "8001:8000"
    env_file:
      - .env
EOF
  echo "✅ docker-compose.yml criado."
fi

# ── .env ─────────────────────────────────────────────────────
if [ ! -f .env ]; then
  cat > .env <<'EOF'
# Chave da API Anthropic (obrigatório)
# Obtenha em: https://console.anthropic.com/
ANTHROPIC_API_KEY=

# Nível de log (opcional): DEBUG exibe a resposta bruta do Claude nos logs
# LOG_LEVEL=INFO
EOF
  echo ""
  echo "✅ Arquivo .env criado."
  echo ""
  echo "👉 Abra o arquivo .env, preencha o ANTHROPIC_API_KEY e rode o script novamente:"
  echo "      bash start.sh"
  echo ""
  exit 0
fi

# ── Valida chave ──────────────────────────────────────────────
if grep -qE '^ANTHROPIC_API_KEY=[[:space:]]*$' .env; then
  echo "❌ ANTHROPIC_API_KEY está vazio no arquivo .env."
  echo "   Edite o .env, preencha sua chave e rode novamente:"
  echo "      bash start.sh"
  exit 1
fi

# ── Sobe o container ─────────────────────────────────────────
echo "🚀 Iniciando Construtor de Aulas..."
docker compose up "$@"
