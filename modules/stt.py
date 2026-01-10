import pyaudio
import wave
import whisper
import torch
import os
import threading
import logging

# Loglama
logger = logging.getLogger(__name__)

class SpeechToText:
    def __init__(self, model_size="base"):
        print("--- STT (Bas-Konuş) BAŞLATILIYOR ---", flush=True)
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"⚙️ Çalışma Ortamı: {self.device.upper()}", flush=True)

        try:
            print(f"📥 Whisper '{model_size}' modeli yükleniyor...", flush=True)
            self.model = whisper.load_model(model_size, device=self.device)
            print("✅ Model Hazır.", flush=True)
        except Exception as e:
            print(f"❌ Model Hatası: {e}", flush=True)
            self.model = None

        # Kayıt Ayarları
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.is_recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()

    def start_recording(self):
        """Kaydı başlatır (Butona basınca)"""
        if self.is_recording: return
        
        self.is_recording = True
        self.frames = []
        print("🎙️ KAYIT BAŞLADI (Basılı tutuluyor)...", flush=True)
        
        # Kaydı ayrı bir thread'de yap ki arayüz donmasın
        self.stream = self.audio.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      input=True,
                                      frames_per_buffer=self.CHUNK)
        
        threading.Thread(target=self._record_loop, daemon=True).start()

    def _record_loop(self):
        """Arka planda ses verilerini depolar"""
        while self.is_recording:
            try:
                data = self.stream.read(self.CHUNK)
                self.frames.append(data)
            except Exception as e:
                print(f"Kayıt döngüsü hatası: {e}", flush=True)
                break

    def stop_and_transcribe(self):
        """Kaydı bitirir ve yazıya döker (Butonu bırakınca)"""
        print("🛑 KAYIT BİTTİ. İşleniyor...", flush=True)
        self.is_recording = False
        
        # Stream'i kapat
        try:
            self.stream.stop_stream()
            self.stream.close()
        except:
            pass

        # Ses dosyası oluştur
        temp_filename = "temp_voice.wav"
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        # Whisper'a gönder
        if self.model:
            print("🧠 Whisper düşünüyor...", flush=True)
            result = self.model.transcribe(temp_filename, fp16=False, language='tr')
            text = result["text"].strip()
            
            # Dosyayı temizle
            try: os.remove(temp_filename)
            except: pass
            
            print(f"✅ SONUÇ: {text}", flush=True)
            return text
        else:
            return None