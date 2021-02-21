#!/bin/sh

# PREPARE PYTHON ENV
# conda create -n pyqt5 python=3.7
# source activate pyqt5
# pip install pyqt5

pyuic5 gui/KCC.ui --from-imports > kindlecomicconverter/KCC_ui.py
pyuic5 gui/MetaEditor.ui --from-imports > kindlecomicconverter/KCC_ui_editor.py
pyrcc5 gui/KCC.qrc > kindlecomicconverter/KCC_rc.py