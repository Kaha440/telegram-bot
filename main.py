import asyncio
import os
import re
import time

from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ChatPermissions,
)


# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "Переменная окружения BOT_TOKEN не установлена!"
    )

# Render передаёт порт через переменную PORT
PORT = int(os.getenv("PORT", "10000"))


# =========================================================
# ПРИВЕТСТВИЕ
# =========================================================

WELCOME_TEXT = """
👋 Добро пожаловать, друг! 🤗

Новый участник обнаружен — и мы этому безумно рады! 🥳

Добро пожаловать в Воображариум (18+), где арты из шеда оживают, а общение такое, что улыбка будет у тебя на лице всегда 😉

🤩 Важные инструкции:

Расслабьтесь.
Общайтесь.
Получайте удовольствие.

Читайте закреп — там правила 😉

Скиньте свою ссылочку на шед в ветку "База данных" и день рождения по желанию.

Знакомьтесь, шутите, задавайте вопросы — мы все свои! 😉
"""


# =========================================================
# ПРАВИЛА
# =========================================================

RULES = """
📜 <b>ПРАВИЛА ПОВЕДЕНИЯ И ОБЩЕНИЯ В ЧАТЕ:</b>

1. Уважение!
2. Без политики!
3. Без чрезмерного мата!
4. Участники группы только 18+!
5. Никакой рекламы!

⚠️ <b>Предупреждение ❗⛔</b>

✅ Просим соблюдать эстетические правила при пересылке артов.

В группе не допустимы:

❗ Жёсткий хоррор с кровью и ужасами.

❗ Порнография и жёсткая эротика.

❗ Арты с насилием и кровью.

✅ <b>Приветствуются:</b>

Красивые эстетичные арты.

Лёгкая завуалированная эротика.

Оголённая грудь допускается.

Девушки и парни в белье.

Лёгкий хоррор без жести.

<b>Главное — КРАСОТА и ЭСТЕТИКА!</b>

⛔ За нарушение правил материал удаляется администрацией.

🙏 Уважайте всех участников группы.
"""


# =========================================================
# АНТИ-МАТ
# =========================================================

BAD_WORDS = [
    "сука",
    "блять",
    "бля",
    "хуй",
    "пизда",
    "ебать",
    "мудак",
    "дебил",
    "идиот",
    "тупой",
    "лох",
]

WARN_LIMIT = 3
MUTE_TIME = 3600


# =========================================================
# BOT / DISPATCHER
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    ),
)

dp = Dispatcher()

warnings = {}


# =========================================================
# КЛАВИАТУРА
# =========================================================

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📜 Правила")
        ]
    ],
    resize_keyboard=True,
)


# =========================================================
# ПРОВЕРКА АДМИНИСТРАТОРА
# =========================================================

async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )

        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        )

    except Exception as e:
        print(
            f"Ошибка проверки администратора "
            f"{user_id} в чате {chat_id}: {e}"
        )

        return False


# =========================================================
# НОРМАЛИЗАЦИЯ ТЕКСТА
# =========================================================

def normalize(text: str) -> str:
    text = text.lower()

    replace = {
        "@": "а",
        "0": "о",
        "1": "и",
        "3": "з",
        "4": "ч",
        "$": "с",
    }

    for old, new in replace.items():
        text = text.replace(old, new)

    return re.sub(
        r"[^а-яa-z]",
        "",
        text,
    )


def has_bad_word(text: str) -> bool:
    normalized_text = normalize(text)

    for word in BAD_WORDS:
        if normalize(word) in normalized_text:
            return True

    return False


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "👋 Бот работает!\n\n"
        "Команды:\n"
        "/command1 — приветствие\n"
        "/command2 — правила",
        reply_markup=keyboard,
    )


# =========================================================
# COMMAND 1
# =========================================================

@dp.message(Command("command1"))
async def command1(message: Message):

    await message.answer(
        WELCOME_TEXT
    )


# =========================================================
# COMMAND 2
# =========================================================

@dp.message(Command("command2"))
async def command2(message: Message):

    await message.answer(
        RULES,
        reply_markup=keyboard,
    )


# =========================================================
# RULES
# =========================================================

