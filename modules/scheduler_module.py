from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging

class TimeMaster:
    def __init__(self, callback_function):
        """
        callback_function: Zamanı gelince çalıştırılacak fonksiyon (GUI'ye mesaj atacak)
        """
        print("--- Zamanlayıcı (Scheduler) Başlatıldı ---")
        self.scheduler = BackgroundScheduler()
        self.callback = callback_function
        self.scheduler.start()

    def set_reminder(self, message, seconds):
        """X saniye sonra bir hatırlatma kurar."""
        run_time = datetime.now() + timedelta(seconds=seconds)
        
        # Görevi ekle
        self.scheduler.add_job(
            func=self.trigger_alarm, 
            trigger='date', 
            run_date=run_time, 
            args=[message],
            id=f"reminder_{datetime.now().timestamp()}"
        )
        print(f"⏰ Alarm Kuruldu: {seconds} saniye sonra -> '{message}'")
        return f"Tamam, {seconds} saniye sonra hatırlatacağım: {message}"

    def trigger_alarm(self, message):
        """Zamanı gelince bu çalışır"""
        print(f"🔔 DİNG DONG! Zamanı geldi: {message}")
        
        # GUI'deki fonksiyonu tetikle (ADAM konuşsun)
        # Mesajın başına özel bir işaret koyuyoruz ki sistem ayırt etsin
        self.callback(f"⏰ HATIRLATMA: {message}")

    def shutdown(self):
        self.scheduler.shutdown()