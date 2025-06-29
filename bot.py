import asyncio
import logging
from telegram.ext import Application, MessageHandler, filters

from config.settings import settings
from handlers.voice_handler import VoiceHandler
from utils.logger import setup_logger

logger = setup_logger(level=getattr(logging, settings.LOG_LEVEL))


class TranscriptionBot:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.voice_handler = VoiceHandler()
        self.application = Application.builder().token(self.token).build()

    def setup_handlers(self):
        """Налаштування обробників повідомлень"""
        voice_handler = MessageHandler(
            filters.VOICE,
            self.voice_handler.handle_voice_message
        )

        # Обробник аудіо файлів
        audio_handler = MessageHandler(
            filters.AUDIO,
            self.voice_handler.handle_voice_message
        )

        self.application.add_handler(voice_handler)
        self.application.add_handler(audio_handler)

    async def start_bot(self):
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск козацького Слоняри для транскрипції...")
            self.setup_handlers()

            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            logger.info("✅ Слоняру успішно запущено!")

            await asyncio.Event().wait()

        except Exception as e:
            logger.error(f"❌ Помилка запуску Слоняри: {e}")
            raise
        finally:
            await self.application.stop()


def main():
    """Головна функція"""
    try:
        bot = TranscriptionBot()
        asyncio.run(bot.start_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Слоняру зупинено користувачем")
    except Exception as e:
        logger.error(f"💥 Критична помилка зі Слонярою: {e}")

if __name__ == "__main__":
    main()