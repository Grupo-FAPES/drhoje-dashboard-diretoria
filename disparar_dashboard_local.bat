@echo off
title Atualizando Dashboard Diretoria e Publicando no GitHub...

cd /d "c:\Users\marcelo.guedes\Grupo Fapes Projetos\Dr Hoje\dr-hoje-dashboard"

if not exist "data" mkdir "data"
set LOGFILE=data\execucao_atualizacao.log

echo ======================================================== >> %LOGFILE%
echo [%DATE% %TIME%] INICIANDO ATUALIZACAO LOCAL - DIRETORIA >> %LOGFILE%
echo ======================================================== >> %LOGFILE%

echo ========================================================
echo [1/3] Executando script Python de atualizacao local...
echo ========================================================

python scripts/update_dashboard.py >> %LOGFILE% 2>&1

echo.
echo ========================================================
echo [2/3] Verificando alteracoes no index.html...
echo ========================================================

git config --global user.name "Marcelo Guedes"
git config --global user.email "marceloguedes@grupofapes.com.br"

git add index.html .gitignore dashboard_dr_hoje.html scripts/ .github/
git diff --staged --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [3/3] Commitando e enviando painel atualizado para o GitHub Pages...
    git commit -m "data: atualizar base de dados do dashboard diretoria" >> %LOGFILE% 2>&1
    git push origin main >> %LOGFILE% 2>&1
    echo [%DATE% %TIME%] SUCESSO! Dashboard da Diretoria atualizado e publicado no GitHub! >> %LOGFILE%
    echo.
    echo ========================================================
    echo SUCESSO! Dashboard da Diretoria atualizado e publicado!
    echo Log salvo em: data\execucao_atualizacao.log
    echo ========================================================
) else (
    echo [%DATE% %TIME%] Nenhum dado novo alterado no index.html. >> %LOGFILE%
    echo.
    echo ========================================================
    echo Nenhum dado novo alterado. Repositorio ja atualizado.
    echo Log salvo em: data\execucao_atualizacao.log
    echo ========================================================
)

ping 127.0.0.1 -n 3 > nul
