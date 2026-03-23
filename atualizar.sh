#!/bin/bash

# Entra na pasta do projeto
cd /home/ubuntu/SigaaWatch

# Ativa o ambiente virtual
source .venv/bin/activate

# Roda o robô de extração em modo invisível
python robo.py

# Configura a identidade do robô no Git (só é exigido na primeira vez)
git config user.email "bot@sigaawatch.com"
git config user.name "Robo SigaaWatch"

# Adiciona o arquivo novo, faz o commit com a data de hoje e envia!
git add dados_faltas.json
git commit -m "Atualização automática das faltas: $(date +'%d/%m/%Y')"
git push origin main
