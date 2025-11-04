import logging
from logger import log_event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class FeedbackManager:
    """
    Kullanıcıdan gelen geri bildirim komutlarını işler ve MemoryManager'a yönlendirir.
    Lite RLHF politikasının (V1) komut-skor eşlemesini yapar.
    """

    # Desteklenen komutlar ve skorları (Lite RLHF V1)
    # Bu skorlar, ilerideki Hafta 4/5'te 'feedback' tablosuna yazılacaktır.
    COMMAND_MAP = {

        "!onay":   {'type': 'correct', 'score': 1, 'action':'promote'},
        '!yanlis': {'type': 'incorrect', 'score': -1, 'action':'invalidate'},
        '!kaydet': {'type': 'important', 'score': 2, 'action':'promote'}
        
    }

    def __init__(self,memory_manager):
        # MemoryManager nesnesini alıyoruz ki veritabanına erişebilelim

        self.memory = memory_manager
        logger.info("FeedbackManager başlatıldı.")

    def handle_command(self, command_input:str) -> str:
        '''
        Gelen ! komutunu ayrıştırır, skorlar ve ilgili aksiyonu tetikler
        '''
        command = command_input.lower().split()[0]

        if command not in self.COMMAND_MAP:
            return f"Bilinmeyen geri bildirim komutu: {command}. Desteklenenler {', '.join(self.COMMAND_MAP.keys())}"

        feedback_data = self.COMMAND_MAP[command]

        #Son etkileşim ID'sini Hafıza Yöneticisinden al
        #Bu ID, geri bildirimin hangi cevaba ait olduğunu belirtir
        interaction_id = self.memory.last_interaction_id

        if interaction_id is None:
            return "Önce normal bir sorgu yapmalısınız. Geri bildirim kaydedilecek bir etkileşim bulunamadı."
        
        # 1. Geri Bildirimi feedback tablosuna kaydet ( memory.py'deki fonksiyon çağırılacak)
        self.memory.save_feedback(
            interaction_id=interaction_id,
            feedback_type = feedback_data['type'],
            score=feedback_data['score']
        )

        response = f"Geri bildirim ('{feedback_data['type']}'): Kaydedildi (ID: {interaction_id})."

        # 2. Öğrenme Kuralını Uygula(Hafızayı Güncelle)

        if feedback_data['action'] == 'promote':
            #Kalıcı hafızaya taşı

            self.memory.promote_to_memory(interaction_id)
            response += " Cevap, kalıcı hafızaya taşındı"

        elif feedback_data['action'] == 'invalidate':
            #Kalıcı hafızadaki ilgili kaydı geçersiz yap
            self.memory.invalidate_memory(interaction_id)
            response += " Geçerli bir hafıza kaydı varsa geçersiz kılındı."

        return response