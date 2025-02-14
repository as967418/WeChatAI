import os
import shutil
import subprocess
from datetime import datetime
import sys

def create_backup():
    """创建源代码备份"""
    print("正在创建源代码备份...")
    backup_dir = "backups"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"source_backup_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # 创建备份目录
    os.makedirs(backup_dir, exist_ok=True)
    
    # 要备份的文件和目录
    items_to_backup = [
        'core',
        'ui',
        'data',
        'main.py',
        'requirements.txt',
        'resources.qrc',
        'resources_rc.py'
    ]
    
    # 创建备份
    os.makedirs(backup_path)
    for item in items_to_backup:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.copytree(item, os.path.join(backup_path, item))
            else:
                shutil.copy2(item, backup_path)
    
    # 创建zip文件
    shutil.make_archive(backup_path, 'zip', backup_path)
    shutil.rmtree(backup_path)  # 删除临时目录
    print(f"备份完成: {backup_path}.zip")
    return True

def encrypt_with_pyarmor():
    """使用pyarmor加密源代码"""
    print("正在加密源代码...")
    try:
        # 创建构建目录
        build_dir = "build"
        encrypted_dir = os.path.join(build_dir, "encrypted")
        os.makedirs(encrypted_dir, exist_ok=True)
        
        # 复制所有源文件到加密目录
        for item in ['core', 'ui', 'main.py', 'resources_rc.py']:
            src = item
            dst = os.path.join(encrypted_dir, item)
            if os.path.exists(src):
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        
        # 使用 pyarmor-7 加密
        subprocess.run([
            'pyarmor-7',
            'obfuscate',
            '--recursive',
            '--output', encrypted_dir,
            os.path.join(encrypted_dir, 'main.py')
        ], check=True)
        
        # 复制其他必要文件
        for item in ['data', 'bot.ico']:
            src = item
            dst = os.path.join(encrypted_dir, item)
            if os.path.exists(src):
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        
        print("加密完成")
        return True
    except Exception as e:
        print(f"加密失败: {e}")
        return False

def create_executable():
    """使用PyInstaller创建可执行文件"""
    print("正在创建可执行文件...")
    try:
        # 获取 Python DLL 的实际路径
        python_dll = os.path.join(os.path.dirname(sys.executable), 'python310.dll')
        if not os.path.exists(python_dll):
            python_dll = os.path.join(sys.base_prefix, 'python310.dll')
        
        if not os.path.exists(python_dll):
            raise FileNotFoundError("找不到 python310.dll")
            
        print(f"找到 Python DLL: {python_dll}")
        
        # 复制 DLL 到当前目录
        shutil.copy2(python_dll, 'python310.dll')
        
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# 收集所有必要的依赖
wxauto_datas, wxauto_binaries, wxauto_hiddenimports = collect_all('wxauto')
pyside_datas, pyside_binaries, pyside_hiddenimports = collect_all('PySide6')

a = Analysis(
    ['main.py'],
    pathex=[{repr(os.path.dirname(sys.executable))}],  # 添加 Python 路径
    binaries=[
        ('python310.dll', '.'),  # 直接使用复制的 DLL
        *wxauto_binaries,
        *pyside_binaries,
    ],
    datas=[
        ('core', 'core'),
        ('ui', 'ui'),
        ('data', 'data'),
        ('bot.ico', '.'),
        ('resources_rc.py', '.'),
        *wxauto_datas,
        *pyside_datas
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'win32com.client',
        'pythoncom',
        'wxauto',
        'resources_rc',
        *wxauto_hiddenimports,
        *pyside_hiddenimports
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # 改为单文件模式
    a.zipfiles,
    a.datas,
    [],
    name='WeChatAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,  # 重要：使用临时目录
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='bot.ico'
)
'''
        
        # 创建运行时钩子
        with open('runtime_hook.py', 'w', encoding='utf-8') as f:
            f.write('''
import os
import sys
import ctypes

def load_python_dll():
    try:
        if hasattr(sys, '_MEIPASS'):
            dll_path = os.path.join(sys._MEIPASS, 'python310.dll')
            if os.path.exists(dll_path):
                ctypes.CDLL(dll_path)
                return True
        return False
    except:
        return False

# 加载 Python DLL
load_python_dll()

# 设置环境变量
if hasattr(sys, '_MEIPASS'):
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ['PATH']
''')

        # 写入spec文件
        with open('WeChatAI.spec', 'w', encoding='utf-8') as f:
            f.write(spec_content)

        # 使用spec文件构建
        subprocess.run([
            'pyinstaller',
            '--clean',
            'WeChatAI.spec'
        ], check=True)
        
        print("可执行文件创建完成")
        return True
    except Exception as e:
        print(f"创建可执行文件失败: {e}")
        return False

def cleanup():
    """清理临时文件"""
    print("正在清理临时文件...")
    try:
        items_to_clean = [
            'build',
            'WeChatAI.spec',
            '__pycache__',
            'runtime_hook.py',
            'python310.dll'  # 添加临时复制的 DLL
        ]
        
        for item in items_to_clean:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.rmtree(item)
                else:
                    os.remove(item)
                    
        # 清理所有 __pycache__ 目录
        for root, dirs, files in os.walk('.'):
            for d in dirs:
                if d == '__pycache__':
                    shutil.rmtree(os.path.join(root, d))
                    
        print("清理完成")
    except Exception as e:
        print(f"清理失败: {e}")

def main():
    try:
        # 1. 创建源代码备份
        if not create_backup():
            print("备份失败，终止构建")
            return 1
        
        # 2. 直接创建可执行文件（跳过加密）
        if not create_executable():
            print("创建可执行文件失败")
            return 1
        
        # 3. 清理临时文件
        cleanup()
        
        print("\n构建完成!")
        print("可执行文件位置: dist/WeChatAI.exe")
        return 0
        
    except Exception as e:
        print(f"构建过程出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 