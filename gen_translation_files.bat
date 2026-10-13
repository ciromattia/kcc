@echo off
rem Update translation sources (.ts) and rebuild the runtime translation
rem files (.qm), then re-bundle the .qm files into the Qt resource module
rem (KCC_rc.py). Run from the repository root.
setlocal

where pyside6-lupdate >nul 2>nul || (echo Error: pyside6-lupdate not found. Install it with: pip install pyside6 & exit /b 1)
where pyside6-lrelease >nul 2>nul || (echo Error: pyside6-lrelease not found. Install it with: pip install pyside6 & exit /b 1)
where pyside6-rcc >nul 2>nul || (echo Error: pyside6-rcc not found. Install it with: pip install pyside6 & exit /b 1)

rem 1. Update every translation source file in place.
rem    comic2ebook.py must stay in the list: the CLI-side messages live there.
for %%f in (translations\*.ts) do (
    pyside6-lupdate kindlecomicconverter\KCC_gui.py kindlecomicconverter\comic2ebook.py gui\KCC.ui gui\MetaEditor.ui -ts "%%f"
    if errorlevel 1 exit /b 1
)

rem 2. Compile each .ts into its .qm runtime file.
for %%f in (translations\*.ts) do (
    pyside6-lrelease "%%f" -qm "%%~dpnf.qm"
    if errorlevel 1 exit /b 1
)

rem 3. Re-bundle the .qm files into KCC_rc.py via the Qt resource file.
pyside6-rcc gui\KCC.qrc > kindlecomicconverter\KCC_rc.py
if errorlevel 1 exit /b 1

echo Translation files updated and re-bundled.
endlocal
