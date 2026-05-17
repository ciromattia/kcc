# -*- coding: utf-8 -*-
#
# Runtime GUI translations kept outside KCC_gui.py to reduce upstream merge
# conflicts. Static Qt Designer text is translated by translations/kcc_zh_CN.qm.

import re

from PySide6.QtCore import QCoreApplication


CONTEXT = 'KCCGUIRuntime'
UNSUPPORTED_FILE_PREFIX = 'Unsupported file type for '


def _qt(source):
    return QCoreApplication.translate(CONTEXT, source)


def translate(message):
    if not isinstance(message, str):
        return message

    translated = _qt(message)
    if translated != message:
        return translated

    # GitHub announcement messages are composed dynamically in KCC_gui.py.
    def translate_link(match):
        return match.group(1) + _qt(match.group(2)) + match.group(3)

    message = re.sub(r'(<a [^>]+><b>)(.*?)(</b></a>)', translate_link, message)
    message = re.sub(r': (\d+) day\(s\) left', lambda m: f': {m.group(1)} {_qt("day(s) left")}', message)
    message = message.replace(' [referral]', ' ' + _qt('[referral]'))

    if message.startswith(UNSUPPORTED_FILE_PREFIX):
        return _qt(UNSUPPORTED_FILE_PREFIX) + message[len(UNSUPPORTED_FILE_PREFIX):]

    return message


def _translate_label_text(text):
    if text == 'Gamma: Auto':
        return _qt('Gamma: Auto')
    if text.startswith('Gamma: '):
        return _qt('Gamma: ') + text[len('Gamma: '):]
    if text.startswith('Cropping Power: '):
        return _qt('Cropping Power: ') + text[len('Cropping Power: '):]
    return translate(text)


def install(KCC_gui):
    if getattr(KCC_gui, '_kcc_zh_cn_runtime_installed', False):
        return
    KCC_gui._kcc_zh_cn_runtime_installed = True

    original_add_message = KCC_gui.KCCGUI.addMessage

    def addMessage(self, message, icon, replace=False):
        return original_add_message(self, translate(message), icon, replace)

    KCC_gui.KCCGUI.addMessage = addMessage

    original_add_tray_message = KCC_gui.SystemTrayIcon.addTrayMessage

    def addTrayMessage(self, message, icon):
        return original_add_tray_message(self, translate(message), icon)

    KCC_gui.SystemTrayIcon.addTrayMessage = addTrayMessage

    original_mode_convert = KCC_gui.KCCGUI.modeConvert

    def modeConvert(self, enable):
        result = original_mode_convert(self, enable)
        if enable == 1:
            self.convertButton.setText(_qt('Convert'))
        elif enable == 0:
            self.convertButton.setText(_qt('Abort'))
        return result

    KCC_gui.KCCGUI.modeConvert = modeConvert

    original_change_gamma = KCC_gui.KCCGUI.changeGamma

    def changeGamma(self, value):
        result = original_change_gamma(self, value)
        self.gammaLabel.setText(_translate_label_text(self.gammaLabel.text()))
        return result

    KCC_gui.KCCGUI.changeGamma = changeGamma

    original_change_cropping_power = KCC_gui.KCCGUI.changeCroppingPower

    def changeCroppingPower(self, value):
        result = original_change_cropping_power(self, value)
        self.croppingPowerLabel.setText(_translate_label_text(self.croppingPowerLabel.text()))
        return result

    KCC_gui.KCCGUI.changeCroppingPower = changeCroppingPower

    original_meta_load_data = KCC_gui.KCCGUI_MetaEditor.loadData

    def loadData(self, file):
        result = original_meta_load_data(self, file)
        self.statusLabel.setText(translate(self.statusLabel.text()))
        return result

    KCC_gui.KCCGUI_MetaEditor.loadData = loadData

    original_meta_save_data = KCC_gui.KCCGUI_MetaEditor.saveData

    def saveData(self):
        result = original_meta_save_data(self)
        self.statusLabel.setText(translate(self.statusLabel.text()))
        return result

    KCC_gui.KCCGUI_MetaEditor.saveData = saveData
