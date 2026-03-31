@echo off
chcp 65001 >nul
title MarketInfo

cd /d "%~dp0"
python service_manager.py