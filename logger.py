import logging

def log_event(level: str, message: str, name: str = "project_x"):
    """
    Tüm modüllerin kullanabileceği merkezi loglama fonksiyonu.
    """
    logger = logging.getLogger(name)
    
    level = level.upper()
    if level == "INFO":
        logger.info(message)
    elif level == "DEBUG":
        logger.debug(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "CRITICAL":
        logger.critical(message)
    else:
        logger.info(f"Bilinmeyen log seviyesi: {level}. Mesaj INFO olarak kaydedildi: {message}")