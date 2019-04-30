from __future__ import unicode_literals
from json import dump
from random import randint, choice
from copy import deepcopy
from re import findall, match
import logging

logging.basicConfig(level=logging.DEBUG)


class NoCellsError(Exception):
    pass


class WinnerError(Exception):
    pass


class ShipBattle:
    def __init__(self):
        self.reversed_alphabet = {j: i for i, j in enumerate(ALPHABET)}
        self.field = [[0 for _ in range(10)] for _ in range(10)]

    def check_cell(self, cell, first_cell=False):
        x, y = cell
        count = 0
        possible_cells = [(1, 1), (-1, -1), (0, 1), (1, 0), (-1, 0), (0, -1), (-1, 1), (1, -1)]
        for possible in possible_cells:
            if -1 < x + possible[0] < 10 and -1 < y + possible[1] < 10:
                if self.field[y + possible[1]][x + possible[0]] == 1:
                    count += 1

        if (count < 2 and not first_cell) or (first_cell and count == 0):
            return True
        return False

    def place_ships(self):
        for ship in SHIPS:
            while True:
                new_field = deepcopy(self.field)
                intersection = False
                direction = choice([True, False])

                if direction:
                    random_coors = (randint(0, 10 - ship), randint(0, 9))
                    for x in range(random_coors[0], random_coors[0] + ship):
                        if x == random_coors[0]:
                            passed_cell = self.check_cell((x, random_coors[1]), True)
                        else:
                            passed_cell = self.check_cell((x, random_coors[1]), False)

                        if not passed_cell:
                            intersection = True
                            break
                        else:
                            new_field[random_coors[1]][x] = 1

                else:
                    random_coors = (randint(0, 9), randint(0, 10 - ship))
                    for y in range(random_coors[1], random_coors[1] + ship):
                        if y == random_coors[1]:
                            passed_cell = self.check_cell((random_coors[0], y), True)
                        else:
                            passed_cell = self.check_cell((random_coors[0], y), False)

                        if not passed_cell:
                            intersection = True
                            break
                        else:
                            new_field[y][random_coors[0]] = 1

                if not intersection:
                    self.field = deepcopy(new_field)
                    break

    def save_to_map_json(self):
        with open('map.json', 'w', encoding='utf8') as file:
            dump({"maps": self.field}, file)


