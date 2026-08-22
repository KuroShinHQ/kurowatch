@echo off
:: kurowatch.bat v2.0 - INCE SARMLAYICI (BAT_OLUSTURMA_REHBERI standardi)
:: Tum mantik kurowatch_menu.py icinde; bu dosya sadece TUI'i cagirir.
:: Otomasyon destegi korunur: kurowatch.bat 4  ->  dogrudan eylem 4.
title KuroWatch Izleme Kulesi
chcp 65001 >nul
mode con: cols=112 lines=40
cd /d "%~dp0"
python kurowatch_menu.py %1
