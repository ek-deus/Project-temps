# импорт токенов для бота и АПИ ФНС из файла конфигурации, а также необходимых модулей
from config import Bot_Token, API_Token
import requests
import json
import os.path
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


# преобразовываем полученную информацию об организации из словаря в список для красивого вывода
def facts_to_str(data):
    facts = list()
    for key, value in data.items():
        facts.append('{} - {}'.format(key, value))
    return "\n".join(facts).join(['\n', '\n'])


# функция для обработки команды /start
def start(update, context):
    first_name = update.message.chat.first_name
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text=f"Добрый день {first_name}, рад видеть Вас! \n\n"
                                                   f"Я могу проверить, принадлежит ли введенный Вами ИНН организации и выдать краткую информацию о ней. \n\n"
                                                   f"Введите ИНН для проверки: \n")


# функция для обработки ввода ИНН
def text(update, context):
    chat = update.effective_chat
    inn = update.message.text
    context.bot.send_message(chat_id=chat.id, text=f"Проверяю введенный ИНН '{inn}'...")
    # проверка что ИНН вводится правильно - 10 знаков, только цифры и сам ИНН корректен
    if len(inn) == 10 and inn.isdigit() and check_valid_inn(inn):
        inn_info = get_inn_info(inn)
        update.message.reply_text("ИНН указан корректно и принадлежит юридическому лицу, краткая информация об организации: "
                                  "{}".format(facts_to_str(inn_info['items'][0]['ЮЛ'])))
        context.bot.send_message(chat_id=chat.id, text=f"\n Введите следующий ИНН для проверки")
    else:
        if not check_valid_inn(inn):
            context.bot.send_message(chat_id=chat.id, text=f"Введен некорректный ИНН, такой организации не существует. \n"
                                                           f"Введите ИНН в правильном формате: последовательность из 10 арабских цифр без пробелов.")


# функция проверки корректности введенного ИНН
def check_valid_inn(inn):
    inn_key = [2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
    key_sum = 0
    for num in range(10):
        key_sum += inn_key[num] * int(inn[num])
    control = key_sum % 11
    if control > 9:
        control = control % 10
    if control == int(inn[9]):
        return True
    else:
        return False


# функция для сбора данных с API ФНС, которая проверяет, если нет файла с данными по организации, то обращается к ФНС и сохраняет файл с данными по организации
def get_inn_info(inn):
    if not os.path.isfile(f'{inn}.json'): # если файла нет, то считываем информацию у ФНС
        url = 'https://api-fns.ru/api/search' # в бесплатной версии здесь доступно 8 видов запросов по 100 раз каждого запроса для одного API_token
        params = dict(q=inn, key=API_Token)
        response = requests.get(url, params=params)
        inn_info = response.json()
        with open(f'{inn}.json', 'w', encoding='utf-8') as outfile:
            json.dump(inn_info, outfile, ensure_ascii=False, indent=4)
    else:
        with open(f'{inn}.json', 'r', encoding='utf-8') as outfile:  # если файл с таким ИНН уже существует - открываем файл на чтение (сделал так из-за ограниченного количества запросов)
            inn_info = json.load(outfile)
    return inn_info


# здесь должна быть функция для обработки команды /help
def help(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text=f'Обработка команды help в разработке')


# функция для обработки ошибок
def error(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text=f'Произошла ошибка')


# основная функция
def main():

    # создаем объект updater, который автоматически создает объект dispatcher
    updater = Updater(Bot_Token, use_context=True)
    dispatcher = updater.dispatcher
    # добавляем обработку команд start и help
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    # добавляем обработчика текста (не команд)
    dispatcher.add_handler(MessageHandler(Filters.text, text))
    # добавляем обработчика ошибок
    dispatcher.add_error_handler(error)
    # запускаем бота на локальной машине
    updater.start_polling()
    # бот работает, пока не нажмем Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
