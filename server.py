from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1030494/a947f3d4e2bce84221ae', '1030494/2948641ff2f33e26b725'],
    'нью-йорк': ['1030494/6699365299eeeca58801', '997614/ad55b500037a9f30252c'],
    'париж': ['997614/e9f3dcf28d2c48a9512c', '1656841/e42df0dc56a2cb6872ba']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    res['response']['buttons'] = []
    user_id = req['session']['user_id']
    if 'помощь' in req['request']['original_utterance'].lower():
        res['response']['text'] = 'Данный навык играет в угадайку городов по картинке'
        res['response']['buttons'] = [{
            'title': 'Продолжить',
            'hide': True
        }]
        return

    if 'что ты умеешь' in req['request']['original_utterance'].lower():
        res['response']['text'] = 'Данный навык умеет играть с тобой в угадайку с городами по картинке'
        res['response']['buttons'] = [{
            'title': 'Продолжить',
            'hide': True
        }]
        return

    if 'продолжить' in req['request']['original_utterance'].lower():
        res['response']['text'] = 'Продолжаем. Возвращаемся к моей фразе, не связанной с пояснительной информацией)'
        return
    if 'покажи город на карте' in req['request']['original_utterance'].lower():
        if len(
                sessionStorage[user_id]['guessed_cities']) != 3:
            res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Будешь угадывать следующий город?'
            res['response']['buttons'].append(
                {
                    'title': 'Да',
                    'hide': True
                })
            res['response']['buttons'].append(
                {
                    'title': 'Нет',
                    'hide': True
                })
        else:
            res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Красава! Отгадал все города'
            sessionStorage[user_id]['game_started'] = False
            res['response']['end_session'] = True
        return

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }
        return

    if sessionStorage[user_id]['first_name'] is None:
        name_user = get_first_name(req)
        if name_user is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        else:
            sessionStorage[user_id]['first_name'] = name_user.capitalize()
            sessionStorage[user_id]['guessed_cities'] = []
            res['response']['text'] = f'Приятно познакомиться, {sessionStorage[user_id]["first_name"]}. ' \
                                      f'Я Алиса. Отгадаешь город по фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
    else:
        if not sessionStorage[user_id]['game_started']:
            if 'да' in req['request']['nlu']['tokens']:
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Ты лучший, отгадал все города!'
                    sessionStorage[user_id]['game_started'] = False
                    res['response']['end_session'] = True
                else:
                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)
            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Ну и ладно!'
                sessionStorage[user_id]['game_started'] = False
                res['response']['end_session'] = True
            else:
                if len(sessionStorage[user_id]['guessed_cities']) == 3:
                    res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Ты лучший, отгадал все города!'
                    sessionStorage[user_id]['game_started'] = False
                    res['response']['end_session'] = True
                else:
                    res['response'][
                        'text'] = f'{sessionStorage[user_id]["first_name"]}, Не поняла ответа! Так да или нет?'
                    res['response']['buttons'] = [
                        {
                            'title': 'Да',
                            'hide': True
                        },
                        {
                            'title': 'Нет',
                            'hide': True
                        }
                    ]
        else:
            play_game(res, req)
    res['response']['buttons'].append({
        'title': 'Помощь',
        'hide': True
    })

    res['response']['buttons'].append({
        'title': 'Что ты умеешь?',
        'hide': True
    })


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']
    if len(sessionStorage[user_id]['guessed_cities']) == 3:
        res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Ты лучший, отгадал все города!'
        sessionStorage[user_id]['game_started'] = False
        res['response']['end_session'] = True
        return

    if attempt == 1:
        city = random.choice(list(cities))
        while city in sessionStorage[user_id]['guessed_cities']:
            city = random.choice(list(cities))

        sessionStorage[user_id]['city'] = city
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]
        res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Тогда сыграем!'
    else:
        city = sessionStorage[user_id]['city']
        if get_city(req) == city:
            if len(sessionStorage[user_id]['guessed_cities']) < 2:
                res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Правильно! Сыграем ещё?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True
                    },
                    {
                        'title': 'Нет',
                        'hide': True
                    },

                    {'title': 'Покажи город на карте',
                     'hide': True,
                     'url': f'https://yandex.ru/maps/?mode=search&text={city}'}
                ]
            else:
                res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, Лучший! Отгадал все города'
                res['response']['buttons'].append(
                    {'title': 'Покажи город на карте',
                     'hide': True,
                     'url': f'https://yandex.ru/maps/?mode=search&text={city}'}
                )
            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = False
            return
        else:
            if attempt == 3:
                res['response'][
                    'text'] = f'{sessionStorage[user_id]["first_name"]}, Вы пытались. Это {city.title()}. Сыграем ещё?'

                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card'][
                    'title'] = f'{sessionStorage[user_id]["first_name"]}, Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]
                res['response']['text'] = f'{sessionStorage[user_id]["first_name"]}, А вот и не угадал!'
    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
