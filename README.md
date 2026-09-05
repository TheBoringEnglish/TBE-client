# TheBoringEnglish Client (TBE-Client)

<div align="center">

**面向所有英语学习者与创作者的现代化桌面算力与发音客户端**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-orange.svg)](https://wiki.qt.io/Qt_for_Python)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[功能特性](#-核心功能特性) • [快速启动](#-快速启动) • [一键打包发布](#-一键打包-exe-发布) • [开源安全规范](#-开源安全与隐私保护)

</div>

---

## 📖 项目简介

`tbe-client` 是 [TheBoringEnglish](https://theboringenglish.com) 官方推出的现代化桌面客户端。与内部管理工具不同，本项目专为**所有普通终端用户**设计打造，旨在为用户提供：

- 🎙️ **本地算力发音工坊 (TTS Studio)**：本地极速合成母语级纯正美音/英音，支持离线 AI 神经模型与在线高保真音色；
- 👣 **学习足迹一键出片 (Footprints & Remotion)**：同步您在 TheBoringEnglish 的日常文章精读、跟读对话与生词足迹，一键生成动态 Remotion 视频工程并在本地浏览器实时预览；
- ⚡ **分布式算力节点 (Compute Node)**：一键开启闲置算力挂机代跑，参与社区或个人发音任务，支持最小化至系统托盘后台静默运行；
- 🎨 **大厂级现代桌面 UI**：媲美 Notion / Linear / CapCut 的极简质感设计，支持深邃暗黑与透亮浅色双主题无缝切换。

---

## 🌟 核心功能特性

### 1. 本地发音工坊 (TTS Studio)
- **多音色矩阵**：覆盖美音（Jenny, Guy, Aria）、英音（Sonia, Ryan）、中文及中英双语；
- **离线神经发音**：支持 Kokoro ONNX 本地离线模型，断网也能秒级生成高保真语音；
- **实时音频控制台**：自研原生播放进度控制器，波形拖拽、播放/暂停、耗时统计，并支持一键将音频另存为本地 MP3/WAV。

### 2. 学习足迹与一键 Remotion 预览
- **云端足迹无缝同步**：一键拉取用户的阅读足迹、AI 跟读历史与重点生词；
- **多种视频模板**：纯文字动态、背景视频、羊皮纸排版、图说跟读卡片；
- **一键拉起预览**：点击“一键 Remotion 预览”，自动转换意群数据并在本地浏览器秒级打开 Studio 预览页面。

### 3. 分布式算力节点 (Compute Node)
- **挂机代跑**：利用本地算力协助处理 TTS 合成与音频切片任务；
- **任务实时流水**：黑曜石风格控制台实时展示任务吞吐、耗时与网络心跳；
- **系统托盘集成**：关闭时自动缩至任务栏托盘，不影响日常工作。

### 4. 纯净开源与安全隔离 (Zero-Secret)
- **无任何硬编码机密**：不包含任何私有 API Key、内部 token 或团队密码；
- **配置隔离**：用户凭证全部安全保存在本地用户主目录（`~/.tbe_client_config.json`），绝对不提交至代码仓库。

---

## 🚀 快速启动

### 方式 A：直接运行便携版 EXE（推荐普通用户）
前往 [Releases 页面](../../releases) 下载最新的 `TBE-Client.exe`，无需配置 Python 环境，双击即可直接使用！

---

### 方式 B：从源码运行（开发者）

#### 1. 克隆代码仓库
```bash
git clone https://github.com/TheBoringEnglish/tbe-client.git
cd tbe-client
```

#### 2. 安装 Python 依赖
推荐在虚拟环境中安装：
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 3. 启动应用
```bash
python -m src.main
# 或者在 Windows 下双击 run.bat
```

---

## 📦 一键打包 EXE 发布

本项目内置了自动化 PyInstaller 打包流程，排除了重型无关依赖（torch, tensorflow, pandas 等），生成体积紧凑、加载神速的单文件绿色版：

```bash
python build_exe.py
```
编译完成后，可在 `dist/` 目录下找到 `TBE-Client.exe`，直接分发即可。

> **💡 GitHub Actions 云端自动编译**：项目已配置 `.github/workflows/release.yml`。推送带有 `v*` 版本的 Git Tag 时，GitHub 会自动启动 Windows runner 编译并在 Releases 页面发布最新安装包。

---

## 🔒 开源安全与隐私保护

- 本项目遵循严格的安全防泄露规范；
- 所有网络请求默认走 HTTPS / WSS 加密协议；
- 用户 Token 在本地明文输入框中默认以掩码形式展示，用户可自主重置或清空。

---

## 📄 开源许可证

本项目采用 [MIT License](LICENSE) 开源许可协议。
