import torch
from TTS.api import TTS
import logging
import os
import time

# Pygame kontrolü
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

logger = logging.getLogger(__name__)

class TextToSpeech:
    def __init__(self):
        logger.info("📢 ADAM'ın Sesi (Glow-TTS) Hazırlanıyor...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            # İndirdiğin modelin tam adı
            model_name = "tts_models/tr/common-voice/glow-tts"
            
            # Vocoder'ı da belirtelim ki ses metalik çıkmasın (İndirmiştik)
            vocoder_name = "vocoder_models/tr/common-voice/hifigan"
            
            logger.info(f"⚙️ Model Yükleniyor... (Bu kez indirme yapmayacak)")
            
            # Modeli yükle
            self.tts = TTS(model_name).to(device)
            
            logger.info("✅ Ses Sistemi Devrede.")
            
        except Exception as e:
            logger.critical(f"❌ Ses motoru hatası: {e}")
            self.tts = None

        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                logger.error(f"Pygame başlatılamadı: {e}")

    def speak(self, text):
        if not text or not self.tts:
            return

        try:
            # --- DÜZELTME BURADA ---
            # Model büyük harf sevmiyor, her şeyi küçültüyoruz.
            text_clean = text.lower()
            
            logger.info(f"🗣️ Konuşuyor: {text_clean}")
            output_file = "reply.wav"
            
            # Eski dosyayı temizle
            if os.path.exists(output_file):
                try: os.remove(output_file)
                except: pass

            # Dosyaya kaydet (Vocoder otomatik devreye girer)
            self.tts.tts_to_file(text=text_clean, file_path=output_file)
            
            # Oynat
            if PYGAME_AVAILABLE and os.path.exists(output_file):
                self.play_audio(output_file)
            else:
                # Yedek oynatıcı
                import winsound
                winsound.PlaySound(output_file, winsound.SND_FILENAME)

        except Exception as e:
            logger.error(f"Konuşma hatası: {e}")

    def play_audio(self, file_path):
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"Ses oynatma hatası: {e}")

# Test Bloğu
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = TextToSpeech()
    app.speak("Merhaba Yavuz. Ben ADAM. Ses sistemim başarıyla kuruldu.")