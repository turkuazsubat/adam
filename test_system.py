import os
import sys
import logging

# Logları konsola basalım
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("🚀 SİSTEM TANI TESTİ BAŞLIYOR (HAFTA 1-10)...")
print("---------------------------------------------------")

# 1. MODÜL İMPORT KONTROLÜ
try:
    print("[1/5] Modüller aranıyor...")
    from nlu import interpret_text
    from memory import MemoryManager  # <--- DÜZELTİLDİ: Sınıf adı MemoryManager
    from semantic_engine import SemanticEngine
    from retriever import retrieve_info
    print("✅ Tüm modüller başarıyla yüklendi.")
except ImportError as e:
    print(f"❌ MODÜL HATASI: {e}")
    # Hata varsa dur, devam etme
    sys.exit(1)

# 2. VERİTABANI KONTROLÜ
try:
    print("\n[2/5] Hafıza (MemoryManager) kontrol ediliyor...")
    mem = MemoryManager() # <--- DÜZELTİLDİ
    
    # Test verisi yazıp okuyalım
    # Senin kodunda LTM'ye kayıt fonksiyonu: promote_to_memory
    test_key = "sistem testi anahtarı"
    test_val = "sistem testi değeri"
    
    print(f"   Yazılıyor: {test_key} -> {test_val}")
    success = mem.promote_to_memory(test_key, test_val) # <--- DÜZELTİLDİ: Fonksiyon adı
    
    if success:
        read_val = mem.read_from_memory(test_key)
        if read_val == test_val:
            print(f"✅ Veritabanı Okuma/Yazma Başarılı. Okunan: {read_val}")
        else:
            print(f"⚠️ Yazıldı ama okunan değer eşleşmedi. Okunan: {read_val}")
    else:
        print("❌ Veritabanına yazma işlemi başarısız oldu.")
        
except Exception as e:
    print(f"❌ HAFIZA HATASI: {e}")

# 3. SEMANTİK MOTOR (BEYİN) KONTROLÜ
try:
    print("\n[3/5] Semantik Motor (Model) yükleniyor... (Bu biraz sürebilir)")
    brain = SemanticEngine()
    
    if brain:
        # Basit bir vektör testi
        corpus = ["Kas yapmak için ağırlık kaldır.", "Başkent Ankara'dır."]
        query = "hipertrofi nedir" # Kas yapmak ile eşleşmeli
        
        # Eğer semantic_engine.py içinde hata varsa burada patlar
        best_match, score = brain.find_best_match(query, corpus)
        print(f"   Sorgu: '{query}' -> Eşleşen: '{best_match}' (Skor: {score:.2f})")
        
        if score > 0.3:
            print("✅ Semantik Motor Mantıklı Eşleşme Yaptı.")
        else:
            print("⚠️ Semantik Motor çalıştı ama skor düşük. (Model doğru yüklenmiş mi?)")
    else:
        print("❌ Semantik Motor None döndü (Başlatılamadı).")

except Exception as e:
    print(f"❌ SEMANTİK MOTOR HATASI: {e}")

# 4. NLU (NİYET) KONTROLÜ
try:
    print("\n[4/5] NLU (Niyet Analizi) Testi...")
    inputs = {
        "merhaba asistan": "general", # Veya senin NLU ayarına göre 'greeting'
        "hesap makinesini aç": "command",
        "türkiyenin başkenti neresi": "query" 
    }
    
    for text, expected_intent in inputs.items():
        res = interpret_text(text)
        intent = res.get("intent")
        print(f"   Girdi: '{text}' -> Tespit Edilen: {intent}")
        
    print("✅ NLU Fonksiyonu hata vermeden çalıştı.")
except Exception as e:
    print(f"❌ NLU HATASI: {e}")

# 5. RETRIEVER (İNTERNET/CURL) KONTROLÜ
try:
    print("\n[5/5] Retriever (CURL - Wikipedia) Testi...")
    # Zorlu sorgu: Ekli kelime (Suffix Cleaning testi)
    query = "Türkiyenin başkenti"
    print(f"   Sorgulanıyor (CURL): '{query}' ...")
    
    # Retriever hafıza objesi istiyor, yukarıda oluşturduğumuz 'mem'i veriyoruz
    result = retrieve_info(query, mem)
    
    # Sonuç analizi
    if result and ("Ankara" in result or "Türkiye" in result):
        print("✅ İnternet Erişimi BAŞARILI (Doğru içerik geldi).")
        print(f"   Çıktı Özeti: {result[:80]}...")
    elif "Sorun var" in result or "Hata" in result:
         print(f"❌ CURL Hatası veya Veri Bulunamadı. Dönen: {result}")
    else:
        print(f"⚠️ Sonuç geldi ama beklenen kelimeler yok: {result[:50]}...")
        
except Exception as e:
    print(f"❌ RETRIEVER HATASI: {e}")

print("\n---------------------------------------------------")
print("🏁 TEST TAMAMLANDI.")