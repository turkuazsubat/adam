import pytesseract
from PIL import Image, ImageGrab
import os
import logging

# Tesseract Yolu (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class VisionSystem:
    def __init__(self):
        print("--- Vision (Göz) Modülü Hazır ---")

    def read_image_from_path(self, image_path):
        """Dosya yolundaki resmi okur."""
        try:
            if not os.path.exists(image_path):
                return "HATA: Dosya bulunamadı."
            img = Image.open(image_path)
            return self._ocr_process(img)
        except Exception as e:
            return f"Dosya okuma hatası: {e}"

    def read_from_clipboard(self):
        """Panoya kopyalanmış resmi (Screenshot) okur."""
        try:
            # Panodaki resmi yakala
            img = ImageGrab.grabclipboard()
            
            if img is None:
                return "Panoda resim bulunamadı. Lütfen önce ekran görüntüsü alın veya bir resim kopyalayın."
            
            print("👁️ Gözler Panodaki Resme Bakıyor...")
            return self._ocr_process(img)
            
        except Exception as e:
            return f"Pano okuma hatası: {e}"

    def _ocr_process(self, img):
        """Ortak OCR İşlemi"""
        try:
            # Türkçe ve İngilizce dene
            text = pytesseract.image_to_string(img, lang='tur+eng')
            
            if text.strip():
                print(f"✅ OCR Başarılı: {len(text)} karakter.")
                return text.strip()
            else:
                return "Resimde okunabilir bir yazı göremedim."
        except Exception as e:
            return f"OCR İşleme Hatası: {e}"