import tkinter as tk
from tkinter import scrolledtext
import datetime
import logging
import sys
import threading #W8
import locale #GUI UTF*8 Sorunu 

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
        self.root.title("Proje X Asistanı (GUI v2 - Threading)")
        self.root.geometry("600x700") #Pencere boyutu

        #---Durum takibi---
        self.is_processing = False #İşlem sürüyor mu?
        self.thinkind_id = None #"Düşünüyor..." mesajının ID'si
        self.memor = None # Thread id çakışması için buraya taşıdım

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

        self.send_button = tk.Button(
            bottom_frame,
            text="Gönder",
            command=self.send_message,
            font=("Arial",10,"bold"),
            bg="#4CAF50",
            fg="#FFFFFF",
            width=10
        )
        self.send_button.pack(side="right",padx=10,pady=10)

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

        # --- KRİTİK KLAVYE DÜZELTMESİ (Input Translation) ---
        # Tcl/Tk'nın bozduğu karakterleri (özellikle 'ı' karakterini) düzeltiyoruz.
        user_input = user_input.replace('ý', 'ı').replace('Ý', 'İ') # <<< YENİ: I, ı karakter düzeltmesi
        # ----------------------------------------------------

        if not user_input or self.is_processing:
            return "break" #Tuş basımını engelle
        
        # --- KRİTİK DÜZELTME 1: Çıkış Komutunu Ana Thread'de Yakala ---
        if user_input.lower() in ["çık", "exit", "quit"]:
            self.append_message("Sistem", "Kapatılıyor...", 'system')
            self.memory.close() 
            self.root.destroy() # Pencereyi kapat
            return "break"
        
        # 1. Kullanıcı mesajını yaz
        self.append_message("Siz", user_input, 'user')
        self.entry_field.delete(0, 'end')

        # 2. Buton ve kutuyu devre dışı bırak
        self.is_processing = True
        self.entry_field.configure(state="disabled")
        self.send_button.configure(state="disabled")

        # 3. "Düşünüyor" mesajını yaz
        self.thinkind_id = self.append_message("Asistan","Yazıyor...",'thinking',is_temp=True)

        # 4. İşlemeyi arka plana gönder 
        thread = threading.Thread(target=self.process_input_thread,args=(user_input,))
        thread.start()

        return "break"
    def process_input_thread(self, user_input):
        '''
        Arka plan thread'inde çalışan, bloke edici mantık.
        '''
        try:
            response = ""

            # A) Çıkış Komutu
            '''
            if user_input.lower() in ["çık","exit","quit"]:
                response = "Görüşmek üzere! (Pencereyi Kapatabilirsiniz)"
                self.memory.close()
            '''
            #NOT:Çıkış Komutu kontrolü buradan deaktif edildi.

            # B) Geri Bildirim (!Komut)
            if user_input.startswith("!"):
                response = self.feedback_manager.handle_command(user_input)

            # C) Normal Akış (Sorgu veya Komut)
            else:
                response = generate_response(user_input, self.memory, self.tool_manager)

        except Exception as e:
            response = f"Beklenmedik hata: {e}"
            log_event("ERROR",f"THREAD İşlem Hatası: {e}", "gui")

        #İşlem bitti: Cevabı ana thread'e göndermemiz gerekiyor(root.after ile)
        self.root.after(0,self.update_ui_with_response, user_input,response)

    def update_ui_with_response(self, user_input,response):
        '''Ana thread'de cevabı gösterir ve arayüzü sıfırlar.'''

        #1. Düşünüyor mesajını sil
        if self.thinkind_id:
            self.delete_message(self.thinkind_id)

        #2. Cevabı ekrana yaz
        tag = 'system' if user_input.lower() in ["çık","exit","quit"] or response.startswith("Beklenmedik hata:") else "bot"
        self.append_message("Asistan", response, tag)

        #3. Arayüzü sıfırla
        self.is_processing = False
        self.entry_field.configure(state="normal")
        self.send_button.configure(state="normal")
        self.entry_field.focus_set() # imleci giriş kutusuna geri getir (Auto focus)


    def append_message(self, sender, message,tag,is_temp = False):
        '''Sohbet Ekranına formatlı mesaj ekler'''
        self.chat_display.configure(state="normal") #Yazma kilidini aç

        timestamp = datetime.datetime.now().strftime("%H:%M")
        header = f"{sender} [{timestamp}]:\n"

        start_index = self.chat_display.index("end-1c") #Mesajın başlangıcını bul


        #Başlığı ve mesajı ekle
        self.chat_display.insert("end", header, tag)
        self.chat_display.insert("end", message + "\n\n",tag)

        end_index = self.chat_display.index("end-1c") #Mesajın sonunu bul

        self.chat_display.configure(state="disabled") #Tekrar kilitle(salt okunur yap)
        self.chat_display.see("end") #En aşağıya (son mesaja) kaydır

        #Eğer gecici mesajsa (thinking), silmek için ID'sini döndür
        if is_temp:
            #Tkinter'da mesajı silmek için Text widget'ının indexleri döndürülür
            return start_index, end_index
        
    def delete_message(self, indices):
        '''Geçici "düşünüyor" mesajını siler '''
        self.chat_display.configure(state="normal")
        self.chat_display.delete(indices[0],indices[1])
        self.chat_display.configure(state='disabled')

        

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
    #Türkçe klavye(LOCALE) Ayarı
    # --- KRİTİK VE GARANTİLİ Tcl/Tk ZORLAMASI ---
    try:
        # Tcl/Tk ana interpreter'ın varsayılan encoding'ini UTF-8'e ayarlar.
        root.tk.call('encoding', 'system', 'utf-8') 
    except Exception as e:
        log_event("WARNING", f"Tcl/Tk encoding ayarlanamadı: {e}", "gui")
        pass



    
    app = ProjectXGUI(root)
    root.mainloop()         

