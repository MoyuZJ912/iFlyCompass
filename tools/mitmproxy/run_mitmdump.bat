@echo off
REM iFlyCompass Local mitmproxy Launcher
REM This launcher ensures using local mitmproxy and its dependencies

setlocal

set "PYTHONPATH=E:\Projects\iFlyCompass\tools\mitmproxy\libs;%PYTHONPATH%"

"E:\Projects\iFlyCompass\tools\mitmproxy\mitmdump.exe" %*
endlocal
