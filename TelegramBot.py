from io import BytesIO
import numpy as np
import cv2
from telebot import telebot, types
import openai
import unicodedata

NAME = 'ArtConverterSendBot'
openai.api_key = "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"
TOKEN = '6474256953:AAFj6eNjHGgwPgPCZixF3tE00qlTgyKUGu4'
bot = telebot.TeleBot(TOKEN)

#
list_buttons = ['/start', 'TRANSLATE', 'REMOVE COLOR']
keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
keyboardStart = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
#
button_translate = telebot.types.KeyboardButton(list_buttons[1])
convert_photo = telebot.types.KeyboardButton(list_buttons[2])
#
keyboard.add(button_translate, convert_photo)

# Словарь для отслеживания состояний пользователей
user_state = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_state[message.chat.id] = None # Устанавливаем начальное состояние None

    user_name = message.from_user.first_name
    Introductory_text = f"""Hello <b>{user_name}</b>! 
I have TWO OPTIONS for you. 
<b>The first option:</b> 
    I can translate text from <b>English to Ukrainian</b> and vice versa, just enter the text, and I'll provide you with the translation.
<b>The second option:</b>
    I can remove all colors from an image, you just need to send me the picture."""
    bot.send_message(message.chat.id, text=Introductory_text, reply_markup=keyboard, parse_mode='HTML')


@bot.message_handler(func=lambda message: message.text in list_buttons)
def handle_buttons(message):
    user_id = message.from_user.id
    user_state[user_id] = message.text  # Устанавливаем текущее состояние

    if message.text == list_buttons[1]:
        bot.send_message(message.chat.id,
    """Send me the text for translation, depending on the language of your message. I will generate the translation.""")

    elif message.text == list_buttons[2]:
        bot.send_message(message.chat.id, "Send me a color image for processing.")


@bot.message_handler(content_types=['text'])
def send_translate(message):
    user_id = message.from_user.id
    if user_state.get(user_id) == list_buttons[1]:
        # Получаем текст сообщения от пользователя
        bot.send_message(message.chat.id, "Translating the text...")
        user_message = message.text
        # Обработка сообщения с помощью функции
        if user_message not in list_buttons:
            response = make_response_gpt(user_message)
            bot.send_message(user_id, response)

        user_state[user_id] = None
    elif user_state.get(user_id) == list_buttons[2]:
        bot.send_message(message.chat.id,
                         """I did not receive the image. Please send me a file in JPEG, PNG, or another format.""")
    else:   bot.send_message(message.chat.id, "Please choose an option for processing the information.")


#----------------------------------------TRANSLATE----------------------------------------
def has_cyrillic(unidata):
    return any('CYRILLIC' in unicodedata.name(char) for char in unidata)

def has_latin(unidata):
    return any('LATIN' in unicodedata.name(char) for char in unidata)

def make_response_gpt(message):
    if has_latin(message) and isinstance(message, str):
        user_message = f'Переклади на Украiнську: {message}'

    elif has_cyrillic(message) and isinstance(message, str):
        user_message = f'Translate to English: {message}'

    else: user_message = 'I did not receive the text. '

    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[{"role": 'user', "content": user_message}],
      temperature=0,
      max_tokens=256
    )
    return response.choices[0].message['content']

#-------------------------------------COLOR TO GRAY---------------------------------------

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id

    if user_state.get(user_id) == list_buttons[2]:
        bot.send_message(message.chat.id, "Processing the image....")
        # Получаем информацию о файле изображения
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        # Загружаем изображение с серверов Telegram
        image_stream = BytesIO(bot.download_file(file_path))
        image = cv2.imdecode(np.frombuffer(image_stream.read(), dtype=np.uint8), -1)
        # Преобразуем изображение в черно-белый формат
        black_and_white_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Конвертируем изображение в байты формата JPEG
        _, ascii_image_bytes = cv2.imencode('.jpg', np.array(black_and_white_image))
        # Отправляем обработанное ASCII-изображение обратно пользователю
        bot.send_photo(message.chat.id, photo=ascii_image_bytes.tobytes(), caption="BLACK|WHITE")

        # Очищаем состояние после обработки
        user_state[user_id] = None

    elif user_state.get(user_id) == list_buttons[1]:
        bot.send_message(message.chat.id, """Please select the option <<REMOVE COLOR>>..""")

    else:
        bot.send_message(message.chat.id,
                 """This is a joke, it's difficult for me to construct a sentence from these words.""")


if __name__ == '__main__':
    bot.polling(none_stop=True)









