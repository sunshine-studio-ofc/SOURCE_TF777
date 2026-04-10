@echo off
:: Define o título da janela do console (mesmo que ela feche rápido)
title TF777_BOOT_PROCESS

:: Pega o caminho da pasta onde o .bat está
set "ROOT_DIR=%~dp0"

:: Muda o diretório de trabalho para a pasta do robô
:: Isso garante que o Python encontre o "ico.ico" e os módulos locais
cd /d "%ROOT_DIR%"

:: Executa o main.py usando o pythonw (invisível)
:: O primeiro par de aspas "" é o título do processo para o Windows
:: O comando 'start' exige que o título venha antes do comando de execução
start "TF-777 OS" pythonw "main.py"

:: Fecha o processo do lote imediatamente
exit