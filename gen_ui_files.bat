
REM install qt creator
REM conda create -n qtenv python=3.7
REM conda activate qtenv 
REM pip install PyQt5

pyuic5 gui/KCC.ui > kindlecomicconverter/KCC_ui.py

pyuic5 gui/MetaEditor.ui > kindlecomicconverter/KCC_ui_editor.py

pyrcc5 gui/KCC.qrc > kindlecomicconverter/KCC_rc.py