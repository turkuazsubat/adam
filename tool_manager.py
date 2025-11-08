import logging
from tools.note_tool import take_note #Hafta 5, tools paketinden ilk import
from tools.todo_tool import add_todo, list_todos #Hatfa 6 todo aracını import et 

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
            "todo_add": add_todo,
            "todo_list": list_todos,
            #Gelecekte eklenecekler(HAFTA 5)
            #"calendar": add_to_calendar,
            #"weather": get_weather,
        }

        # 'find_tool_for_command' fonksiyonuna artık gerek kalmadı,
        # çünkü 'nlu.py' bu mantığı (tool_key) bizim için yapıyor.

        logger.info("ToolManager başlatıldı ve araçlar yüklendi.")

    def execute_tool(self, tool_key: str, payload: str) -> str:
        """
        NLU'dan gelen 'tool_key'e göre belirlenen aracı bulur 
        ve verilen 'payload' (görev yükü) ile çalıştırır.
        """

        if tool_key not in self.tools:
            logger.warning(f"Bilinmeyen araç çağırıldı: {tool_key}")
            return "Üzgünüm, bu komutu yürütüecek bir araç bulamadım"
    
        try:
            #Hafta6 düzeltme 
            tool_function = self.tools[tool_key]
            
            # --- KRİTİK DÜZELTME (Hata 2) ---
            # 'payload'un 'None' olup olmadığını kontrol et.
            # 'list_todos' (payload=None) ise argümansız çalıştır.
            # 'note' veya 'todo_add' (payload=metin) ise argümanla çalıştır.
            if payload is not None:
                result = tool_function(payload)
            else:
                result = tool_function()
                
            return result
        
        except TypeError as e:
            if "required positional argument" in str(e) or "takes 0" in str(e) or "takes 1" in str(e):
                 logger.error(f"Araç ({tool_key}) yanlış argümanla çağrıldı. Payload: {payload}. Hata: {e}")
                 return f"Üzgünüm, '{tool_key}' komutunu çalıştırırken bir argüman hatası oluştu."
            else:
                 logger.error(f"Araç çalıştırılırken (TypeError) hata oluştu ({tool_key}): {e}")
                 return f"Üzgünüm, '{tool_key}' aracını çalıştırırken bir tip hatası oluştu."
        except Exception as e:
            logger.error(f"Araç çalıştırılırken (Genel Hata) hata oluştu ({tool_key}): {e}")
            return f"Üzgünüm, '{tool_key}' aracını çalıştırırken bir hata oluştu."