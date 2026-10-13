#!/bin/sh
# Update translation sources (.ts) and rebuild the runtime translation
# files (.qm), then re-bundle the .qm files into the Qt resource module
# (KCC_rc.py). Run from the repository root.

set -e

# Fail early if the PySide6 translation tools are missing.
for tool in pyside6-lupdate pyside6-lrelease pyside6-rcc; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Error: $tool not found. Install it with: pip install pyside6" >&2
        exit 1
    fi
done

# 1. Update every translation source file in place.
#    comic2ebook.py must stay in the list: the CLI-side messages live there.
for ts in translations/*.ts; do
    pyside6-lupdate \
        kindlecomicconverter/KCC_gui.py \
        kindlecomicconverter/comic2ebook.py \
        gui/KCC.ui \
        gui/MetaEditor.ui \
        -ts "$ts"
done

# 2. Compile each .ts into its .qm runtime file.
for ts in translations/*.ts; do
    pyside6-lrelease "$ts" -qm "${ts%.ts}.qm"
done

# 3. Re-bundle the .qm files into KCC_rc.py via the Qt resource file.
pyside6-rcc gui/KCC.qrc > kindlecomicconverter/KCC_rc.py

echo "Translation files updated and re-bundled."
