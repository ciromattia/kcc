#!/bin/sh

pyside6-uic gui/KCC.ui --from-imports > kindlecomicconverter/KCC_ui.py
pyside6-uic gui/MetaEditor.ui --from-imports > kindlecomicconverter/KCC_ui_editor.py
pyside6-rcc gui/KCC.qrc > kindlecomicconverter/KCC_rc.py
