from memory import MemoryManager

mem = MemoryManager()
# Test verilerini giriyoruz
mem.set_profile("user_name", "Adam")
mem.set_profile("expertise", "teknik olmayan kullanıcı")
mem.set_profile("tone", "yardımsever ve sade")
print("Profil verileri kaydedildi. Lütfen 'user_profile.txt' dosyasını kontrol et.")