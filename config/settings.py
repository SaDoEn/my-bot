import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Налаштування додатку"""

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    TRANSCRIPTION_CONFIG = {
        "language": "uk",
        "task": "transcribe",
        "fp16": False,
        "verbose": False,
        "word_timestamps": False,
        "temperature": (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
        "compression_ratio_threshold": 2.4,
        "logprob_threshold": -1.0,
        "no_speech_threshold": 0.6,
        "condition_on_previous_text": True,
        "initial_prompt": """Це українська розмовна мова. Використовуй правильну українську граматику та орфографію. 
                Розпізнавай українські слова точно, враховуючи особливості вимови. 
                Не плутай українські слова з російськими. Дотримуйся норм сучасної української мови.""",
    }

    @classmethod
    def validate(cls):
        """Перевірка наявності обов'язкових налаштувань"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не знайдено в .env файлі")

        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if cls.WHISPER_MODEL not in valid_models:
            raise ValueError(f"WHISPER_MODEL має бути одним з: {valid_models}")

        return True


settings = Settings()
settings.validate()