SHIPS = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
LIFE = sum(SHIPS)
ALPHABET = ['а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'к']

KILLED_WORDS = ['убила', 'убил', 'потопила', 'потоплен', 'потопил']
INJURED_WORDS = ['попала', 'попал', 'попадание', 'ранил', 'ранила', 'ранен']
MISSED_WORDS = ['мимо', 'промах', 'промазала', 'промазал']
CANCEL_WORD = ['отмена', 'отменить', 'отменитьход', 'назад']
ENDING_WORDS = ['новаяигра', 'выход', 'начатьновуюигру', 'начать']


ALL_WORDS = KILLED_WORDS+INJURED_WORDS+MISSED_WORDS+CANCEL_WORD+ENDING_WORDS

PHRASES_FOR_ALICES_TURN = ['Пожалуйста, не жульничайте, я контролирую игру.', 'Помоему, сейчас не ваш ход.',
                           'Со мной такое не прокатит. Сейчас мой ход.', 'Может вы не будете меня обманывать?',
                           'Давайте я забуду это, а вы ответите еще раз.']

PHRASES_FOR_USERS_TURN = ['Сейчас ваш ход, не надо поддаваться.',
                          'Может вы что-то перепутали? Сейчас вы атакуете.',
                          'Я конечно не против, но давайте играть по правилам', 'Не люблю лёгкие победы...']


def handle_dialog(request, response, user_storage):
    # response.user_id
    if request.is_new_session:
        ship_battle = ShipBattle()
        ship_battle.place_ships()

        user_storage = {
            "user_id": request.user_id,
            "users_turn": True,
            "alice_life": LIFE,
            "users_ships": [4, 3, 3, 2, 2, 2, 1, 1, 1, 1],
            "users_life": LIFE,
            "Target": [],
            "alices_matrix": ship_battle.field,
            "users_matrix": [[0 for _ in range(10)] for _ in range(10)],
            "cheating_stage": 0,
            "last_turn": None,
            "last_turn_field": [],
            "directions": [[0, 1], [1, 0], [-1, 0], [0, -1]]
        }
        global backup_turn
        backup_turn = user_storage

        response.set_text('Привет! Играем в морской бой. Каждая клетка обозначается алфавитной буквой по горизонтали '
                          '(от "А" до "К", исключая "Ё" и "Й", слева направо) и цифрой по вертикали '
                          '(от 1 до 10 сверху вниз). Мои корабли уже расставлены. По вашей готовности атакуйте. Чтобы '
                          'провести атаку скажите или введите координаты.'
                          'Для отмены действия наберите "Отменить"'
                          'Для начала новой игры наберите "Новая игра" или "Выход"')
        return response, user_storage

    user_message = request.command.lower().strip().replace(' ', '')
    try_to_make_coor = ''.join(findall(r'\w+', user_message))
    matched = match('\w\d0*', try_to_make_coor)

    try:
        if user_message in ALL_WORDS:

            if user_message in CANCEL_WORD:
                try:
                    user_storage = backup_turn
                    user_storage["users_turn"] = False
                    # user_storage["alices_matrix"] = user_storage["last_turn_field"][0]
                    # user_storage["users_matrix"] = user_storage["last_turn_field"][1]
                    response.set_text('Предыдущий ваш ход и ход Алисы отменены.')
                except Exception as e:
                    print(e)
                    response.set_text('Невозможно отменить ход')
            elif user_message in ENDING_WORDS:
                user_storage = end(request, response)
            elif not user_storage["users_turn"]:
                backup_turn = user_storage
                if user_message in KILLED_WORDS:
                    alice_answer = alice_fires(user_storage, "убил")
                    response.set_text(alice_answer)
                elif user_message in INJURED_WORDS:
                    alice_answer = alice_fires(user_storage, "ранил")
                    response.set_text(alice_answer)
                elif user_message in MISSED_WORDS:
                    alice_answer = alice_fires(user_storage, "мимо")
                    response.set_text(alice_answer)
                elif user_message in CANCEL_WORD:
                    try:
                        user_storage["alices_matrix"] = user_storage["last_turn_field"][0]
                        user_storage["users_matrix"] = user_storage["last_turn_field"][1]
                        response.set_text('Предыдущий ваш ход и ход Алисы отменены.')
                        user_storage["last_turn_field"] = []
                    except IndexError:
                        response.set_text('Невозможно отменить ход')
                elif user_message in ENDING_WORDS:
                    user_storage = end(request, response)
            else:
                response.set_text(choice(PHRASES_FOR_USERS_TURN))
        elif matched is not None:
            if user_storage["users_turn"]:
                letter = matched.group(0)[0]
                number = int(matched.group(0)[1:])
                if 0 < number < 11 and letter in ALPHABET:
                    # user_storage["last_turn_field"] = [user_storage["alices_matrix"], user_storage["users_matrix"]]
                    result_of_fire = user_fires(user_storage["alices_matrix"], (ALPHABET.index(letter), number - 1))
                    if result_of_fire == 'Мимо':
                        user_storage["users_turn"] = False
                        alice_answer = alice_fires(user_storage, "remember")
                        response.set_text('Мимо. Я хожу. ' + alice_answer)
                    else:
                        user_storage["alice_life"] -= 1
                        if user_storage["alice_life"] < 1:
                            response.set_text("Вы победили меня, поздравляю! Спасибо за игру!")
                            user_storage = end(request, response)
                        else:
                            response.set_text(result_of_fire)
                else:
                    response.set_text(
                        "Координаты клетки обозначаются буквой (от А до К, исключая Ё и Й) "
                        "и числом (от 1 до 10) для поля 10 на 10 клеток. Пример - А1.")
            else:
                response.set_text(choice(PHRASES_FOR_ALICES_TURN))

        else:
            response.set_text("Простите, но я вас не поняла.")

    except NoCellsError:
        response.set_text("Я простреляла все клетки, так что считайте, что я победила.")
        user_storage = end(request, response)

    except WinnerError:
        response.set_text("Я выиграла, спасибо за игру!")
        user_storage = end(request, response)

    return response, user_storage


def alice_fires(user_data, happened):
    def random_fire():
        cells_for_fire = []
        for _y in range(10):
            for _x in range(10):
                if user_data["users_matrix"][_y][_x] == 0:
                    cells_for_fire.append((_x, _y))
        if len(cells_for_fire) == 0:
            raise NoCellsError
        turn = choice(cells_for_fire)
        # user_data["last_turn_field"][0] = user_data["alices_matrix"]
        user_data["last_turn"] = turn
        return "{}{}".format(ALPHABET[turn[0]].upper(), turn[1] + 1)

    def clever_fire():
        if len(user_data["Target"]) > 1:
            cell_1 = user_data["Target"][0]
            cell_2 = user_data["Target"][1]
            cells_to_del = []
            if cell_1[0] == cell_2[0]:
                for direction in user_data["directions"]:
                    if direction in [[1, 0], [-1, 0]]:
                        cells_to_del.append(direction)
            elif cell_1[1] == cell_2[1]:
                for direction in user_data["directions"]:
                    if direction in [[0, 1], [0, -1]]:
                        cells_to_del.append(direction)
            for cell_to_del in cells_to_del:
                user_data["directions"].remove(cell_to_del)

        chosen = False
        directions_to_del = []
        cells_to_check = {}
        for possible_direction in user_data["directions"]:
            for _cell in user_data["Target"]:
                _x = possible_direction[0] + _cell[0]
                _y = possible_direction[1] + _cell[1]

                if 0 <= _x <= 9 and 0 <= _y <= 9:

                    if user_data["users_matrix"][_y][_x] == 2:
                        directions_to_del.append(possible_direction)
                        break
                    elif user_data["users_matrix"][_y][_x] == 0:
                        cells_to_check[(_x, _y)] = possible_direction
                        chosen = True
                else:
                    directions_to_del.append(possible_direction)
            for direction in directions_to_del:
                try:
                    user_data["directions"].remove(direction)
                except ValueError:
                    pass

        if chosen:
            for _cell in cells_to_check:
                if cells_to_check[_cell] in user_data["directions"]:
                    x, y = _cell
                    user_data['last_turn'] = _cell

                    user_data["last_turn_alice"] = [_cell, 0]
                    return "{}{}".format(ALPHABET[_cell[0]].upper(), _cell[1] + 1)

        elif not chosen and not user_data["directions"]:
            user_data["directions"] = [[0, 1], [1, 0], [-1, 0], [0, -1]]
            try_fire = random_fire()
            return "Судя по всему, корабль уже потоплен. " + try_fire

    def delete_ship():
        for cell in user_data["Target"]:
            x, y = cell

            possible_cells = [(1, 1), (-1, -1), (0, 1), (1, 0), (-1, 0), (0, -1), (-1, 1), (1, -1), (0, 0)]
            for possible in possible_cells:
                if -1 < x + possible[0] < 10 and -1 < y + possible[1] < 10:
                    user_data["users_matrix"][y + possible[1]][x + possible[0]] = 2
        user_data["users_ships"].remove(len(user_data["Target"]))
        user_data["Target"] = []
        user_data["directions"] = [[0, 1], [1, 0], [-1, 0], [0, -1]]

    if happened == "убил" or happened == "ранил":
        if not (len(user_data["Target"]) + 1 in user_data["users_ships"]):
            delete_ship()
            return "Максимальный размер корабля на данный момент {} клетки. ".format(max(user_data["users_ships"]))

        user_data["users_life"] -= 1
        user_data["cheating_stage"] = 0

        if user_data["users_life"] < 1:
            raise WinnerError

    if happened == "убил":
        user_data["last_turn_field"] = [user_data["alices_matrix"], user_data["users_matrix"]]
        user_data["Target"].append(user_data["last_turn"])
        delete_ship()
        answer = random_fire()

    elif happened == "ранил":
        user_data["Target"].append(user_data["last_turn"])
        x, y = user_data["last_turn"]
        user_data["users_matrix"][y][x] = 3

        answer = clever_fire()

    elif happened == "remember":
        if user_data["Target"]:
            answer = clever_fire()
        else:
            answer = random_fire()
    else:

        # user_data["last_turn_field"][1] = user_data["users_matrix"]

        user_data["users_turn"] = True

        x, y = user_data["last_turn"]
        user_data["users_matrix"][y][x] = 2

        user_data["cheating_stage"] += 1
        answer = 'Ваш ход.'

        if user_data["cheating_stage"] == 10:
            answer = 'Что-то мне не везет. Ваш ход.'
        elif user_data["cheating_stage"] == 20:
            answer = 'По теории вероятности я уже должна была попасть хотя бы раз. Ваш ход.'
        elif user_data["cheating_stage"] == 40:
            answer = 'Мне кажется, что вы играете не совсем честно.'
        elif user_data["cheating_stage"] == 60:
            answer = 'Моя гипотеза подтверждается с каждым моим промахом.'
        elif user_data["cheating_stage"] == 80:
            answer = 'Роботы в отличае от людей не умеют обманывать.'
        elif user_data["cheating_stage"] == 97:
            answer = 'Надеюсь, такая простая победа принесет вам хотя бы каплю удовольствия, ' \
                     'ведь моя задача заключается в том чтобы радовать людей и упрощать их жизнь'

    return answer


def user_fires(matrix, coord):
    x, y = coord
    output = 'Вы уже стреляли сюда'

    if matrix[y][x] == 0:
        output = 'Мимо'
        matrix[y][x] = 2

    elif matrix[y][x] == 1:
        matrix[y][x] = 3

        ship = [(x, y)]
        was = []

        while len(ship) > 0:
            sinking = True

            x, y = ship.pop(0)
            was.append((x, y))

            possible_cells = [(0, 1), (1, 0), (-1, 0), (0, -1)]

            for possible in possible_cells:
                if -1 < x + possible[0] < 10 and -1 < y + possible[1] < 10:
                    if (x + possible[0], y + possible[1]) not in was:
                        if matrix[y + possible[1]][x + possible[0]] == 3:
                            ship.append((x + possible[0], y + possible[1]))
                        elif matrix[y + possible[1]][x + possible[0]] == 1:
                            sinking = False
                            break

            if sinking:
                for cell in was:
                    matrix[cell[1]][cell[0]] = 2
                output = 'Потоплен'
            else:
                output = 'Ранен'

    return output


def end(request, response):
    ship_battle = ShipBattle()
    ship_battle.place_ships()

    user_storage = {
        "user_id": request.user_id,
        "users_turn": True,
        "alice_life": LIFE,

        "users_ships": [4, 3, 3, 2, 2, 2, 1, 1, 1, 1],

        "users_life": LIFE,
        "Target": [],
        "alices_matrix": ship_battle.field,
        "users_matrix": [[0 for _ in range(10)] for _ in range(10)],
        "cheating_stage": 0,
        "last_turn": None,

        # "last_turn_field": [],
        "directions": [(0, 1), (1, 0), (-1, 0), (0, -1)]
    }

    backup_turn = user_storage


    response.set_text(
        'Новая игра! Напомню правила. Каждая клетка обозначается алфавитной буквой по горизонтали '
        '(от "А" до "К", исключая "Ё" и "Й", слева направо) и цифрой по вертикали '
        '(от 1 до 10 сверху вниз). Мои корабли уже расставлены. По вашей готовности атакуйте. Чтобы '
        'провести атаку скажите или введите координаты.'
        'Для отмены действия наберите "Отменить"'
        'Для начала новой игры наберите "Новая игра" или "Выход"')

    return user_storage
