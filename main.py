import asyncio
import re
import time

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ChatPermissions
)


# ==========================
# ТОКЕН БОТА
# ==========================

BOT_TOKEN = "8703274155:AAHvcQwkFxiCu37fgw00HOiB_MEu4mojEsI"


# ==========================
# ПРИВЕТСТВИЕ
# ==========================

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


# ==========================
# ПРАВИЛА
# ==========================

RULES = """
📜 ПРАВИЛА ПОВЕДЕНИЯ И ОБЩЕНИЯ В ЧАТЕ:

1. Уважение!
2. Без политики!
3. Без чрезмерного мата!
4. Участники группы только 18+!
5. Никакой рекламы!


⚠️ Предупреждение ❗⛔


✅ Просим соблюдать эстетические правила при пересылке артов.

В группе не допустимы:

❗ Жёсткий хоррор с кровью и ужасами.

❗ Порнография и жёсткая эротика.

❗ Арты с насилием и кровью.


✅ Приветствуются:

Красивые эстетичные арты.

Лёгкая завуалированная эротика.

Оголённая грудь допускается.

Девушки и парни в белье.

Лёгкий хоррор без жести.


Главное — КРАСОТА и ЭСТЕТИКА!


⛔ За нарушение правил материал удаляется администрацией.


🙏 Уважайте всех участников группы.
"""


# ==========================
# АНТИ-МАТ
# ==========================

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
    "лох"
]


WARN_LIMIT = 3
MUTE_TIME = 3600


# ==========================
# БОТ
# ==========================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


warnings = {}


# ==========================
# КНОПКА
# ==========================

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📜 Правила"
            )
        ]
    ],
    resize_keyboard=True
)


# ==========================
# ПРОВЕРКА АДМИНА
# ==========================

async def is_admin(chat_id, user_id):

    member = await bot.get_chat_member(
        chat_id,
        user_id
    )

    return member.status in [
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR
    ]


# ==========================
# ПРОВЕРКА СЛОВ
# ==========================

def normalize(text):

    text = text.lower()

    replace = {
        "@": "а",
        "0": "о",
        "1": "и",
        "3": "з",
        "4": "ч"
    }

    for a, b in replace.items():
        text = text.replace(a, b)

    return re.sub(
        r"[^а-яa-z]",
        "",
        text
    )


def has_bad_word(text):

    text = normalize(text)

    for word in BAD_WORDS:

        if normalize(word) in text:
            return True

    return False


# ==========================
# START
# ==========================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "👋 Бот работает!\n\n"
        "Команды:\n"
        "/command1 — приветствие\n"
        "/command2 — правила",
        reply_markup=keyboard
    )


# ==========================
# COMMAND 1
# ==========================

@dp.message(Command("command1"))
async def command1(message: Message):

    await message.answer(
        WELCOME_TEXT
    )


# ==========================
# COMMAND 2
# ==========================

@dp.message(Command("command2"))
async def command2(message: Message):

    await message.answer(
        RULES,
        reply_markup=keyboard
    )


# ==========================
# RULES
# ==========================

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


# ==========================
# НОВЫЙ УЧАСТНИК
# ==========================

@dp.chat_member()
async def new_member(event):

    if event.new_chat_member.status == ChatMemberStatus.MEMBER:

        user = event.new_chat_member.user


        await bot.send_message(
            event.chat.id,
            f"<b>{user.first_name}</b>\n\n"
            f"{WELCOME_TEXT}"
        )


        await asyncio.sleep(2)


        await bot.send_message(
            event.chat.id,
            RULES,
            reply_markup=keyboard
        )


# ==========================
# МОДЕРАЦИЯ
# ==========================

@dp.message()
async def moderation(message: Message):

    if not message.text:
        return


    if await is_admin(
        message.chat.id,
        message.from_user.id
    ):
        return


    if has_bad_word(message.text):

        try:
            await message.delete()
        except:
            pass


        key = (
            message.chat.id,
            message.from_user.id
        )


        warnings[key] = warnings.get(
            key,
            0
        ) + 1


        await message.answer(
            f"⚠️ {message.from_user.first_name}, "
            f"сообщение удалено.\n"
            f"Нарушение {warnings[key]}/{WARN_LIMIT}"
        )


        if warnings[key] >= WARN_LIMIT:

            await bot.restrict_chat_member(
                message.chat.id,
                message.from_user.id,
                permissions=ChatPermissions(
                    can_send_messages=False
                ),
                until_date=int(time.time())
                + MUTE_TIME
            )


            await message.answer(
                "🔇 Пользователь получил мут на 1 час."
            )


            warnings[key] = 0



# ==========================
# ЗАПУСК
# ==========================

async def main():

    print("Бот запущен")

    await dp.start_polling(
        bot,
        allowed_updates=[
            "message",
            "chat_member"
        ]
    )


if __name__ == "__main__":

    asyncio.run(main())