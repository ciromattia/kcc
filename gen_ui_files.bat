
REM install qt creator
REM conda create -n qtenv python=3.7
REM conda activate qtenv 
REM pip install PyQt5

pyside6-uic gui/KCC.ui > kindlecomicconverter/KCC_ui.py

pyside6-uic gui/MetaEditor.ui > kindlecomicconverter/KCC_ui_editor.py

pyside6-rcc gui/KCC.qrc > kindlecomicconverter/KCC_rc.py