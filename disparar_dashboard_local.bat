@echo off
title Atualizando Dashboard Diretoria e Publicando no GitHub...
echo ========================================================
echo [1/3] Executando script Python de atualizacao local...
echo ========================================================

cd /d "c:\Users\marcelo.guedes\Grupo Fapes Projetos\Dr Hoje\dr-hoje-dashboard"

python scripts/update_dashboard.py

echo.
echo ========================================================
echo [2/3] Verificando alteracoes nos dados/html...
echo ========================================================

git config --global user.name "Marcelo Guedes"
git config --global user.email "marceloguedes@grupofapes.com.br"

git add -A
git diff --staged --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [3/3] Commitando e enviando dados novos para o GitHub Pages...
    git commit -m "data: atualizar base de dados do dashboard diretoria"
    git push origin main
    echo.
    echo ========================================================
    echo SUCESSO! Dashboard da Diretoria atualizado e publicado!
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo Nenhum dado novo alterado. Repositorio ja atualizado.
    echo ========================================================
)

ping 127.0.0.1 -n 4 > nul
