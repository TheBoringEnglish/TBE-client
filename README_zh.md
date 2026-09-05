# TheBoringEnglish 桌面客户端 (TBE-Client)

<div align="center">

[English](./README.md) | [中文]

**面向所有英语学习者与创作者的现代化桌面算力与发音客户端**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-orange.svg)](https://wiki.qt.io/Qt_for_Python)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[功能特性](#-核心功能特性) • [快速启动](#-快速启动) • [界面设计](#-现代化极简界面-ui-showcase) • [一键打包发布](#-一键打包-exe-发布) • [开源安全规范](#-开源安全与隐私保护)

</div>

---

## 📖 项目简介

`TBE-client` 是 [TheBoringEnglish](https://theboringenglish.com) 官方推出的现代化桌面客户端。与内部管理工具不同，本项目专为**所有普通终端用户**设计打造，旨在为用户提供：

- 👤 **theboringenglish.com 账号一键关联**：一键登录官方账户，自动同步用户资料与权益状态；
- ⚡ **本地发音引擎 (Local Speech Engine)**：极简一键启停开关，作为高速发音服务节点，为精读与浏览器跟读提供毫秒级高保真原声发音；
- 🎬 **足迹出片历史 (Video History)**：由 theboringenglish.com 网页端学习足迹直接调起生成视频，客户端化身轻量纯净的本地出片历史档案库，支持一键在浏览器重新拉起预览与历史管理；
- 🌐 **全功能国际化 (i18n)**：简体中文与英文无缝切换；
- 🚀 **生态无缝互联**：内置 TheBoringEnglish 官网与 TBE-YouTube 浏览器双语字幕扩展直达入口；
- ⚙️ **极简双胶囊导航**：参考 Antigravity-Manager 现代化美学，顶部仅保留【⚙️ 设置与发音】与【🎬 出片历史】两大核心胶囊，首页即主控，无冗长多余层级；
- 🎨 **原生桌面级体验**：支持 Windows 系统托盘右键快捷菜单、自定义高清图标与任务栏分组绑定。

---

## 🌟 核心功能特性

### 1. 首页一键主控 (Settings & Speech)
- **本地发音引擎开关**：首页顶部一键切换启用/暂停，状态清晰直观；
- **官方账号一键互联**：支持打开官网浏览器一键登录免密同步至客户端，亦可直接粘贴 Token；
- **系统偏好设置**：语言、深浅主题、关闭主界面时保持后台托盘运行；
- **折叠高级设置**：默认收纳非必改的高级服务端口与离线模型路径，不干扰日常使用。

### 2. 网页端足迹调起与出片历史档案 (Video History)
- **网页端无缝调起**：在 theboringenglish.com 网页端点击足迹「一键 Remotion 预览」或生成视频，客户端通过本地 6502 端口自动捕获并唤起本地 Remotion 运行时；
- **本地出片历史档案**：客户端专注做好轻量展示，完整归档已生成的视频工程，记录生成时间、模板、意群句数及预计时长；
- **一键重新预览与管理**：随时可在客户端一键重新在浏览器拉起 Remotion Studio 预览，或对历史出片记录进行删除维护。

### 3. 系统环境与网络健康体检 (System Doctor)
- **多维度网络连通测试**：并发排查 YouTube 学习通道、BBC 听力原声媒体通道与 TheBoringEnglish 官网 API 响应状态及毫秒延迟；
- **发音引擎可用性诊断**：在线验证微软 Edge-TTS 语音握手回包，以及 Kokoro 本地离线神经网络模型权重与推理依赖；
- **核心多媒体依赖检查**：自动检测 FFmpeg 编解码器与 Node.js 视频合成运行时是否存在；
- **一键体检与报告导出**：顶部快捷按钮 `🩺` 或偏好设置中随时一键呼出，支持格式化体检报告一键复制。

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
git clone https://github.com/TheBoringEnglish/TBE-client.git
cd TBE-client
```

#### 2. 安装 Python 依赖
推荐在虚拟环境中安装：
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 3. 启动应用
- **PowerShell 启动**：
```powershell
.\run.ps1
# 或者直接使用 python 运行:
python -m src.main
```

---

## 🎨 现代化极简界面 (UI Showcase)

客户端界面采用现代化极简美学：
- **顶部 Header 药丸胶囊主导航 (Top Pill Navbar)**：
  - 仅保留核心的 `⚙️ 设置与发音` 与 `🎬 出片历史` 两个胶囊，消除认知负担；
  - 右侧工具组：支持 `⛶` 全屏化、`🌙/☀️` 暗黑与明亮主题一键切换、`🇨🇳 ZH / 🇺🇸 EN` 语言药丸即时热重载。
- **首页主控台**：
  - 发音引擎状态与启停开关卡片；
  - 官网账户一键关联卡片；
  - 界面与偏好卡片；
  - 折叠式高级设置与生态互联入口。
- **出片历史页**：
  - 纯净列表，展示由网页端调起生成的视频历史，支持一键浏览器预览与清理。

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
