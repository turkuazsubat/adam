import logging
from tools.note_tool import take_note #Hafta 5, tools paketinden ilk import

logger = logging.getLogger(__name__)


class ToolManager:
    '''
    NLU' dan gelen 'command' niyetini analiz eder,
    doğru aracı bulur ve çalıştırır.
    '''

    def __init__(self):
        #Araç kaydı: Hangi anahtar kelimenin hangi fonksiyonu tetikleyeceğimi eşleştirir
        #Bu yapı, gelecekte yeni araçlar eklememizi kolaylaştırır.

        self.tools = {
            "note": take_note,
            #Gelecekte eklenecekler(HAFTA 5)
            #"calendar": add_to_calendar,
            #"weather": get_weather,
        }

        #Komut -> Araç Eşleştirmesi (NLU'dan gelen kök kelimelere göre)
        #NLU'da "not" ve "al" gördüğünde, "note" aracını tetikler.

        self.command_to_tool_map = {
            ("not","al"): "note",
        }
        logger.info("ToolManager başlatıldı ve araçlar yüklendi.")

    def find_tool_for_command(self, keywords: list) -> str:

        '''
        NLU'dan gelen kök kelime listesini analiz eder ve 
        çalıştıralacak aracın adını ( örn: "note") bulur.
        '''

        #Şimdilik çok basit bir eşleştirme yapıyoruz.
        # "not" ve "al" kelimeleri NLU keywords'ları içinde geçiyorsa:
        if "not" in keywords and "al" in keywords:
            return "note" #Çalıştırılacak aracın adı

        return None #Uygun aracın bulunmadığı senaryo
    
    def execute_tool(self, tool_name: str, payload: str) -> str:
        '''
        Belirlenen aracı bulur ve verilen payload(görev yükü) ile çalıştırır.
        '''

        if tool_name not in self.tools:
            logger.warning(f"Bilinmeyen araç çağırıldı: {tool_name}")
            return "Üzgünüm, bu komutu yürütüecek bir araç bulamadım"
    
        try:
            #Sözlükten doğru fonksiyonu bul (örn: take_note)
            tool_function = self.tools[tool_name]

            result = tool_function(payload)
            return result
        
        except Exception as e:
            logger.error(f"Araç çalıştırılırken hata oluştu ({tool_name}): {e}")
            return f"Üzgünüm, '{tool_name}' aracını çalıştırırken bir hata oluştu."