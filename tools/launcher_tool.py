import os
import subprocess
import json
import logging

#Config dosyasının yolu
CONFIG_PATH = os.path.join("data","apps_config.json")

def launch_app(app_name: str):
    '''
    apps_confing.json dosyasındaki isme göre uygulama başlatılır
    örn app_name = "brave" -> chrome açar 
    '''

    try:
        #1.config dosyasını yükle
        if not os.path.exists(CONFIG_PATH):
            return "Hata: data/apps_config.json dosyası bulunamadı"
        
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            apps=json.load(f)

        #2. Uygulama adını normalize et (küçük harf, boşluk temizle)
        target_key = app_name.lower().strip()

        #3.Listede var mı bak
        if target_key in apps:
            exe_path = apps[target_key]

            #Uygulamayı başlat(subprocess.Popen arka planda açar, asistanı dondurmaz)
            subprocess.Popen(exe_path)
            return f"Tamam, {target_key} başlatılıyor..."
        else:
            #Benzer isim önerisi(Opsiyonel basit zeka)
            mevcutlar = ", ".join(apps.keys())
            return f"Üzgünüm, '{target_key}' yapılandırma dosyamda yok. Tanımlı olanlar: {mevcutlar}"
         
    except FileNotFoundError:
        return f"Hata: Belirtilen yolda uygulama bulunamadı ({exe_path})"
    except Exception as e:
        return f"Uygulama başlatılırken hata oluştu: {e}"
