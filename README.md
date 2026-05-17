# 本仓库是一个纯汉化 Fork

本仓库只做 **Kindle Comic Converter** 的中文界面与中文文档适配，尽量保持与上游项目同步。功能介绍、下载、FAQ、已知问题、使用教程和完整项目说明，请直接查看原仓库：

[ciromattia/kcc](https://github.com/ciromattia/kcc)

## 本地启动

建议使用 Python 3.13，与项目 Dockerfile 的目标环境保持一致。

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python kcc.py
```

如果已经创建并激活虚拟环境，可以直接运行：

```bash
python kcc.py
```

命令行工具入口：

```bash
python kcc-c2e.py --help
python kcc-c2p.py --help
```

## 汉化文件

静态 Qt 界面翻译文件：

```text
translations/kcc_zh_CN.qt.xml
translations/kcc_zh_CN.qm
```

运行时消息汉化集中在：

```text
kindlecomicconverter/i18n_zh_CN.py
```

重新编译 Qt 翻译文件：

```bash
.venv/bin/pyside6-lrelease translations/kcc_zh_CN.qt.xml -qm translations/kcc_zh_CN.qm
```

如果上游更新了 `.ui` 文件，需要重新提取翻译源并补中文：

```bash
.venv/bin/pyside6-lupdate gui/KCC.ui gui/MetaEditor.ui -ts translations/kcc_zh_CN.qt.xml
.venv/bin/pyside6-lrelease translations/kcc_zh_CN.qt.xml -qm translations/kcc_zh_CN.qm
```

## 构建

构建桌面应用：

```bash
python setup.py build_binary
```

构建命令行工具：

```bash
python setup.py build_c2e
python setup.py build_c2p
```

Docker 构建请参考项目内 [Dockerfile](./Dockerfile)，更多平台打包和发布信息请查看上游文档：

[ciromattia/kcc](https://github.com/ciromattia/kcc)

## 许可证

本仓库保留上游项目许可证。详情见 [LICENSE.txt](./LICENSE.txt)。
