import telebot as tb
from telebot import types
import random
import threading
from collections import defaultdict
from data import botkey

# WARN! YOU NEED TO CREATE FILE data.py WITH VARIABLE botkey

bot = tb.TeleBot(botkey)

# База данных ситуаций
situations = [
    {
        "id": 1,
        "description": "Ты проспал и опаздываешь в школу, а родители уже ушли на работу."
    },
    {
        "id": 2,
        "description": "Учитель случайно назвал тебя чужим именем, и весь класс ржёт."
    },
    {
        "id": 3,
        "description": "Ты забыл сделать домашку, а сегодня как раз проверяют."
    },
    {
        "id": 4,
        "description": "Ты нашел(а) старый дневник и не можешь поверить, что это писал(а)."
    },
    {
        "id": 5,
        "description": "Ты написал(а) другу 'Привет, как дела?', а он прочитал и не ответил."
    },
    {
        "id": 6,
        "description": "Ты пытаешься объяснить бабушке, как отправить стикер в WhatsApp."
    },
    {
        "id": 7,
        "description": "Ты случайно отправил(а) мем про учителя в общий чат класса."
    },
    {
        "id": 8,
        "description": "Ты весь вечер решал(а) сложную задачу, а ответ оказался неправильным."
    },
    {
        "id": 9,
        "description": "Ты пришёл(а) в новую компанию, и все говорят на своих внутренних шутках."
    },
    {
        "id": 10,
        "description": "Ты пошёл(а) гулять, а на улице внезапно дождь, и телефон на 5%."
    },
    {
        "id": 11,
        "description": "Ты хотел(а) сделать крутое селфи, но получилось как в старых мемах."
    },
    {
        "id": 12,
        "description": "Ты случайно отправил(а) голосовое вместо текста, и там фоном играет странная музыка."
    },
    {
        "id": 13,
        "description": "Ты весь день в наушниках, а потом понимаешь, что они не были подключены к телефону."
    },
    {
        "id": 14,
        "description": "Ты долго выбирал(а), что посмотреть, а потом заснул(а) через 5 минут."
    },
    {
        "id": 15,
        "description": "Ты идёшь в гардероб и видишь, что у тебя стырили красовки."
    }
]








active_games = {}

class MemeGame:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.current_situation = None
        self.used_situations = set()
        self.message_to_reply = None
        self.memes = {}  # {user_id: {'text': meme_text, 'scores': [], 'username': username}}
        self.scores = defaultdict(int)  # {user_id: total_score}
        self.timer = None
        self.current_meme_index = 0
        self.meme_list = []
        self.voted_users = set()
        self.all_participants = set()

    def start(self):
        """Начинает новую игру"""
        self.send_situation()

    def send_situation(self):
        """Отправляет новую ситуацию в чат"""
        available = [s for s in situations if s["id"] not in self.used_situations]
        
        if not available:
            self.show_final_results()
            self.end_game()
            return

        self.current_situation = random.choice(available)
        self.used_situations.add(self.current_situation["id"])
        self.memes.clear()
        self.voted_users.clear()
        self.all_participants.clear()
        
        msg = bot.send_message(
            self.chat_id,
            f"🎲 Ситуация:\n{self.current_situation['description']}\n\n"
            "Отправляйте свои мемные ответы на это сообщение в течение 15 секунд!"
        )
        self.message_to_reply = msg.message_id
        
        self.timer = threading.Timer(15.0, self.start_voting)
        self.timer.start()

    def handle_response(self, message):
        """Обрабатывает текстовый ответ пользователя"""
        if message.reply_to_message and message.reply_to_message.message_id == self.message_to_reply:
            user_id = message.from_user.id
            username = message.from_user.username or message.from_user.first_name
            self.memes[user_id] = {'text': message.text, 'scores': [], 'username': username}
            self.all_participants.add(user_id)

    def start_voting(self):
        """Начинает процесс голосования"""
        if not self.memes:
            bot.send_message(self.chat_id, "Никто не отправил мемы! Пропускаем этот раунд.")
            self.send_situation()
            return

        self.meme_list = list(self.memes.items())
        self.current_meme_index = 0
        self.voted_users.clear()
        self.show_next_meme_for_voting()

    def show_next_meme_for_voting(self):
        """Показывает следующий мем для голосования"""
        if self.current_meme_index >= 5:
            self.calculate_round_results()
            threading.Timer(5.0, self.send_situation).start()
            return

        user_id, meme_data = self.meme_list[self.current_meme_index]
        markup = types.InlineKeyboardMarkup()
        for i in range(1, 6):
            markup.add(types.InlineKeyboardButton(str(i), callback_data=f"rate_{user_id}_{i}"))
        
        bot.send_message(
            self.chat_id,
            f"Мем от @{meme_data['username']}:\n{meme_data['text']}\n\n"
            "Оцените по шкале от 1 до 5 (могут голосовать все участники):",
            reply_markup=markup
        )

    def handle_rating(self, user_id, rater_id, score):
        """Обрабатывает оценку мема"""
        if rater_id not in self.all_participants:
            return False
        
        if (rater_id, user_id) in self.voted_users:
            return False
        
        if user_id in self.memes:
            self.memes[user_id]['scores'].append(score)
            self.voted_users.add((rater_id, user_id))
            
            if len(self.voted_users) == len(self.all_participants) * (self.current_meme_index + 1):
                self.current_meme_index += 1
                self.show_next_meme_for_voting()
            
            return True
        return False

    def calculate_round_results(self):
        """Вычисляет результаты раунда"""
        results = []
        for user_id, meme_data in self.meme_list:
            if meme_data['scores']:
                avg_score = sum(meme_data['scores']) / len(meme_data['scores'])
                self.scores[user_id] += avg_score
                results.append(f"@{meme_data['username']}: {avg_score:.1f} баллов (оценки: {', '.join(map(str, meme_data['scores']))})")
        
        if results:
            bot.send_message(
                self.chat_id,
                "Результаты этого раунда:\n" + "\n".join(results)
            )

    def show_final_results(self):
        """Показывает финальные результаты игры"""
        if not self.scores:
            bot.send_message(self.chat_id, "Игра завершена! Нет результатов для отображения.")
            return

        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        result_text = "🏆 Финальные результаты:\n"
        for i, (user_id, score) in enumerate(sorted_scores, 1):
            username = next((m['username'] for m in self.memes.values() if m.get('username')), "Unknown")
            result_text += f"{i}. @{username}: {score:.1f} баллов\n"
        
        bot.send_message(self.chat_id, result_text)

    def end_game(self):
        """Завершает игру"""
        if self.timer:
            self.timer.cancel()
        if self.chat_id in active_games:
            del active_games[self.chat_id]

