# KCC 项目 i18n 多语言支持 — 开发者说明文档

> 本文档面向接手此项目的其他 agent/开发者，帮助快速理解 KCC 项目的多语言（i18n）实现方式、架构、关键文件和常见操作。

---

## 一、项目概览

**KCC (Kindle Comic Converter)** 是一个用 Python + PySide6 编写的漫画/电子书格式转换工具，可将图片/CBZ/PDF 等转换为 Kindle/Kobo 等设备可读的 MOBI/EPUB/KFX 等格式。

- **主仓库**: https://github.com/ciromattia/kcc
- **本地工作目录**: `d:\KccLanguage\kcc-upstream\`（这是从上游 fork 后的代码，已添加 i18n 功能）
- **GUI 框架**: PySide6 (Qt 6)
- **入口文件**: `kcc.py` → `kindlecomicconverter/startup.py:start()` → `kindlecomicconverter/KCC_gui.py`

---

## 二、i18n 实现架构

### 2.1 核心设计思路

KCC 的 i18n 完全基于 **Qt 原生的国际化机制**（QTranslator + .ts/.qm 文件），而非自己实现翻译框架。

```
用户点击语言菜单
    → changeLanguage(lang_code)
        → i18n.apply_language(lang_code)   # 安装/替换 QTranslator
        → self.retranslateUi(MW)            # Qt 自动重译所有 UI 静态文本
        → self.updateDynamicText()          # 手动刷新代码中动态写入的文本
        → 同步刷新 MetaEditor 弹窗
```

### 2.2 关键技术点

| 概念 | 说明 |
|------|------|
| **QTranslator** | Qt 提供的翻译器，从 .qm 文件加载翻译，安装到 QApplication 后 `tr()` 会自动查找翻译 |
| **.ts 文件** | Qt 翻译源文件（XML 格式），人类可读可编辑，包含原文和译文 |
| **.qm 文件** | .ts 编译后的二进制文件，运行时加载，体积小加载快 |
| **tr()** | QObject 的方法，将字符串标记为可翻译，运行时返回翻译后的文本 |
| **retranslateUi()** | Qt UIC 自动生成的方法，调用所有 UI 控件的 `setText(tr("..."))` 来刷新界面文本 |
| **tr_arg()** | 自定义辅助函数，替代 PySide6 中缺失的 `QString.arg()` 用于替换 %1/%2 占位符 |
| **QRC 资源系统** | Qt 的资源打包机制，翻译 .qm 文件被打包进资源，随程序一起分发 |

### 2.3 为什么需要 QObject 继承？

`self.tr()` 方法是 `QObject` 提供的。原来的 `KCCGUI` 和 `KCCGUI_MetaEditor` 类**没有继承 QObject**，所以不能直接用 `self.tr()`。

**解决方案**：让两个类多继承 `QObject`：

```python
class KCCGUI(QObject, KCC_ui.Ui_mainWindow):
    def __init__(self, kccapp, kccwindow):
        QObject.__init__(self)   # 必须显式调用 QObject 初始化
        ...
