@echo off
verpatch\lib\win\verpatch dist\KCC.exe %1 /va /pv %1 /s product "Kindle Comic Converter" /s description "Kindle Comic Converter" /s copyright "Copyright (C) 2012-2017 Ciro Mattia Gonano and Pawel Jastrzebski"
"C:\Program Files (x86)\Windows Kits\8.1\bin\x64\signtool.exe" sign /f "%APPVEYOR_BUILD_FOLDER%\other\windows\Cert.pfx" /p "%CERT_PASS%" /t http://time.certum.pl /d "Kindle Comic Converter" /du "http://kcc.iosphe.re/" dist/KCC.exe
iscc /SSignTool="""C:\Program Files (x86)\Windows Kits\8.1\bin\x64\signtool.exe"" sign /f ""%APPVEYOR_BUILD_FOLDER%\other\windows\Cert.pfx"" /p ""%CERT_PASS%"" /t http://time.certum.pl $p" kcc.iss >nul 2>&1
