import tkinter as tk
from tkinter import scrolledtext
import datetime
import logging
import sys

#---Backend Modülleri (Beyin)---
from response import generate_response
from memory import MemoryManager
from feedback import FeedbackManager
from tool_manager import ToolManager
from logger import log_event

#Sabitler
DB_PATH = "db/project.db"
SCHEMA_PATH = "db_schema.sql"

class ProjectXGUI:
    def __init__(self,root):
        self.root = root
        self.root.title("Proje X Asistanı (GUI v1)")
        self.root.geometry("600x700") #Pencere boyutu

        #--- Arayüz Kurulumu---
        self.setup_ui()
        
        #---Renk ve Still Ayarları(Tag Config)---
        #Kullanıcı mesajları: Mavi, Sağa yaslı
        self.chat_display.tag_config('user', foreground="#0000FF",justify="right",rmargin=10)
        #asistan mesajları: Yeşil (veya Siyah), Sola yaslı
        self.chat_display.tag_config('bot', foreground="#006400",justify="left",lmargin1=10,lmargin2=10)
        #Sistem/Hata mesajları: Kırmızı, Ortada
        self.chat_display.tag_config('system', foreground="#640000",justify="center")
        #Bilgi mesajları
        self.chat_display.tag_config("info",foreground="gray",justify="center")        

        # --- Backend Başlatma ----
        self.append_message("Sistem", "Beyin modülleri yükleniyor..","info")
        #Arayüz donmasın diye 100ms sonra başlat
        self.root.after(100,self.init_backend)

    def setup_ui(self):
        '''Pencere elemanları (Widget) yerleştirir.'''

        #1. Sohbet Geçmişi (ScrolledText)
        #state = 'disabled' kullanıcısının elle buraya yazı yazmasını engeller ( sadece kodla yazılır)
        self.chat_display = scrolledtext.ScrolledText(
            self.root,
            state='disabled',
            wrap='word',
            font=('Arial',11),
            bg="#f0f0f0"
        )
        self.chat_display.pack(expand=True, fill='both', padx=10, pady=10)

        #2. Alt Panel (Girdi Alanı ve buton için kapsayıcı)
        bottom_frame = tk.Frame(self.root, bg="#ddd")
        bottom_frame.pack(fill="x", side="bottom")

        #3.Metin Giriş Kutusu (Entry)
        self.entry_field = tk.Entry(bottom_frame, font=("Arial",12))
        self.entry_field.pack(side="left",fill="x",expand=True,padx=10,pady=10)
        self.entry_field.bind("<Return>", self.send_message)

        #4.Gönder Butonu

        send_button = tk.Button(
            bottom_frame,
            text="Gönder",
            command=self.send_message,
            font=("Arial",10,"bold"),
            bg="#4CAF50",
            fg="#FFFFFF",
            width=10
        )
        send_button.pack(side="right",padx=10,pady=10)

    def init_backend(self):
        '''Arka plan servislerini başlatır'''

        try:
            self.memory = MemoryManager(db_path=DB_PATH, schema_path=SCHEMA_PATH)
            self.feedback_manager = FeedbackManager(self.memory)
            self.tool_manager = ToolManager()

            self.append_message("Sistem", "Bağlantı başarılı. Asistan hazır.","info")
            self.append_message("Asistan","Merhaba! Size nasıl yardımcı olabilirim?","bot")
            log_event("INFO","GUI: Asistan başlatıldı.","gui")
        
        except Exception as e:
            self.append_message("Sistem",f"KRİTİK HATA: {e}","systej")
            log_event("CRITICAL",f"GUI Başlatma Hatası: {e}","gui")


    def send_message(self, event=None):
        '''Kullanıcı "Gönder" e bastığında veya Enter'a tıkladığında çalışır'''
        user_input = self.entry_field.get().strip()

        if not user_input:
            return
        
        # 1. Kullanıcı mesajını yaz
        self.append_message("Siz", user_input, 'user')
        self.entry_field.delete(0, 'end')

        # 2. Backend'e gönder (Process Input)
        # Arayüzün donmasını engellemek için 'after' kullanabiliriz ama şimdilik direkt çağırıyoruz.
        self.process_input(user_input)

    def process_input(self,user_input):
        '''Girdiyi analiz eder ve cevabı üretir (main.py mantığı)'''
        try:
            response = ""
       
            # A) Çıkış Komutu
            if user_input.lower() in ["çık", "exit", "quit"]:
                response = "Görüşmek üzere! (Pencereyi kapatabilirsiniz)"
                self.memory.close()
                # İsterseniz self.root.destroy() ile pencereyi de kapatabilirsiniz
            
            # B) Geri Bildirim (!Komut)
            elif user_input.startswith("!"):
                response = self.feedback_manager.handle_command(user_input)
                
            # C) Normal Akış (Sorgu veya Komut)
            else:
                response = generate_response(user_input, self.memory, self.tool_manager)

            # Cevabı ekrana yaz
            self.append_message("Asistan", response, 'bot')
            
            # Logla
            log_event("INFO", f"GUI: {user_input} | {response}", "gui")

        except Exception as e:
            error_msg = f"Beklenmedik hata: {e}"
            self.append_message("Sistem", error_msg, 'system')
            log_event("ERROR", f"GUI İşlem Hatası: {e}", "gui")

    def append_message(self, sender, message,tag):
        '''Sohbet Ekranına formatlı mesaj ekler'''
        self.chat_display.configure(state="normal") #Yazma kilidini aç

        timestamp = datetime.datetime.now().strftime("%H:%M")
        header = f"{sender} [{timestamp}]:\n"

        #Başlığı ve mesajı ekle
        self.chat_display.insert("end", header, tag)
        self.chat_display.insert("end", message + "\n\n",tag)

        self.chat_display.configure(state="disabled") #Tekrar kilitle(salt okunur yap)
        self.chat_display.see("end") #En aşağıya (son mesaja) kaydır


if __name__ == "__main__":
    #Loglama Ayarları (Dosyayı Yaz)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        filename='project.log',
        filemode='a'
    )

    #Tkinter ana döngüsünü başlat
    root = tk.Tk()
    app = ProjectXGUI(root)
    root.mainloop()         

