from memory import MemoryManager

print("--- BELLEK TESTi BAŞLATILDI ---")
try:
    mem = MemoryManager()
    
    # Veritabanına elle veri ekleyerek tetikleyelim
    print("Veritabanına test verisi yazılıyor...")
    mem.set_profile("test_kullanici", "Adam")
    mem.set_profile("durum", "sistem_test_ediliyor")
    
    print("İşlem bitti. Lütfen klasörde 'user_profile.txt' dosyasını kontrol et.")
except Exception as e:
    print(f"Test sırasında hata oluştu: {e}")