import os
import sys
import subprocess
import ctypes
from tkinter import messagebox

# Tesseract'ın varsayılan kurulum yolu
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def is_admin():
    """Program yönetici olarak mı çalışıyor?"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_resource_path(relative_path):
    """
    PyInstaller ile paketlendiğinde geçici klasörü (_MEIPASS) bulur.
    Normal çalışırken mevcut klasörü kullanır.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def check_and_install_tesseract():
    """Tesseract kurulu mu bakar, değilse kurucuyu başlatır."""
    
    # 1. Kontrol: Zaten kurulu mu?
    if os.path.exists(TESSERACT_PATH):
        print("✅ Tesseract OCR zaten yüklü.")
        return True

    # 2. Kurulu değilse kullanıcıya sor
    response = messagebox.askyesno(
        "Eksik Bileşen", 
        "ADAM'ın görme yetisi (OCR) için 'Tesseract' yazılımı gerekli ama bulunamadı.\n\n"
        "Otomatik kurulumu başlatmak ister misiniz?"
    )

    if response:
        # Kurulum dosyasının yolunu bul (installers/tesseract_setup.exe)
        installer_path = get_resource_path(os.path.join("installers", "tesseract_setup.exe"))
        
        if not os.path.exists(installer_path):
            messagebox.showerror("Hata", f"Kurulum dosyası bulunamadı:\n{installer_path}")
            return False

        try:
            print("🚀 Tesseract kurulumu başlatılıyor...")
            # Kurulumu çalıştır ve bitmesini bekle
            subprocess.run([installer_path], check=True)
            
            # Kurulumdan sonra tekrar kontrol et
            if os.path.exists(TESSERACT_PATH):
                messagebox.showinfo("Başarılı", "Tesseract başarıyla kuruldu! ADAM başlatılıyor...")
                return True
            else:
                messagebox.showwarning("Uyarı", "Kurulum tamamlandı gibi görünüyor ama dosya bulunamadı.\nProgram yine de açılacak.")
                return True
                
        except Exception as e:
            messagebox.showerror("Kurulum Hatası", f"Bir hata oluştu: {e}")
            return False
    else:
        # Kullanıcı kurulumu reddetti
        print("Kullanıcı Tesseract kurulumunu reddetti.")
        return False