@dp.message(Command("rules"))
async def rules(message: Message):

    await message.answer(
        RULES
    )


@dp.message(F.text == "📜 Правила")
async def rules_button(message: Message):

    await message.answer(
        RULES
    )


# =========================================================
# НОВЫЙ УЧАСТНИК
# =========================================================

@dp.chat_member()
async def new_member(event):

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    # Срабатываем, когда пользователь становится обычным участником
    if (
        new_status == ChatMemberStatus.MEMBER
        and old_status != ChatMemberStatus.MEMBER
    ):

        user = event.new_chat_member.user

        try:
            await bot.send_message(
                event.chat.id,
                f"<b>{user.first_name}</b>\n\n"
                f"{WELCOME_TEXT}",
            )

            await asyncio.sleep(2)

            await bot.send_message(
                event.chat.id,
                RULES,
                reply_markup=keyboard,
            )

        except Exception as e:
            print(
                f"Ошибка приветствия нового участника: {e}"
            )


# =========================================================
# МОДЕРАЦИЯ
# =========================================================

@dp.message()
async def moderation(message: Message):

    # Нет текста — ничего не проверяем
    if not message.text:
        return

    # Сообщения от пользователей без from_user
    if not message.from_user:
        return

    # Администраторов не модерируем
    if await is_admin(
        message.chat.id,
        message.from_user.id,
    ):
        return

    # Проверяем мат
    if not has_bad_word(message.text):
        return

    # Удаляем сообщение
    try:
        await message.delete()

    except Exception as e:
        print(
            f"Не удалось удалить сообщение: {e}"
        )

    # Считаем предупреждения
    key = (
        message.chat.id,
        message.from_user.id,
    )

    warnings[key] = warnings.get(key, 0) + 1

    warning_count = warnings[key]

    # Отправляем предупреждение
    try:
        warning_message = await message.answer(
            f"⚠️ {message.from_user.first_name}, "
            f"сообщение удалено.\n"
            f"Нарушение {warning_count}/{WARN_LIMIT}"
        )

        # Удаляем предупреждение через 10 секунд
        await asyncio.sleep(10)

        try:
            await warning_message.delete()
        except Exception:
            pass

    except Exception as e:
        print(
            f"Ошибка отправки предупреждения: {e}"
        )

    # Если 3 нарушения — мут
    if warning_count >= WARN_LIMIT:

        try:
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_audios=False,
                    can_send_documents=False,
                    can_send_photos=False,
                    can_send_videos=False,
                    can_send_video_notes=False,
                    can_send_voice_notes=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_change_info=False,
                    can_invite_users=True,
                    can_pin_messages=False,
                    can_manage_topics=False,
                ),
                until_date=int(time.time()) + MUTE_TIME,
            )

            await message.answer(
                f"🔇 {message.from_user.first_name} "
                f"получил мут на 1 час."
            )

            print(
                f"Пользователь {message.from_user.id} "
                f"получил мут на 1 час."
            )

        except Exception as e:
            print(
                f"Ошибка выдачи мута: {e}"
            )

        # Обнуляем предупреждения
        warnings[key] = 0


# =========================================================
# HTTP SERVER ДЛЯ RENDER
# =========================================================

async def health(request):
    return web.Response(
        text="Bot is running!",
        status=200,
    )


async def start_web_server():

    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=PORT,
    )

    await site.start()

    print(
        f"HTTP сервер запущен на порту {PORT}"
    )

    return runner


# =========================================================
# ЗАПУСК
# =========================================================

async def main():

    print("=================================")
    print("Запуск Telegram-бота...")
    print("=================================")

    # Удаляем webhook.
    # Это важно, если бот раньше запускался через webhook.
    try:
        await bot.delete_webhook(
            drop_pending_updates=True
        )

        print("Webhook удалён.")

    except Exception as e:
        print(
            f"Ошибка удаления webhook: {e}"
        )

    # Запускаем HTTP сервер для Render
    web_runner = await start_web_server()

    try:

        print("Бот запущен и готов к работе!")
        print("Telegram polling запущен.")

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )

    finally:

        print("Остановка бота...")

        await web_runner.cleanup()
        await bot.session.close()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):

        print(
            "Бот остановлен."
        )
