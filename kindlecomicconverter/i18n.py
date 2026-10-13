# -*- coding: utf-8 -*-
"""KCC UI 语言切换辅助模块。"""
from PySide6.QtCore import QCoreApplication, QTranslator

# 语言代码 -> 菜单显示名（菜单按"各自语言"显示，不参与翻译）
LANGUAGES = {
    'en': 'English',
    'zh_CN': '中文（简体）',
    'ja_JP': '日本語',
    'ko_KR': '한국어',
}
DEFAULT_LANGUAGE = 'en'

# 模块级持有引用，防止 translator 被 GC 回收后失效
_translator = None


def apply_language(lang_code):
    """安装指定语言的 QTranslator，返回实际生效的 code。

    语言文件打包在 qrc 资源 /i18n/ 前缀下。
    """
    global _translator
    app = QCoreApplication.instance()
    if app is None:
        # QApplication 尚未创建，无法安装翻译器；保持默认语言
        return DEFAULT_LANGUAGE
    if _translator is not None:
        app.removeTranslator(_translator)
        _translator = None
    if lang_code not in LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    if lang_code != 'en':
        t = QTranslator()
        if t.load(f':/i18n/kcc_{lang_code}.qm'):
            app.installTranslator(t)
            _translator = t
        else:
            lang_code = DEFAULT_LANGUAGE
    return lang_code


def tr_arg(translated_str, *args):
    """替换翻译字符串中的 %1, %2, %3 ... 占位符。

    PySide6 的 tr() 返回 Python str 而非 QString，没有 .arg() 方法，
    因此用此函数手动替换占位符。
    """
    result = translated_str
    for i, arg in enumerate(args, 1):
        result = result.replace(f'%{i}', str(arg))
    return result
