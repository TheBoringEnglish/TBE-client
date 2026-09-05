# -*- coding: utf-8 -*-
"""
TheBoringEnglish 客户端一键 EXE 打包编译脚本
利用 PyInstaller 将应用程序编译为免安装、开箱即用的绿色单文件可执行软件 (TBE-Client.exe)。
"""

import os
import sys
import shutil
import subprocess


def run_command(cmd_list):
    print(f"[执行] {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    print("═══════════════════════════════════════════════════════════════")
    print("      TheBoringEnglish 桌面客户端 (TBE-Client) 一键打包工具      ")
    print("═══════════════════════════════════════════════════════════════")

    # 1. 检查 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("[依赖] 正在安装 PyInstaller 打包套件...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. 清理旧编译缓存
    dist_dir = os.path.join(root_dir, "dist")
    build_dir = os.path.join(root_dir, "build")
    spec_file = os.path.join(root_dir, "TBE-Client.spec")

    for p in [dist_dir, build_dir]:
        if os.path.exists(p):
            print(f"[清理] 清除旧缓存: {p}")
            shutil.rmtree(p, ignore_errors=True)
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # 3. 构造 PyInstaller 参数
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",       # 单文件便携版
        "--windowed",      # 无黑色终端弹窗
        "--name=TBE-Client",
        # 排除多余重型计算库以极大幅度缩减可执行文件体积
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "--exclude-module=scipy",
        "--exclude-module=matplotlib",
        "--exclude-module=pandas",
        "--exclude-module=notebook",
        # 显式包含网络与音频隐式依赖
        "--hidden-import=edge_tts",
        "--hidden-import=websockets",
        "--hidden-import=soundfile",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        # 搜索路径
        f"--paths={root_dir}",
    ]

    # 添加图标与内置静态资产
    icon_path = os.path.join(root_dir, "assets", "icon.ico")
    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")

    # 打包 assets 文件夹中的图标与静态素材
    assets_dir = os.path.join(root_dir, "assets")
    if os.path.exists(assets_dir):
        sep = ";" if sys.platform.startswith("win") else ":"
        cmd.append(f"--add-data={assets_dir}{sep}assets")

    # 主入口文件
    entry_point = os.path.join(root_dir, "src", "main.py")
    cmd.append(entry_point)

    print("\n[编译] 开始通过 PyInstaller 编译独立可执行程序...\n")
    try:
        run_command(cmd)

        exe_name = "TBE-Client.exe" if sys.platform.startswith("win") else "TBE-Client"
        final_exe_path = os.path.join(dist_dir, exe_name)

        print("\n═══════════════════════════════════════════════════════════════")
        print("🎉 [成功] 客户端单文件 EXE 编译打包完成！")
        print(f"📦 程序路径: {final_exe_path}")
        print("💡 您可以直接将此文件分发给任意用户，双击即可直接运行使用！")
        print("═══════════════════════════════════════════════════════════════\n")

    except Exception as e:
        print(f"\n❌ [错误] 编译打包失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
