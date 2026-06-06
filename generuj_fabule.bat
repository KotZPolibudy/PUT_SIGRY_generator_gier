@echo off
chcp 65001 > nul

echo ======================================================
echo Generator Fabuły i Questów PDDL
echo ======================================================
echo.

set "STORY_PROMPT=%~1"
set "MAX_REPAIRS=%~2"
set "GEN_IMAGES=%~3"

if "%STORY_PROMPT%"=="" (
    set /p "STORY_PROMPT=Wpisz prompt (temat fabuły): "
)

if "%STORY_PROMPT%"=="" (
    echo Błąd: Prompt nie może być pusty!
    pause
    exit /b 1
)

if "%MAX_REPAIRS%"=="" (
    set /p "MAX_REPAIRS=Wpisz maksymalną liczbę napraw (domyślnie 10): "
)
if "%MAX_REPAIRS%"=="" (
    set "MAX_REPAIRS=10"
)

if "%GEN_IMAGES%"=="" (
    set /p "GEN_IMAGES=Czy generować obrazy Stable Diffusion? (t/n, domyślnie n): "
)
if "%GEN_IMAGES%"=="" (
    set "GEN_IMAGES=n"
)

echo.
echo ======================================================
echo Rozpoczynam generowanie z parametrami:
echo - Prompt: "%STORY_PROMPT%"
echo - Max repairs: %MAX_REPAIRS%
echo - Generowanie obrazów: %GEN_IMAGES%
echo ======================================================
echo.

python generate_story.py --prompt "%STORY_PROMPT%" --max-repairs %MAX_REPAIRS%
if %ERRORLEVEL% neq 0 (
    echo.
    echo [BŁĄD] Wystąpił błąd podczas generowania fabuły.
    pause
    exit /b %ERRORLEVEL%
)

:: Sprawdzenie czy użytkownik wybrał opcję generowania obrazów
if /i "%GEN_IMAGES%"=="t" goto :generate_images
if /i "%GEN_IMAGES%"=="y" goto :generate_images
if /i "%GEN_IMAGES%"=="tak" goto :generate_images
if /i "%GEN_IMAGES%"=="yes" goto :generate_images
goto :done

:generate_images
echo.
echo ======================================================
echo Generowanie obrazów (Stable Diffusion)...
echo ======================================================

:: Pobranie nazwy folderu (slug) za pomocą Pythona z importowanego skryptu
for /f "tokens=*" %%i in ('python -c "import os, sys; sys.path.append('.'); import generate_story; print(generate_story.get_campaign_slug(os.environ.get('STORY_PROMPT', '')))"') do set "CAMPAIGN_SLUG=%%i"

if "%CAMPAIGN_SLUG%"=="" (
    echo [BŁĄD] Nie można wyznaczyć unikalnej nazwy folderu dla podanego promptu.
    goto :done
)

python generate_images.py --story_name "%CAMPAIGN_SLUG%"
if %ERRORLEVEL% neq 0 (
    echo [BŁĄD] Wystąpił błąd podczas generowania obrazów.
) else (
    echo Obrazy zostały wygenerowane pomyślnie w folderze: quests\%CAMPAIGN_SLUG%\images\
)

:done
echo.
echo Generowanie zakończone sukcesem!
pause
