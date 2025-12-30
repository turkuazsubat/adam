import logging
import os

# Senin belirttiğin log dosyası
LOG_FILE = "project.log"

def setup_logging():
    """
    Tüm sistemi ve dış kütüphaneleri susturur, logları dosyaya hapseder.
    """
    # 1. Kök loglayıcıdaki tüm mevcut handler'ları temizle (Gürültünün kaynağı bunlar)
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers[:]:
            root.removeHandler(handler)

    # 2. Sadece dosyaya yazacak şekilde yapılandır
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        encoding='utf-8'
    )

    # 3. İnatçı kütüphanelerin sesini manuel olarak kıs (WARNING altına düşemezler)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)

def log_event(level, message, source="System"):
    """
    Dosyaya log yazar. Konsola hiçbir şey basmaz.
    """
    logger = logging.getLogger(source)
    if level == "INFO": logger.info(message)
    elif level == "WARNING": logger.warning(message)
    elif level == "ERROR": logger.error(message)
    elif level == "CRITICAL": logger.critical(message)

# Dosya import edildiği an susturma işlemi devreye girsin
setup_logging()