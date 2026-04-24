@echo off
chcp 65001 >nul

echo === K^&H2 종료 ===
taskkill /f /im ollama.exe >nul 2>&1 && (echo Ollama 종료) || (echo Ollama 미실행)

:: 백엔드: uvicorn 부모 PID로 taskkill /T (트리 전체: reloader + multiprocessing 손자까지)
:: CommandLine 매칭만으로는 "multiprocessing.spawn" 손자를 놓쳐 좀비가 남음
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*uvicorn backend.app.main*' } | ForEach-Object { Start-Process -FilePath taskkill -ArgumentList '/F','/T','/PID',$_.ProcessId -NoNewWindow -Wait }" >nul 2>&1
:: 백엔드 8000 포트 기반 강제 종료 (CommandLine 매칭 누락 대비)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /t /pid %%a >nul 2>&1
:: 좀비 multiprocessing 자식 정리 (부모가 이미 죽은 고아 프로세스)
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*multiprocessing.spawn*' } | ForEach-Object { $ppid = $_.ParentProcessId; if (-not (Get-Process -Id $ppid -ErrorAction SilentlyContinue)) { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }" >nul 2>&1
echo 백엔드 종료

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
echo 프론트엔드 종료
echo === 완료 ===
pause
