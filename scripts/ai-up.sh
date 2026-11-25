#!/usr/bin/env bash
# Sobe o Ollama nativo (usa a GPU do Mac) e baixa o modelo do .env antes do `make up`.
# Sem Ollama instalado, só avisa: o app sobe com a IA desligada.
set -u

env_value() { sed -n "s/^$1=//p" .env 2>/dev/null | tail -n 1; }
model="$(env_value AI_MODEL)"
model="${model:-deepseek-r1:8b}"
base_url="$(env_value AI_BASE_URL)"

# IA em outro serviço (ex.: DeepSeek na nuvem): nada a subir aqui.
if [[ -n "$base_url" && "$base_url" != *":11434"* ]]; then
  exit 0
fi

if ! command -v ollama >/dev/null; then
  echo "Aviso: Ollama não instalado (https://ollama.com/download); a IA fica desligada."
  exit 0
fi

ready() { curl -sf http://localhost:11434/api/version >/dev/null; }
if ! ready; then
  echo "Iniciando o Ollama..."
  nohup ollama serve >/tmp/ollama.log 2>&1 &
  for _ in $(seq 20); do ready && break; sleep 0.5; done
  ready || { echo "Aviso: o Ollama não respondeu (veja /tmp/ollama.log)."; exit 0; }
fi

if ! ollama list | awk 'NR > 1 { print $1 }' | grep -qx -e "$model" -e "$model:latest"; then
  echo "Baixando $model (só na primeira vez)..."
  ollama pull "$model"
fi