@bot.message_handler(commands=['start'])
def start(message):
    """Обработчик команды /start"""
    if message.chat.type == "private":
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Добавить в группу", url="https://t.me/YourBotName?startgroup=true")
        markup.add(btn)
        
        bot.reply_to(message,
            "👋 Привет! Я бот для весёлых игр в группах.\n"
            "Добавь меня в группу и используй /gamelist для списка игр!",
            reply_markup=markup)
    else:
        bot.reply_to(message, 
            "Используйте команды:\n"
            "/gamelist - список доступных игр\n"
            "/memegame - начать игру в мемы")

@bot.message_handler(commands=['help'])
def help(message):
    """Обработчик команды /help"""
    bot.reply_to(message,
        "ℹ Доступные команды:\n"
        "/gamelist - список игр\n"
        "/memegame - игра в мемы\n"
        "/stopgame - остановить текущую игру\n\n"
        "Для админов групп:\n"
        "/settings - настройки бота")

@bot.message_handler(commands=['gamelist'])
def gamelist(message):
    """Показывает список доступных игр"""
    if message.chat.type not in ["group", "supergroup"]:
        bot.reply_to(message, "Эта команда работает только в группах!")
        return

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Начать игру в мемы", callback_data="start_memegame")
    markup.add(btn)
    
    bot.reply_to(message,
        "🎮 Доступные игры:\n\n"
        "1. /memegame - Игра в мемы\n"
        "   Участники придумывают мемные ответы на ситуации\n"
        "2. (скоро добавим ещё игры!)",
        reply_markup=markup)

@bot.message_handler(commands=['stopgame'])
def stopgame(message):
    """Останавливает текущую игру"""
    if message.chat.id in active_games:
        active_games[message.chat.id].end_game()
        bot.reply_to(message, "Игра остановлена!")
    else:
        bot.reply_to(message, "Сейчас нет активных игр.")

@bot.message_handler(commands=['memegame'])
def start_memegame(message):
    """Запускает игру в мемы"""
    if message.chat.type not in ["group", "supergroup"]:
        return

    # Проверка прав администратора
    admins = bot.get_chat_administrators(message.chat.id)
    is_admin = any(admin.user.id == message.from_user.id for admin in admins)
    
    if not is_admin:
        bot.reply_to(message, "❌ Только админы могут запускать игры!")
        return

    if message.chat.id in active_games:
        bot.reply_to(message, "Игра уже запущена! Используйте /stopgame для остановки.")
        return

    game = MemeGame(message.chat.id)
    active_games[message.chat.id] = game
    game.start()

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработчик inline-кнопок"""
    if call.data == "start_memegame":
        start_memegame(call.message)
    elif call.data.startswith('rate_'):
        chat_id = call.message.chat.id
        if chat_id not in active_games:
            bot.answer_callback_query(call.id, "Игра уже завершена!")
            return

        _, user_id, score = call.data.split('_')
        rater_id = call.from_user.id
        success = active_games[chat_id].handle_rating(int(user_id), rater_id, int(score))
        
        if success:
            bot.answer_callback_query(call.id, f"Вы поставили оценку {score}")
        else:
            bot.answer_callback_query(call.id, "Вы уже голосовали за этот мем или не участвуете в игре!")

@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_messages(message):
    """Обрабатывает текстовые сообщения"""
    if message.chat.id in active_games:
        active_games[message.chat.id].handle_response(message)

if __name__ == '__main__':
    print("Бот запущен!")
    bot.polling(none_stop=True)