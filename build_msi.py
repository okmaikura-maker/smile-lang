"""Smile Language - MSI インストーラー作成"""
import msilib
import msilib.schema
import msilib.sequence
import os
import sys
import uuid

# 設定
PRODUCT_NAME = "Smile Language"
VERSION = "0.3.0"
MANUFACTURER = "Smile Language Project"
DESCRIPTION = "Smile言語 - 軽くて安全で優しいプログラミング言語"
EXE_PATH = os.path.join(os.path.dirname(__file__), "dist", "smile.exe")
OUTPUT_MSI = os.path.join(os.path.dirname(__file__), "dist", "smile-0.3.0-win64.msi")
INSTALL_DIR = "SmileLang"

# UUIDs (固定してアップグレード対応)
UPGRADE_CODE = "{E7A3B5C1-4D2F-4A8E-9B1C-3F5D7E9A2B4C}"
PRODUCT_CODE = "{" + str(uuid.uuid4()).upper() + "}"
PACKAGE_CODE = "{" + str(uuid.uuid4()).upper() + "}"

if not os.path.exists(EXE_PATH):
    print(f"エラー: {EXE_PATH} が見つかりません。先に build_exe.py を実行してください。")
    sys.exit(1)

print(f"MSI作成中: {OUTPUT_MSI}")

# MSI データベース作成
if os.path.exists(OUTPUT_MSI):
    os.remove(OUTPUT_MSI)

db = msilib.init_database(
    OUTPUT_MSI,
    msilib.schema,
    PRODUCT_NAME,
    PRODUCT_CODE,
    VERSION,
    MANUFACTURER,
)

# Summary Info
si = db.GetSummaryInformation(20)
si.SetProperty(msilib.PID_TITLE, f"{PRODUCT_NAME} Installer")
si.SetProperty(msilib.PID_SUBJECT, DESCRIPTION)
si.SetProperty(msilib.PID_AUTHOR, MANUFACTURER)
si.SetProperty(msilib.PID_TEMPLATE, "Intel;1033")
si.SetProperty(msilib.PID_REVNUMBER, PACKAGE_CODE)
si.SetProperty(msilib.PID_WORDCOUNT, 2)  # compressed
si.SetProperty(msilib.PID_PAGECOUNT, 200)
si.Persist()

# Directory テーブル
msilib.add_data(db, "Directory", [
    ("TARGETDIR", None, "SourceDir"),
    ("ProgramFilesFolder", "TARGETDIR", "."),
    ("INSTALLDIR", "ProgramFilesFolder", INSTALL_DIR),
])

# Component テーブル
comp_id = "{" + str(uuid.uuid4()).upper() + "}"
msilib.add_data(db, "Component", [
    ("SmileExe", comp_id, "INSTALLDIR", 0, None, "smile.exe"),
])

# Feature テーブル
msilib.add_data(db, "Feature", [
    ("SmileFeature", None, PRODUCT_NAME, DESCRIPTION, 1, 1, "INSTALLDIR", 0),
])

# FeatureComponents テーブル
msilib.add_data(db, "FeatureComponents", [
    ("SmileFeature", "SmileExe"),
])

# File テーブル
exe_size = os.path.getsize(EXE_PATH)
msilib.add_data(db, "File", [
    ("smile.exe", "SmileExe", "smile.exe", exe_size, None, None, 512, 1),
])

# Environment テーブル (PATH に追加)
msilib.add_data(db, "Environment", [
    ("SmilePath", "=-*Path", "[INSTALLDIR]", "SmileExe"),
])

# cabファイルにexeを追加
cab = msilib.CAB("smile.cab")
cab.append(EXE_PATH, "smile.exe", "smile.exe")
cab.commit(db)

db.Commit()

print(f"完了: {OUTPUT_MSI}")
print(f"サイズ: {os.path.getsize(OUTPUT_MSI) / 1024 / 1024:.1f} MB")
print()
print("インストール:")
print(f'  msiexec /i "{OUTPUT_MSI}"')
print()
print("アンインストール:")
print(f'  msiexec /x "{OUTPUT_MSI}"')
