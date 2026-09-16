"""Smile Language - exe ビルドスクリプト"""
import PyInstaller.__main__
import os

here = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    os.path.join(here, "smile", "__main__.py"),
    "--name=smile",
    "--onefile",
    "--console",
    f"--add-data={os.path.join(here, 'smile', 'grammar.lark')};smile",
    f"--add-data={os.path.join(here, 'smile', 'logo.svg')};smile",
    "--hidden-import=smile.compiler",
    "--hidden-import=smile.errors",
    "--hidden-import=smile.stdlib",
    "--hidden-import=smile.pypi_fetch",
    "--hidden-import=smile.lowlevel",
    "--hidden-import=smile.debugger",
    "--hidden-import=smile.lsp",
    "--hidden-import=smile.web",
    "--hidden-import=smile.gpu",
    "--hidden-import=smile.ffi",
    "--hidden-import=smile.compute",
    "--hidden-import=smile.gui",
    "--hidden-import=lark",
    "--exclude-module=bitsandbytes",
    "--exclude-module=torch",
    "--exclude-module=tensorflow",
    "--exclude-module=transformers",
    "--exclude-module=numpy",
    "--exclude-module=pandas",
    "--exclude-module=scipy",
    "--exclude-module=matplotlib",
    "--exclude-module=PIL",
    "--exclude-module=cv2",
    "--exclude-module=sklearn",
    f"--distpath={os.path.join(here, 'dist')}",
    f"--workpath={os.path.join(here, 'build')}",
    f"--specpath={here}",
    "--clean",
])
