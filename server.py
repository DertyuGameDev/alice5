# импортируем библиотеки
import logging
from flask import Flask, request, jsonify
import pymorphy3

morph = pymorphy3.MorphAnalyzer()
app = Flask(__name__)

# Устанавливаем уровень логирования
logging.basicConfig(level=logging.INFO)

# Создадим словарь, чтобы для каждой сессии общения
# с навыком хранились подсказки, которые видел пользователь.
# Это поможет нам немного разнообразить подсказки ответов
# (buttons в JSON ответа).
# Когда новый пользователь напишет нашему навыку,
# то мы сохраним в этот словарь запись формата
# sessionStorage[user_id] = {'suggests': ["Не хочу.", "Не буду.", "Отстань!" ]}
# Такая запись говорит, что мы показали пользователю эти три подсказки.
# Когда он откажется купить слона,
# то мы уберем одну подсказку. Как будто что-то меняется :)
sessionStorage = {}
sessionStorage["cur_animal"] = 'слон'


@app.route('/post', methods=['POST'])
def main():
    # Функция получает тело запроса и возвращает ответ.
    # Внутри функции доступен request.json - это JSON,
    # который отправила нам Алиса в запросе POST

    logging.info(f'Request: {request.json!r}')

    # Начинаем формировать ответ, согласно документации
    # мы собираем словарь, который потом отдадим Алисе
    response = {
        "session": request.json["session"],
        "version": request.json["version"],
        "response": {
            "end_session": False
        }
    }

    logging.info(f'Response:  {response!r}')

    # Отправляем request.json и response в функцию handle_dialog.
    # Она сформирует оставшиеся поля JSON, которые отвечают
    # непосредственно за ведение диалога
    handle_dialog(request.json, response)

    return jsonify(response)


def handle_dialog(request_dict, response):
    user_id = request_dict['session']['user_id']

    if request_dict['session']['new']:  # кнопки

        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу!",
                "Не буду!",
                "Не куплю!"
            ]
        }
        animal = morph.parse(sessionStorage["cur_animal"])[0].inflect({'gent'}).word
        response['response']['text'] = f'Салюют! Купи {animal}!'
        response['response']['buttons'] = get_suggests(user_id)
        return

    else:
        if request_dict['request']['original_utterance'].lower() in ['ладно', 'куплю', 'покупаю', 'хорошо',
                                                                     'я покупаю', 'я куплю', 'я куплю ёпта', 'давай',
                                                                     'ну давай', 'ща отберу, дай сюда']:
            # пользователь согласился
            match sessionStorage["cur_animal"]:
                case 'слон':
                    text_rabbit = "А теперь купи кролика)"
                case 'кролик':
                    text_rabbit = ""
            animal = morph.parse(sessionStorage["cur_animal"])[0].inflect({'gent'}).word
            response['response'][
                'text'] = f'{animal} можно найти на Яндекс.Маркете! ' \
                          f'\nhttps://market.yandex.ru/search?text={sessionStorage["cur_animal"]}\n\n ' \
                          f'{text_rabbit}'

            if sessionStorage["cur_animal"] == 'кролик':
                response['response']['end_session'] = True
                sessionStorage["cur_animal"] = 'слон'

            else:
                sessionStorage["cur_animal"] = 'кролик'
                sessionStorage[user_id] = {
                    'suggests': [
                        "Не хочу!",
                        "Неее!",
                        "Не куплю!"
                    ]
                }
                response['response']['buttons'] = get_suggests(user_id)
            return

        elif request_dict['request']['original_utterance'].lower() in ['помощь']:
            text_animal_buy = morph.parse(sessionStorage["cur_animal"])[0].inflect({'gent'}).word
            response['response'][
                'text'] = f'Навык пытается убедить купить {text_animal_buy}. \n' \
                          'Для согласия можно написать: "ладно", "куплю", "покупаю", "хорошо".'
            response['response']['buttons'] = get_suggests(user_id)

        elif 'что ты умеешь' in request_dict['request']['original_utterance'].lower():
            text_animal_buy = morph.parse(sessionStorage["cur_animal"])[0].inflect({'gent'}).word
            response['response'][
                'text'] = f"Я умею настойчиво убеждать купить {text_animal_buy}, купи {text_animal_buy}!"
            response['response']['buttons'] = get_suggests(user_id)

        else:
            text_animal_buy = morph.parse(sessionStorage["cur_animal"])[0].inflect({'gent'}).word
            response['response']['text'] = \
                f"Все говорят '{request_dict['request']['original_utterance']}', а ты купи {text_animal_buy}!"
            response['response']['buttons'] = get_suggests(user_id)


def get_suggests(user_id):
    """ функция возвращает подсказки для пользователя """
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    # Убираем первую подсказку, чтобы подсказки менялись каждый раз, будут показаны другие
    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    suggests.append({
        'title': 'Помощь',
        'hide': True
    })

    suggests.append({
        'title': 'Что ты умеешь?',
        'hide': True
    })

    # предлагаем подсказку со ссылкой на Яндекс.Маркет.
    if len(suggests) < 4:
        match sessionStorage["cur_animal"]:
            case 'слон':
                suggests.append({
                    "title": "Ладно",
                    "hide": True
                })
            case 'кролик':
                suggests.append({
                    "title": "Ладно",
                    "hide": True,
                    "url": "https://market.yandex.ru/search?text=кролик"
                })
    return suggests


if __name__ == "__main__":
    app.run()

# xTunnel -k 04554c4c74204ea984c2d743e011edec
# xTunnel 5000
