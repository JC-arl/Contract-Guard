@echo off
setlocal EnableDelayedExpansion

:: Pull Ollama quantized model variants that actually exist in the registry.
:: Disk usage: fp16 ~= 15GB, q8_0 ~= 8GB, q4_K_M ~= 4.7GB (total ~= 28GB).
:: Remove with "ollama rm <tag>" afterwards.
::
:: Tag list is kept in sync with SUPPORTED_QUANTIZATIONS in backend/app/config.py.

if "%LLM_BASE_MODEL%"=="" (
    set "BASE_MODEL=exaone3.5:7.8b"
) else (
    set "BASE_MODEL=%LLM_BASE_MODEL%"
)

set TAGS=q4_K_M q8_0 fp16

for %%t in (%TAGS%) do (
    set "FULL=!BASE_MODEL!-instruct-%%t"
    echo ==^> ollama pull !FULL!
    ollama pull "!FULL!"
    if errorlevel 1 (
        echo [ERROR] pull failed: !FULL!
        exit /b 1
    )
)

echo.
echo Done. Run "ollama list" to see local tags.
endlocal