```

---

## 三、关键文件清单

### 3.1 核心代码文件

| 文件路径 | 作用 | 改动状态 |
|----------|------|----------|
| `kindlecomicconverter/i18n.py` | **i18n 核心模块**：语言切换、translator 管理、tr_arg 工具函数 | ✅ 新增 |
| `kindlecomicconverter/KCC_gui.py` | 主 GUI 逻辑：语言按钮、菜单、changeLanguage()、updateDynamicText() | ✅ 修改 |
| `kindlecomicconverter/KCC_ui.py` | 主窗口 UI 定义（由 Qt UIC 从 .ui 生成），含 retranslateUi() | 自动生成 |
| `kindlecomicconverter/KCC_ui_editor.py` | 元数据编辑器 UI 定义 | 自动生成 |
| `gui/KCC.qrc` | Qt 资源文件，新增 `/i18n` 前缀包含所有 .qm 文件 | ✅ 修改 |
| `kindlecomicconverter/KCC_rc.py` | 编译后的资源文件（pyside6-rcc 生成） | ✅ 重新生成 |

### 3.2 翻译文件

翻译文件位于 `translations/` 目录：

| 文件 | 语言 | 类型 |
|------|------|------|
| `kcc_zh_CN.ts` | 简体中文 | 源文件（XML） |
| `kcc_zh_CN.qm` | 简体中文 | 编译后二进制 |
| `kcc_ja_JP.ts` | 日语 | 源文件（XML） |
| `kcc_ja_JP.qm` | 日语 | 编译后二进制 |
| `kcc_ko_KR.ts` | 韩语 | 源文件（XML） |
| `kcc_ko_KR.qm` | 韩语 | 编译后二进制 |

> **英文 (en)** 是默认语言，不需要翻译文件——源代码中的字符串本身就是英文。

---

## 四、i18n.py 模块详解

### 4.1 LANGUAGES 字典

定义所有支持的语言及其显示名（菜单按"各自语言"显示）：

```python
LANGUAGES = {
    'en': 'English',
    'zh_CN': '中文（简体）',
    'ja_JP': '日本語',
    'ko_KR': '한국어',
}
DEFAULT_LANGUAGE = 'en'
```

### 4.2 apply_language(lang_code)

核心函数。安装指定语言的 QTranslator：

1. 如果已有 translator，先移除（避免多个 translator 叠加）
2. 非英语语言才需要加载 translator
3. 从 QRC 资源 `:/i18n/kcc_{lang_code}.qm` 加载
4. 安装到 QApplication
5. 返回实际生效的语言代码（加载失败回退到 en）

**重要**：模块级 `_translator` 变量持有 translator 引用，防止被 Python GC 回收后翻译失效。

### 4.3 tr_arg(translated_str, *args)

PySide6 的 `tr()` 返回 Python `str` 而非 `QString`，因此没有 `.arg()` 方法。

用此函数手动替换翻译字符串中的 `%1`, `%2`, `%3` ... 占位符：

```python
# 用法示例
i18n.tr_arg(self.tr('Gamma: %1'), value)
i18n.tr_arg(self.tr('Processing %1/%2: %3'), i, total, filename)
```

---

## 五、语言切换流程详解

### 5.1 初始化时加载语言

在 `KCCGUI.__init__` 中：

```python
self.settings = QSettings('ciromattia', 'kcc10')
self.language = str(self.settings.value('language', i18n.DEFAULT_LANGUAGE))
self.language = i18n.apply_language(self.language)
# 之后才调用 setupUi(MW)，确保首次渲染就用正确语言
```

语言设置持久化在 QSettings（Windows 上是注册表，macOS/Linux 是配置文件）。

### 5.2 用户切换语言

用户点击右上角 🌐 按钮 → 弹出语言菜单 → 选择某语言：

```python
def changeLanguage(self, lang_code):
    self.language = i18n.apply_language(lang_code)   # 1. 切换 translator
    self.settings.setValue('language', self.language) # 2. 保存设置
    self.retranslateUi(MW)                            # 3. 刷新 UI 静态文本
    self.updateDynamicText()                          # 4. 刷新动态文本
    # 5. 同步刷新元数据编辑器
    if hasattr(self, 'editor'):
        self.editor.retranslateUi(self.editor.ui)
        self.editor.updateDynamicText()
    # 6. 更新菜单勾选状态
    for act in self.languageMenu.actions():
        act.setChecked(act.data() == self.language)
```

### 5.3 动态文本为什么需要单独处理？

`retranslateUi()` 只能刷新在 `.ui` 文件中定义的静态文本。

但有些文本是**代码运行时动态设置**的，例如：
- 窗口标题（含版本号）
- Convert/Abort 按钮状态切换
- Gamma/Cropping Power 滑块标签（含数值）
- 语言按钮 tooltip
- MetaEditor 中的占位符文本

这些需要在 `updateDynamicText()` 中手动重新调用 `self.tr()` 设置。

---

## 六、翻译文件的生成与更新流程

### 6.1 从源码提取可翻译字符串

使用 Qt 的 `pyside6-lupdate` 工具扫描代码中所有 `self.tr("...")` 调用，生成/更新 .ts 文件：

```bash
# 生成/更新简体中文翻译文件
pyside6-lupdate kindlecomicconverter/KCC_gui.py -ts translations/kcc_zh_CN.ts

# 可以一次指定多个源文件
pyside6-lupdate kindlecomicconverter/KCC_gui.py gui/KCC.ui -ts translations/kcc_zh_CN.ts
```

### 6.2 编辑翻译

.ts 文件是 XML，可以直接用文本编辑器编辑，也可以用 Qt Linguist 图形化工具：

```xml
<message>
    <source>Convert</source>
    <translation>转换</translation>
