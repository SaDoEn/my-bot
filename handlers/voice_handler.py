import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes

from services.transcription_service import TranscriptionService
from utils.logger import setup_logger

logger = setup_logger()


class VoiceHandler:
    def __init__(self):
        self.transcription_service = TranscriptionService()

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробляє голосові повідомлення та аудіо файли"""
        try:
            user = update.effective_user
            chat = update.effective_chat

            logger.info(f"📢 Отримано голосочок {user.first_name} в чаті {chat.title or chat.id}")

            status_message = await update.message.reply_text(
                "🎤 Обробляю голосочок...",
                reply_to_message_id=update.message.message_id
            )

            if update.message.voice:
                file_obj = update.message.voice
                file_extension = ".ogg"
                logger.info("🎵 Обробляю voice повідомлення")
            elif update.message.audio:
                file_obj = update.message.audio
                file_extension = ".mp3"
                logger.info("🎵 Обробляю audio файл")
            else:
                await status_message.edit_text("❌ Непідтримуваний тип файлу")
                return

            file = await context.bot.get_file(file_obj.file_id)

            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                temp_file_path = temp_file.name

            try:
                await file.download_to_drive(temp_file_path)
                logger.info(f"📥 Файл завантажено: {temp_file_path}")

                if not os.path.exists(temp_file_path):
                    raise FileNotFoundError(f"Файл не існує: {temp_file_path}")

                file_size = os.path.getsize(temp_file_path)
                if file_size == 0:
                    raise ValueError("Завантажений файл порожній")

                logger.info(f"📊 Розмір файлу: {file_size} байт")

                await status_message.edit_text("🔄 Розпізнаю мовлення...")

                transcription = await self.transcription_service.transcribe_audio(temp_file_path)

                if transcription and transcription.strip():
                    response_text = f"📝 **Текст повідомлення:**\n\n{transcription}"

                    await status_message.edit_text(
                        response_text,
                        parse_mode='Markdown'
                    )

                    logger.info(f"✅ Транскрипція завершена для {user.first_name}")
                else:
                    await status_message.edit_text("❌ Не вдалося розпізнати мовлення. Спробуйте говорити чіткіше.")
                    logger.warning("⚠️ Порожня транскрипція")

            except Exception as e:
                logger.error(f"❌ Помилка обробки аудіо: {e}")
                await status_message.edit_text(
                    "❌ Помилка при обробці голосового повідомлення. Спробуйте ще раз."
                )
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    logger.info(f"🗑️ Тимчасовий файл видалено: {temp_file_path}")

        except Exception as e:
            logger.error(f"💥 Критична помилка в обробці голосового повідомлення: {e}")
            if 'status_message' in locals():
                await status_message.edit_text("❌ Виникла помилка. Спробуйте ще раз.")
            else:
                await update.message.reply_text("❌ Виникла помилка. Спробуйте ще раз.")