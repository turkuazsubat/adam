import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_all
import os

# --- AYARLAR ---
APP_NAME = "ADAM_v1.0"
MAIN_FILE = "gui_app.py"

print("🚀 ADAM Paketleme İşlemi Başlıyor (Tam Kapsamlı Mod)...")

# --- 1. OTOMATİK TOPLAYICI (COLLECT ALL) ---
# Sorun çıkaran kütüphanelerin 'HER ŞEYİNİ' topluyoruz.
# Artık "VERSION eksik", "config eksik" hatası almayacaksın.

target_libs = ['TTS', 'trainer', 'customtkinter', 'babel', 'speech_recognition']
collected_args = []

for lib in target_libs:
    try:
        print(f"📦 {lib} kütüphanesi toplanıyor...")
        datas, binaries, hiddenimports = collect_all(lib)
        
        # Veri dosyalarını ekle (--add-data)
        for source, dest in datas:
            collected_args.append(f'--add-data={source};{dest}')
            
        # Gizli importları ekle (--hidden-import)
        for hi in hiddenimports:
            collected_args.append(f'--hidden-import={hi}')
            
    except Exception as e:
        print(f"⚠️ {lib} toplanırken uyarı: {e}")

# --- 2. MANUEL DOSYALAR ---
# Kendi proje dosyalarımızı ekliyoruz
manual_datas = [
    'db/project.db;db',
    'db_schema.sql;.',
    'installers/tesseract_setup.exe;installers'
]

for item in manual_datas:
    collected_args.append(f'--add-data={item}')

# --- 3. KOMUTU OLUŞTUR VE ÇALIŞTIR ---
pyinstaller_args = [
    MAIN_FILE,
    f'--name={APP_NAME}',
    '--onefile',
    '--noconsole',
    '--clean',
    '--hidden-import=sqlite3',
    '--hidden-import=PIL',
    '--hidden-import=pytesseract',
] + collected_args # Otomatik toplananları ekle

print("🔨 Paketleme başlatılıyor (Bu işlem biraz sürebilir)...")

PyInstaller.__main__.run(pyinstaller_args)

print("\n✅ İŞLEM TAMAMLANDI!")
print(f"📂 EXE dosyanız 'dist' klasöründe: {APP_NAME}.exe")