import logging
import os

class LoggingConfig:

    @staticmethod
    def configurar_logging():
        if not os.path.exists('logs'):
            os.makedirs('logs')
        logging.basicConfig(level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler("logs/traducao.log", encoding='utf-8'),
            logging.StreamHandler() # Exibe no console
        ]
    )