# TheBoringEnglish Desktop Client (TBE-Client)

<div align="center">

[English] | [中文](./README_zh.md)

**A modern, lightweight desktop speech engine & video history hub for language learners and creators**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-orange.svg)](https://wiki.qt.io/Qt_for_Python)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

[Features](#-key-features) • [Quick Start](#-quick-start) • [UI Showcase](#-modern-minimalist-ui-showcase) • [Executable Build](#-one-click-exe-packaging) • [Security & Privacy](#-security--privacy)

</div>

---

## 📖 Overview

`TBE-Client` is the official desktop companion application for [TheBoringEnglish](https://theboringenglish.com). Designed for end users and language learners, it combines local computing performance with a streamlined, clutter-free desktop experience:

- 👤 **One-Click Account Link**: Effortlessly sync your theboringenglish.com account, VIP status, and user profile via browser callback or direct token verification;
- ⚡ **Local Speech Engine**: A lightweight, one-click toggleable TTS node delivering ultra-low-latency, natural native American/British audio synthesis for intensive reading and browser shadowing;
- 🎬 **Video History Archive**: Triggered seamlessly from your web learning footprints, serving as a clean local project library with instant re-launch to Remotion Studio preview;
- 🌐 **Full Internationalization (i18n)**: Seamless hot-switching between English and Simplified Chinese;
- 🚀 **Ecosystem Connectivity**: Integrated direct links to the official Web platform and the TBE-YouTube bilingual subtitle extension;
- ⚙️ **Minimalist Pill Navigation**: Inspired by modern desktop aesthetics (Antigravity-Manager), featuring only two core pills (`⚙️ Settings & Speech` and `🎬 Video History`);
- 🎨 **Native Desktop Experience**: Tray icon with contextual menu, custom high-resolution icon, and taskbar group binding.

---

## 🌟 Key Features

### 1. Unified Control Center (Settings & Speech)
- **Speech Engine Switch**: Instant toggle for the local speech service right at the top of the home view;
- **Browser Token Sync**: Log in through your browser to sync credentials automatically via a local loopback server (`6502`), with zero manual copy-pasting;
- **System Preferences**: Theme selection (Dark / Light), language switcher, and minimize-to-tray configuration;
- **Collapsible Advanced Options**: Hide rarely modified ports and offline model paths to keep the interface focused and distraction-free.

### 2. Web Footprint Trigger & Video History (Video History)
- **Seamless Web Dispatch**: Click "Remotion Preview" or "Generate Video" on the web platform; the client captures the payload and automatically launches Remotion Studio;
- **Local History Archive**: Clean catalog tracking generated video projects, dates, templates, sentence counts, and estimated durations;
- **One-Click Preview & Cleanup**: Quickly re-launch any archived project in your browser or remove outdated entries.

### 3. System & Network Health Doctor (System Doctor)
- **Network Latency & Connectivity**: Concurrent diagnostics for YouTube, BBC, and TheBoringEnglish API;
- **Speech Engine Readiness**: Real-time handshake checks with Edge-TTS and offline Kokoro ONNX model weights;
- **Multimedia Environment**: Automatic detection of FFmpeg and Node.js runtimes;
- **Formatted Report Export**: Instant health status report generation with one-click clipboard copying.

### 4. Zero-Secret Architecture & Security
- **No Hardcoded Secrets**: Zero embedded private keys, internal tokens, or developer passwords;
- **Config Isolation**: All runtime credentials and tokens are stored exclusively in the user's home directory (`~/.tbe_client_config.json`), keeping the Git repository strictly clean.

---

## 🚀 Quick Start

### Option A: Portable Standalone Executable (Recommended for Users)
Download the latest `TBE-Client.exe` from the [Releases page](../../releases). No Python installation required—simply double-click to launch!

---

### Option B: Run from Source (Developers)

#### 1. Clone the Repository
```bash
git clone https://github.com/TheBoringEnglish/TBE-client.git
cd TBE-client
```

#### 2. Install Python Dependencies
Setting up a virtual environment is recommended:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 3. Launch the Application
- **Via PowerShell**:
```powershell
.\run.ps1
# Or run with Python directly:
python -m src.main
```

---

## 🎨 Modern Minimalist UI Showcase

Designed with clean typography and high-density information layout:
- **Top Pill Navbar**:
  - Distraction-free two-pill layout (`⚙️ Settings & Speech` and `🎬 Video History`);
  - Top-right utility group: `⛶` Fullscreen, `🌙/☀️` Theme Toggle, and `🇨🇳 ZH / 🇺🇸 EN` Language Switcher.
- **Home Control Board**:
  - Engine status card with live toggle;
  - Account sync card with browser authorization;
  - Preferences and collapsible advanced configurations.
- **Video History Page**:
  - Clean project list with template tags, sentence stats, and instant browser preview triggers.

---

## 📦 One-Click EXE Packaging

The project includes an automated PyInstaller packaging script that strips unused heavy modules (torch, tensorflow, pandas) to produce a compact, ultra-fast single-file binary:

```bash
python build_exe.py
```
Upon completion, the compiled `TBE-Client.exe` is located in the `dist/` directory, ready for immediate distribution.

> **💡 GitHub Actions CI/CD**: The repository is pre-configured with `.github/workflows/release.yml`. Pushing a git tag starting with `v*` will trigger an automated Windows runner build and publish the release assets automatically.

---

## 🔒 Security & Privacy

- Built on strict open-source privacy and security principles;
- All remote requests use secure HTTPS / WSS communication protocols;
- Sensitive tokens are masked in the UI and can be reset or cleared at any time.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
