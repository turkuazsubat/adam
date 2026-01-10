import sys
import os
import importlib

print("🔍 DERİN ANALİZ BAŞLATILIYOR...")
print("Lütfen bekleyin, sistemdeki tüm gizli ajanlar taranıyor...")

# 1. Proje ana dizinini yola ekle
sys.path.append(os.getcwd())

# 2. Kritik kütüphaneleri manuel tetikle (GUI açmadan import et)
# Bu işlem, o kütüphanelerin altındaki gizli importları (jamo vb.) tetikler.
try:
    import gui_app # Ana dosya
    import TTS.api # Ses motoru
    import spacy # NLP
    import torch # Yapay zeka
    
    # TTS'in dil bağımlılıklarını zorla yükle
    try: import jamo; print("   -> Yakalandı: jamo")
    except: pass
    try: import jieba; print("   -> Yakalandı: jieba")
    except: pass
    try: import pypinyin; print("   -> Yakalandı: pypinyin")
    except: pass
    try: import gruut; print("   -> Yakalandı: gruut")
    except: pass
    
except Exception as e:
    # Hata vermesi önemli değil, amaç sys.modules'i doldurmak
    pass

# 3. Hafızadaki (sys.modules) HER ŞEYİ listele
# Sadece yüklü olan ve harici olan kütüphaneleri alır.
std_libs = list(sys.builtin_module_names)
detected_modules = []

for name, module in sys.modules.items():
    if not module: continue
    if hasattr(module, '__file__') and module.__file__:
        # Site-packages (harici kütüphane) içindeyse listeye al
        if "site-packages" in module.__file__:
            root_package = name.split('.')[0]
            if root_package not in detected_modules:
                detected_modules.append(root_package)

print("-" * 50)
print(f"✅ TOPLAM {len(detected_modules)} ADET BAĞIMLILIK TESPİT EDİLDİ.")
print("BUNLAR SİSTEMİN GERÇEK BAĞIMLILIKLARIDIR:")
print(detected_modules)
print("-" * 50)

# Bu listeyi build.py için formatla
print("\n[BUILD.PY İÇİN HAZIR LİSTE]")
print("target_libs = [")
for lib in sorted(detected_modules):
    print(f"    '{lib}',")
print("]")