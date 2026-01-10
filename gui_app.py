import tkinter as tk
from tkinter import scrolledtext
import datetime
import logging
import sys
import threading 

# Backend Modülleri
from response import generate_response
from memory import MemoryManager
from feedback import FeedbackManager
from tool_manager import ToolManager
from logger import log_event

# --- HAFTA 14.5 (SES) ---
# Ses modüllerini dahil ediyoruz
try:
    from modules.tts import TextToSpeech
    from modules.stt import SpeechToText
    VOICE_AVAILABLE = True
except ImportError as e:
    print(f"Ses modülleri bulunamadı: {e}")
    VOICE_AVAILABLE = False
# ------------------------

# Sabitler
DB_PATH = "db/project.db"
SCHEMA_PATH = "db_schema.sql"

class ProjectXGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Proje X Asistanı (v14.5 - Voice)")
        self.root.geometry("600x750")
        
        # --- Durum Yönetimi ---
        self.is_processing = False 
        self.thinking_id = None 
        # Son konuşulanı burada tutacağız ki !kaydet diyebilelim
        self.last_interaction = {"user": None, "bot": None}

        self.tts = None
        self.stt = None
        
        self.setup_ui()
        
        # Renk ve Font Ayarları
        self.chat_display.tag_config('user', foreground="#0000FF", justify="right", rmargin=10)
        self.chat_display.tag_config('bot', foreground="#006400", justify="left", lmargin1=10, lmargin2=10)
        self.chat_display.tag_config('system', foreground="#640000", justify="center")
        self.chat_display.tag_config("info", foreground="gray", justify="center")
        self.chat_display.tag_config('thinking', foreground='orange', justify='left')

        # Backend Başlatma
        self.append_message("Sistem", "Beyin modülleri yükleniyor..", "info")
        self.root.after(100, self.init_backend)

    def setup_ui(self):
        '''Pencere elemanları (Widget) yerleştirir.'''

        # 1. Sohbet Geçmişi
        self.chat_display = scrolledtext.ScrolledText(
            self.root, state='disabled', wrap='word', font=('Arial', 11), bg="#f0f0f0"
        )
        self.chat_display.pack(expand=True, fill='both', padx=10, pady=10)

        # 2. Alt Panel (Giriş alanı ve buton için)
        bottom_frame = tk.Frame(self.root, bg="#ddd")
        bottom_frame.pack(fill="x", side="bottom")

        # --- KRİTİK SIRALAMA: Önce Butonu Yerleştir (Sağa) ---
        # Böylece Text kutusu büyüdüğünde butonu ekrandan dışarı itemez.
        self.send_button = tk.Button(
            bottom_frame,
            text="Gönder",
            command=self.send_message,
            font=("Arial", 10, "bold"),
            bg="#4CAF50",
            fg="#FFFFFF",
            width=10,
            height=2 # Buton yüksekliği
        )
        self.send_button.pack(side="right", padx=10, pady=10)

        # --- BAS-KONUŞ MİKROFON BUTONU ---
        # Not: command parametresini kaldırdık, yerine bind kullanacağız.
        self.mic_button = tk.Button(
            bottom_frame, 
            text="🎙️", 
            font=("Arial",12), 
            bg="#FF5722", 
            fg="white", 
            width=4, 
            height=2
        )
        self.mic_button.pack(side="right", padx=5, pady=10)
        
        # Olayları Bağla (Basınca ve Bırakınca)
        self.mic_button.bind('<ButtonPress-1>', self.on_mic_press)
        self.mic_button.bind('<ButtonRelease-1>', self.on_mic_release)
        # --------------------------------- 

        # 3. Metin Giriş Kutusu (Text Widget)
        # Türkçe karakter sorunu için Entry yerine Text kullanıyoruz
        self.entry_field = tk.Text(bottom_frame, height=2, font=("Arial", 12)) 
        self.entry_field.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        
        # Olay Bağlayıcılar (Bind)
        self.entry_field.bind("<Return>", self.handle_enter)
        self.entry_field.bind("<KeyRelease>", self.fix_turkish_chars_live)

    def fix_turkish_chars_live(self, event):
        """
        Kullanıcı yazarken oluşan bozuk karakterleri (ð, þ, ý) 
        anında görsel olarak (ğ, ş, ı) ile değiştirir.
        """
        if event.keysym in ["Return", "BackSpace", "Shift_L", "Shift_R"]:
            return

        current_text = self.entry_field.get("1.0", "end-1c")
        
        # Bozuk karakter kontrolü
        if any(char in current_text for char in ['ð', 'Ð', 'þ', 'Þ', 'ý', 'Ý']):
            cursor_pos = self.entry_field.index(tk.INSERT)
            
            fixed_text = (current_text
                          .replace('ð', 'ğ').replace('Ð', 'Ğ')
                          .replace('þ', 'ş').replace('Þ', 'Ş')
                          .replace('ý', 'ı').replace('Ý', 'İ'))
            
            self.entry_field.delete("1.0", "end")
            self.entry_field.insert("1.0", fixed_text)
            
            # İmleci kaldığı yere geri koy
            self.entry_field.mark_set(tk.INSERT, cursor_pos)

    def handle_enter(self, event):
        """Shift+Enter alt satıra geçer, Enter gönderir."""
        if event.state & 0x0001: 
            return None 
        self.send_message()
        return "break"

    def init_backend(self):
        '''Arka plan servislerini başlatır'''
        try:
            self.memory = MemoryManager(db_path=DB_PATH, schema_path=SCHEMA_PATH)
            self.feedback_manager = FeedbackManager(self.memory)
            self.tool_manager = ToolManager()

            self.append_message("Sistem", "Bağlantı başarılı. Asistan hazır.", "info")
            self.append_message("Asistan", "Merhaba! Size nasıl yardımcı olabilirim?", "bot")
            log_event("INFO", "GUI: Asistan başlatıldı.", "gui")

            #--Hafta 14.5 Ses--
            #Ses modüllerini ayrı bir thread'de yükle (Arayüz donmasın diye)
            if VOICE_AVAILABLE:
                threading.Thread(target=self.init_voice_modules,daemon=True).start()
        
        except Exception as e:
            self.append_message("Sistem", f"KRİTİK HATA: {e}", "system")
            log_event("CRITICAL", f"GUI Başlatma Hatası: {e}", "gui")


    # --- HAFTA 14.5: GÜNCELLENEN BAS-KONUŞ FONKSİYONLARI ---
    # Eski start_listening_thread yerine bu yeni yapı geldi:

    def init_voice_modules(self):
        '''Ses motorlarını arka planda başlatır.'''
        try:
            self.append_message("Sistem","Ses modülleri yükleniyor","info")
            self.tts = TextToSpeech()
            self.stt = SpeechToText()
            self.append_message("Sistem","Ses sistemi aktif. (Basılı tutarak konuşun)","info")
        except Exception as e:
            self.append_message("Sistem",f"Ses hatası: {e}","system")

    def on_mic_press(self, event):
        """Butona basılınca: Kaydı Başlat"""
        if not self.stt or self.is_processing: return
        
        # Görsel Geri Bildirim
        self.mic_button.config(bg="red", text="🔴") # Kayıt işareti
        self.entry_field.delete("1.0", "end")
        
        # Kaydı başlat (stt.py içindeki fonksiyon)
        try:
            self.stt.start_recording()
        except Exception as e:
            print(f"Kayıt başlatma hatası: {e}")

    def on_mic_release(self, event):
        """Butonu bırakınca: Kaydı Bitir ve İşle"""
        if not self.stt or self.is_processing: return
        
        # Görsel Değişim
        self.mic_button.config(bg="orange", text="⏳") # Bekle işareti
        
        # İşlemi Thread'e at (Arayüz donmasın)
        threading.Thread(target=self.process_voice_thread, daemon=True).start()

    def process_voice_thread(self):
        """Sesi yazıya çevirir ve sisteme gönderir"""
        try:
            # Kaydı durdur ve transkripte çevir
            text = self.stt.stop_and_transcribe()
            
            # GUI'yi güncelle
            self.root.after(0, lambda: self.finish_voice_process(text))
        except Exception as e:
            print(f"Ses işleme hatası: {e}")
            self.root.after(0, lambda: self.finish_voice_process(None))

    def finish_voice_process(self, text):
        """Sonucu ekrana basar"""
        # Butonu normale çevir
        self.mic_button.config(bg="#FF5722", text="🎙️")
        
        if text:
            # Metni kutuya yaz ve gönder fonksiyonunu tetikle
            self.entry_field.insert("1.0", text)
            self.send_message() # Otomatik gönder
        else:
            self.append_message("Sistem", "Ses algılanamadı veya çok kısaydı.", "info")

    def manual_speak(self, text):
        """YENİ: Mavi linke tıklanınca metni okur."""
        if self.tts:
            threading.Thread(target=self.tts.speak, args=(text,), daemon=True).start()
    # -------------------------------------------------------

    def send_message(self, event=None):
        '''Kullanıcı mesajını alır, temizler ve işler.'''
        # Text widget'ından metni al
        user_input = self.entry_field.get("1.0", "end-1c").strip() 

        # Göndermeden önce son bir karakter temizliği
        user_input = (user_input
                      .replace('ð', 'ğ').replace('Ð', 'Ğ')
                      .replace('þ', 'ş').replace('Þ', 'Ş')
                      .replace('ý', 'ı').replace('Ý', 'İ'))

        if not user_input or self.is_processing:
            return "break"
        
        # Çıkış Kontrolü
        if user_input.lower() in ["çık", "exit", "quit"]:
            self.append_message("Sistem", "Kapatılıyor...", 'system')
            self.memory.close() 
            self.root.destroy() 
            return "break"
        
        # 1. Arayüzü Güncelle
        self.append_message("Siz", user_input, 'user')
        self.entry_field.delete("1.0", "end")

        # 2. Kilitle
        self.is_processing = True
        self.entry_field.config(state="disabled") 
        self.send_button.config(state="disabled")
        # --- HAFTA 14.5 (SES) ---
        self.mic_button.config(state="disabled")
        # ------------------------

        # 3. Bekleme Mesajı
        self.thinking_id = self.append_message("Asistan", "Yazıyor...", 'thinking', is_temp=True)

        # 4. Thread Başlat
        thread = threading.Thread(target=self.process_input_thread, args=(user_input,))
        thread.start()

        return "break"

    def process_input_thread(self, user_input):
        '''Arka plan mantığı.'''
        try:
            response = ""
            
            # --- DURUM 1: KOMUTLAR (!kaydet vb.) ---
            if user_input.startswith("!"):
                command = user_input.lower().strip()
                
                if command == "!kaydet":
                    # Hafızada bir önceki konuşma var mı?
                    if self.last_interaction["user"] and self.last_interaction["bot"]:
                        # Yeni memory.py yapısına uygun çağrı (2 parametre)
                        success = self.memory.promote_to_memory(
                            self.last_interaction["user"], 
                            self.last_interaction["bot"]
                        )
                        if success:
                            response = "Son konuşma kalıcı hafızaya kaydedildi ✅"
                        else:
                            response = "Kaydetme sırasında bir veritabanı hatası oluştu."
                    else:
                        response = "Hafızada kaydedilecek önceki bir konuşma bulunamadı." 
                else:
                    response = self.feedback_manager.handle_command(user_input)

            # --- DURUM 2: NORMAL SOHBET / ARAÇLAR ---
            else:
                response = generate_response(user_input, self.memory, self.tool_manager)
                
                # Kısa süreli hafızayı güncelle
                # (Hata mesajlarını ve Araç çıktılarını 'öğrenilecek bilgi' olarak kaydetme)
                if not response.startswith("Beklenmedik hata:") and "görev eklendi" not in response.lower() and "notunuz" not in response.lower():
                    self.last_interaction = {
                        "user": user_input,
                        "bot": response
                    }

        except Exception as e:
            response = f"Beklenmedik hata: {e}"
            log_event("ERROR", f"THREAD İşlem Hatası: {e}", "gui")

        # Sonucu Ana Thread'e gönder
        self.root.after(0, self.update_ui_with_response, user_input, response)

    def update_ui_with_response(self, user_input, response):
        '''Ana thread'de cevabı gösterir.'''
        if self.thinking_id:
            self.delete_message(self.thinking_id)

        tag = 'system' if response.startswith("Beklenmedik hata:") else "bot"
        self.append_message("Asistan", response, tag)

        # --- DEĞİŞİKLİK: Otomatik okumayı kaldırdık ---
        # Artık aşağıda çıkan mavi linke tıklayınca okuyacak.
        # if self.tts and not response.startswith("Beklenmedik hata:"):
        #     threading.Thread(target=self.tts.speak, args=(response,), daemon=True).start()
        # ----------------------------------------------

        self.is_processing = False
        self.entry_field.config(state="normal")
        self.send_button.config(state="normal")
        self.mic_button.config(state="normal") 
        self.entry_field.focus_set()

    def append_message(self, sender, message, tag, is_temp=False):
        self.chat_display.configure(state="normal") 
        timestamp = datetime.datetime.now().strftime("%H:%M")
        header = f"{sender} [{timestamp}]:\n"

        start_index = self.chat_display.index("end-1c")
        self.chat_display.insert("end", header, tag)
        self.chat_display.insert("end", str(message) + "\n", tag)
        
        # --- İSTEĞE BAĞLI OKUMA BUTONU (Sadece Asistan İçin) ---
        if sender == "Asistan" and not is_temp and self.tts:
            # Küçük, mavi, link görünümlü bir etiket oluştur
            lbl = tk.Label(
                self.chat_display, 
                text="🔊 Seslendir", 
                font=("Arial", 9, "underline"), 
                fg="blue", 
                bg="#f0f0f0", 
                cursor="hand2"
            )
            # Bu etikete tıklandığında, o anki mesajı okumasını söyle
            lbl.bind("<Button-1>", lambda e, m=message: self.manual_speak(m))
            
            # Etiketi metin kutusunun içine (sonuna) göm
            self.chat_display.window_create("end", window=lbl)
            self.chat_display.insert("end", "\n\n") # Biraz boşluk bırak
        else:
             self.chat_display.insert("end", "\n\n", tag)
        # -------------------------------------------------------
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

        if is_temp:
            # Geçici mesajın silinmesi için başlangıç ve bitiş indexlerini döndür
            # (start_index zaten string formatında gelir: "line.char")
            return start_index, self.chat_display.index("end-1c")
        
    def delete_message(self, indices):
        self.chat_display.configure(state="normal")
        self.chat_display.delete(indices[0], indices[1])
        self.chat_display.configure(state="disabled")

if __name__ == "__main__":
    # Loglama kısmını terminalde görebilmen için düzelttim:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    root = tk.Tk()
    try:
        # Windows Türkçe encoding zorlaması
        root.tk.call('encoding', 'system', 'utf-8')
    except:
        pass

    app = ProjectXGUI(root)
    root.mainloop()