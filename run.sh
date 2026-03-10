#!/bin/bash

# Ativa o ambiente virtual automaticamente
source .venv/bin/activate

echo "======================================"
echo "🤖 1/2: Iniciando extração do SIGAA..."
echo "======================================"
python robo.py

echo ""
echo "======================================"
echo "📊 2/2: Abrindo o Dashboard..."
echo "======================================"
streamlit run dashboard.py