</message>
```

未翻译的条目会有 `type="unfinished"` 属性。

### 6.3 编译为 .qm 文件

```bash
pyside6-lrelease translations/kcc_zh_CN.ts -qm translations/kcc_zh_CN.qm
```

### 6.4 重新编译资源文件

.qm 文件添加到 `gui/KCC.qrc` 后，需要重新生成 `KCC_rc.py`：

```bash
pyside6-rcc gui/KCC.qrc -o kindlecomicconverter/KCC_rc.py
```

---

## 七、如何添加一门新语言

以添加法语（fr_FR）为例：

1. **生成 .ts 文件**：
   ```bash
   pyside6-lupdate kindlecomicconverter/KCC_gui.py gui/KCC.ui gui/MetaEditor.ui -ts translations/kcc_fr_FR.ts
   ```

2. **翻译**：编辑 `translations/kcc_fr_FR.ts`，填入所有 `<translation>` 内容。

3. **编译 .qm**：
   ```bash
   pyside6-lrelease translations/kcc_fr_FR.ts -qm translations/kcc_fr_FR.qm
   ```

4. **注册到 i18n.py**：在 `LANGUAGES` 字典中添加 `'fr_FR': 'Français'`。

5. **添加到 QRC**：编辑 `gui/KCC.qrc`，在 `/i18n` 前缀下添加一行：
   ```xml
   <file alias="kcc_fr_FR.qm">../translations/kcc_fr_FR.qm</file>
   ```

6. **重新编译资源**：
   ```bash
   pyside6-rcc gui/KCC.qrc -o kindlecomicconverter/KCC_rc.py
   ```

7. **测试**：运行程序，切换到新语言验证。

---

## 八、打包发布

### 8.1 PyInstaller 打包

翻译文件已经通过 QRC 资源系统编译进 `KCC_rc.py`，因此 PyInstaller 打包时**不需要额外处理翻译文件**——它们已经在代码里了。

打包命令示例（Windows）：
```bash
pyinstaller kcc.spec
```

### 8.2 验证

打包后的 `KCC.exe` 应能正常切换语言，不需要额外的翻译文件目录。

---

## 九、常见问题与注意事项

### Q1: tr() 不生效，文本还是英文？

- 检查类是否继承了 `QObject`，且 `__init__` 中调用了 `QObject.__init__(self)`
- 检查 QTranslator 是否成功加载（`t.load()` 返回 True/False）
- 检查 .qm 文件路径是否正确（QRC 路径是 `:/i18n/kcc_xx_XX.qm`）
- 检查 translator 是否被 GC 回收（必须用全局/实例变量持有引用）

### Q2: 切换语言后有些文本没更新？

- **UI 静态文本**没更新：检查是否在代码里硬编码了 setText，而没有在 `updateDynamicText()` 中重新设置
- **动态文本**没更新：把该文本的重新设置加到 `updateDynamicText()` 方法里

### Q3: 新增的 tr() 字符串在 .ts 里找不到？

需要重新运行 `pyside6-lupdate` 来提取新的字符串。

### Q4: 占位符替换（%1, %2）怎么用？

```python
# 错误：直接用 f-string 或 format，翻译时无法调整语序
self.tr(f'Gamma: {value}')

# 正确：用 %1 占位符 + tr_arg()
i18n.tr_arg(self.tr('Gamma: %1'), value)
```

这样翻译者可以调整语序，比如某些语言把数值放在前面。

### Q5: HTML 标签里的文本能翻译吗？

可以，`tr()` 支持 HTML 字符串。HTML 标签会被保留，只翻译文本部分：

```python
self.tr('<a href="...">Click here</a> for more info.')
```

---

## 十、项目目录结构速查

```
kcc-upstream/
├── kcc.py                          # 主入口
├── kcc.spec                        # PyInstaller 打包配置
├── gui/
│   ├── KCC.qrc                     # Qt 资源文件（含 i18n 翻译资源）
│   ├── KCC.ui                      # 主窗口 UI 设计文件
│   └── MetaEditor.ui               # 元数据编辑器 UI 设计文件
├── kindlecomicconverter/
│   ├── __init__.py
│   ├── startup.py                  # 启动逻辑
│   ├── KCC_gui.py                  # ⭐ 主 GUI 逻辑（含语言切换）
│   ├── KCC_ui.py                   # UIC 生成的主窗口 UI 类
│   ├── KCC_ui_editor.py            # UIC 生成的编辑器 UI 类
│   ├── KCC_rc.py                   # RCC 编译的资源文件
│   ├── i18n.py                     # ⭐ i18n 核心模块（新增）
│   ├── comic2ebook.py              # 转换核心逻辑
│   ├── metadata.py                 # 元数据处理
│   └── ...                         # 其他模块
├── translations/                   # ⭐ 翻译文件（新增目录）
│   ├── kcc_zh_CN.ts / .qm
│   ├── kcc_ja_JP.ts / .qm
│   └── kcc_ko_KR.ts / .qm
├── icons/                          # 图标资源
├── images/                         # 图片资源
└── requirements.txt                # Python 依赖
```

---

## 十一、运行项目

### 源码运行

```bash
cd d:\KccLanguage\kcc-upstream
pip install -r requirements.txt
python kcc.py
```

### 打包后的 EXE

```
d:\KccLanguage\kcc\dist\KCC\KCC.exe
```

---

*文档版本: 1.0 | 最后更新: 基于 KCC + i18n 功能版本*
