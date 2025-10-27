import logging

LOG_FILE = "project.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

def log_event(level, message):
    if level == "ERROR":
        logging.error(message)
    else:
        logging.info(message)
