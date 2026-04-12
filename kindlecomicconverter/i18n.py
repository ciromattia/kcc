import json
import os
from PySide6.QtCore import QTranslator, QSettings


class JsonTranslator(QTranslator):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translations = {}
        self.loadLocale()

    def loadLocale(self, locale=None):
        if locale is None:
            # Read locale from QSettings, default to Spanish
            settings = QSettings('ciromattia', 'kcc9')
            locale = settings.value('locale', os.environ.get("KCC_LOCALE", "es"), type=str)

        locales_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales"
        )
        dict_file = os.path.join(locales_dir, f"kcc_{locale}.json")

        if os.path.exists(dict_file):
            try:
                with open(dict_file, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
            except Exception as e:
                print(f"i18n: Failed to load translations for '{locale}': {e}")
        else:
            print(f"i18n: Translation file not found: {dict_file}")
            self.translations = {}

    def translate(self, context, sourceText, disambiguation=None, n=-1):
        if not sourceText:
            return ""
        # Return translation if found, otherwise return the original text
        return self.translations.get(sourceText, sourceText)
