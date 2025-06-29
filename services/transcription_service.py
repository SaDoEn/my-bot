import whisper
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
from utils.logger import setup_logger
from config.settings import settings

logger = setup_logger()


class TranscriptionService:
    def __init__(self):
        """
        Ініціалізація сервісу транскрипції
        """
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _load_model(self):
        """Завантаження моделі Whisper (відбувається один раз)"""
        if self.model is None:
            logger.info(f"🤖 Завантажую модель Whisper: {settings.WHISPER_MODEL}")
            self.model = whisper.load_model(settings.WHISPER_MODEL)
            logger.info("✅ Модель Whisper завантажена")
        return self.model

    def _preprocess_audio(self, audio_path: str) -> str:
        """
        Попередня обробка аудіо для покращення якості розпізнавання
        """
        try:
            logger.info("🔧 Початок попередньої обробки аудіо")

            audio = AudioSegment.from_file(audio_path)

            normalized_audio = audio.normalize()

            if normalized_audio.channels > 1:
                normalized_audio = normalized_audio.set_channels(1)

            target_sample_rate = 16000
            if normalized_audio.frame_rate != target_sample_rate:
                normalized_audio = normalized_audio.set_frame_rate(target_sample_rate)

            normalized_audio = normalized_audio.high_pass_filter(80)

            normalized_audio = normalized_audio.compress_dynamic_range(threshold=-20.0, ratio=4.0)

            processed_path = audio_path.replace('.', '_processed.')
            normalized_audio.export(processed_path, format="wav", parameters=["-ar", "16000", "-ac", "1"])

            logger.info(f"✅ Аудіо оброблено: {processed_path}")
            return processed_path

        except Exception as e:
            logger.error(f"❌ Помилка обробки аудіо: {e}")
            return audio_path

    def _transcribe_sync(self, audio_path: str) -> str:
        """Синхронна транскрипція аудіо файлу з покращеними налаштуваннями"""
        try:
            if not os.path.exists(audio_path):
                logger.error(f"❌ Файл не знайдено: {audio_path}")
                return ""

            file_size = os.path.getsize(audio_path)
            logger.info(f"📊 Розпочинаю транскрипцію файлу розміром {file_size} байт")

            processed_audio_path = self._preprocess_audio(audio_path)

            model = self._load_model()

            transcribe_options = {
                "language": "uk",
                "task": "transcribe",
                "fp16": False,
                "verbose": False,
                "word_timestamps": False,

                "temperature": 0.0,
                "compression_ratio_threshold": 2.0,
                "logprob_threshold": -0.5,
                "no_speech_threshold": 0.4,
                "condition_on_previous_text": True,

                "initial_prompt": """Це українська розмовна мова. Використовуй правильну українську граматику та орфографію. 
                Розпізнавай українські слова точно, враховуючи особливості вимови. 
                Не плутай українські слова з російськими. Дотримуйся норм сучасної української мови.""",
            }

            result = model.transcribe(processed_audio_path, **transcribe_options)
            transcription = result["text"].strip()

            logger.info(f"📝 Первинна транскрипція: '{transcription}'")

            if processed_audio_path != audio_path and os.path.exists(processed_audio_path):
                os.unlink(processed_audio_path)

            cleaned_transcription = self._basic_text_cleanup(transcription)

            logger.info(f"✨ Очищена транскрипція: '{cleaned_transcription}'")
            return cleaned_transcription

        except Exception as e:
            logger.error(f"❌ Помилка транскрипції: {e}")
            import traceback
            logger.error(f"💥 Детальна помилка: {traceback.format_exc()}")
            return ""

    def _basic_text_cleanup(self, text: str) -> str:
        """
        Базове очищення тексту без використання словника виправлень
        """
        if not text:
            return text

        import re

        text = re.sub(r'\s+', ' ', text)

        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([.!?])\s*([а-яієїґА-ЯІЄЇҐ])', r'\1 \2', text)

        text = text.strip()

        if text:
            text = text[0].upper() + text[1:]

        return text

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Асинхронна транскрипція аудіо файлу

        Args:
            audio_path (str): Шлях до аудіо файлу

        Returns:
            str: Розпізнаний текст
        """
        try:
            logger.info(f"🎤 Починаю транскрипцію файлу: {audio_path}")

            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                self.executor,
                self._transcribe_sync,
                audio_path
            )

            if transcription:
                logger.info("✅ Транскрипція успішно виконана")
            else:
                logger.warning("⚠️ Транскрипція повернула порожній результат")

            return transcription

        except Exception as e:
            logger.error(f"💥 Помилка в асинхронній транскрипції: {e}")
            return ""

    def __del__(self):
        """Закриття executor при знищенні об'єкта"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)