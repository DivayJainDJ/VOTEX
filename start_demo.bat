@echo off
REM Batch script to launch example browser client WebSocket server and an HTTP server, then open the demo in a browser.
REM Save this file in: RealtimeSTT/RealtimeSTT/example_browserclient/start_demo.bat

REM Make sure we start from the batch file's folder
cd /d %~dp0

REM Launch example browser WebSocket server in a new window (keeps window open to view logs)
start "RealtimeSTT Browser WS Server" cmd /k "python server.py"

REM Launch a simple HTTP file server in a new window on port 8080 (serves index.html)
start "RealtimeSTT HTTP Server" cmd /k "python -m http.server 8080"

REM Give servers a second to start up (optional)
timeout /t 1 >nul

REM Open the demo page in the default browser
start http://localhost:8080/index.html

REM Done — the batch script will exit while the server windows remain open.
exit 0