from aiogram import Bot, types
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_db_connection
from utils import get_main_keyboard
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD, ADMIN_EMAIL

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определение состояний для FSM
class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()

# Настройки SMTP для отправки писем (замени на свои данные)

async def handle_feedback(message: types.Message, state: FSMContext):
    """Обрабатывает команду /feedback: запрашивает текст отзыва."""
    user_id = message.from_user.id
    await message.answer(
        "📝 Пожалуйста, напишите ваш отзыв или предложение по игре.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(FeedbackStates.waiting_for_feedback)
    logger.info(f"Пользователь {user_id} начал ввод отзыва")

async def process_feedback(message: types.Message, state: FSMContext, bot: Bot):
    """Обрабатывает введённый отзыв, сохраняет в БД и отправляет на почту."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    feedback_text = message.text

    # Сохранение отзыва в базе данных
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO feedback (user_id, username, feedback_text) VALUES (?, ?, ?)',
              (user_id, username, feedback_text))
    conn.commit()
    conn.close()

    # Логирование отзыва
    logger.info(f"Получен отзыв от {username} ({user_id}): {feedback_text}")

    # Отправка отзыва на почту
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f"Новый отзыв от {username} ({user_id})"
        body = f"Отзыв от {username} (ID: {user_id}):\n\n{feedback_text}"
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Включение TLS
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, ADMIN_EMAIL, msg.as_string())
        logger.info(f"Отзыв отправлен на почту {ADMIN_EMAIL}")
    except Exception as e:
        logger.error(f"Ошибка при отправке отзыва на почту {ADMIN_EMAIL}: {e}")

    # Подтверждение пользователю
    await message.answer(
        "Спасибо за ваш отзыв! Он отправлен разработчику.",
        reply_markup=get_main_keyboard()
    )
    await state.clear()