import PyInstaller.__main__
from PyInstaller.utils.hooks import collect_all
import os
import shutil
import sys

APP_NAME = "ADAM_v1.0"
MAIN_FILE = "gui_app.py"

print(f"🔥 ADAM FİNAL BUILD - TESPİT EDİLEN 100+ KÜTÜPHANE PAKETLENİYOR...")

# --- SENİN ANALİZ RPORUNDAN GELEN GERÇEK LİSTE ---
# Bu liste, sistemin çalışırken RAM'e yüklediği kütüphanelerdir.
target_libs = [
    # KRİTİK OLANLAR (Daha önceki hataların kaynağı)
    'jamo', 'jieba', 'pypinyin', 'gruut', 'gruut_ipa', 
    'TTS', 'trainer', 'spacy', 'torch', 'torchaudio', 'whisper',
    'en_core_web_sm', # Spacy Modeli
    
    # DİĞER TESPİT EDİLENLER
    'Cython', 'PIL', 'PyPDF2', 'apscheduler', 'audioread', 'babel',
    'bangla', 'blis', 'bnnumerizer', 'bnunicodenormalizer', 'catalogue',
    'certifi', 'cffi', 'charset_normalizer', 'click', 'colorama', 'confection',
    'coqpit', 'customtkinter', 'cycler', 'cymem', 'cython', 'darkdetect',
    'dateparser', 'dateutil', 'decorator', 'filelock',
    'fsspec', 'google', 'huggingface_hub', 'idna',
    'inflect', 'jinja2', 'joblib', 'jsonlines', 'kiwisolver',
    'langcodes', 'lazy_loader', 'librosa', 'llvmlite', 'markupsafe',
    'matplotlib', 'more_itertools', 'mpl_toolkits', 'msgpack', 'murmurhash',
    'networkx', 'num2words', 'numba', 'numpy', 'packaging', 'pandas',
    'pkg_resources', 'platformdirs', 'pooch', 'preshed', 'psutil', 'pyaudio',
    'pycparser', 'pycrfsuite', 'pydantic', 'pydantic_core', 'pygame',
    'pyparsing', 'pyperclip', 'pysbd', 'pytesseract', 'pythoncom',
    'pytz', 'regex', 'requests', 'safetensors', 'scipy', 'sentence_transformers',
    'sentencepiece', 'six', 'sklearn', 'soundfile', 'soxr',
    'spacy_alignments', 'spacy_transformers', 'srsly', 'thinc',
    'threadpoolctl', 'tiktoken', 'tokenizers', 'torchgen', 'tqdm', 
    'transformers', 'typeguard', 'typer', 'typing_extensions', 
    'tzlocal', 'urllib3', 'wasabi', 'weasel', 'wrapt', 'yaml'
]

collected_args = []

print(f"📦 Hedeflenen {len(target_libs)} kütüphane için 'collect_all' çalıştırılıyor...")

for lib in target_libs:
    try:
        # Kütüphanenin tüm veri, binary ve config dosyalarını al
        datas, binaries, hiddenimports = collect_all(lib)
        
        for source, dest in datas:
            collected_args.append(f'--add-data={source};{dest}')
            
        for hi in hiddenimports:
            collected_args.append(f'--hidden-import={hi}')
            
    except Exception as e:
        # Bazı sistem kütüphaneleri (win32 vb) collect_all ile hata verebilir, onları geçiyoruz.
        # Ama jamo, gruut gibi asıl hedefler hata vermez.
        pass

# --- MANUEL DOSYALAR ---
manual_datas = [
    'db/project.db;db',
    'db_schema.sql;.',
    'installers/tesseract_setup.exe;installers',
    'data;data',
    'audio.wav;.', 'reply.wav;.', 'test.wav;.'
]

for item in manual_datas:
    if os.path.exists(item.split(';')[0]):
        collected_args.append(f'--add-data={item}')

# --- TEMİZLİK ---
if os.path.exists("dist"): shutil.rmtree("dist")
if os.path.exists("build"): shutil.rmtree("build")

# --- KOMUT ---
pyinstaller_args = [
    MAIN_FILE,
    f'--name={APP_NAME}',
    '--onedir',           # Klasör Modu (Hızlı)
    '--noconsole',
    '--clean',
    '--contents-directory=internal',
    
    # Spacy ve Torch için ekstra garantiler
    '--hidden-import=spacy.lang.en',
    '--hidden-import=spacy.lang.tr',
    '--hidden-import=en_core_web_sm',
    
    # GUI APP içindeki yamayı (JIT disable) çalıştırması için:
    '--runtime-hook=gui_app.py', 
    
] + collected_args

print("🔨 Derleme başlatılıyor (Bu işlem 3-5 dakika sürebilir)...")

PyInstaller.__main__.run(pyinstaller_args)

print("\n✅ İŞLEM TAMAMLANDI!")
print(f"📂 Çıktı: dist\\{APP_NAME}")