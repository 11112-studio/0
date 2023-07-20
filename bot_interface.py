import vk_api
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from help import help_text
from my_safe import community_token, access_token, db_url_object
from core import VkTools
from data_base import user_exists_in_db, save_users

engine = create_engine(db_url_object)
session = Session(engine)


class BotInterface:

    def __init__(self, community_token, access_token):
        self.vk = vk_api.VkApi(token=community_token)
        self.vk_tools = VkTools(access_token)
        self.longpoll = VkLongPoll(self.vk)
        self.params = {}
        self.worksheets = []
        self.count = 10
        self.offset = 0

    def search_worksheets(self):
        profiles = self.vk_tools.search_users(self.params, self.offset, self.count)
        self.offset += self.count
        return profiles

    def search_process(self, user_id):
        worksheets = []
        if not worksheets:
            worksheets = self.search_worksheets()
            print(f'в наличии: {worksheets}')

        new_worksheets = [] # список новых анкет

        while not new_worksheets:
            for worksheet in worksheets:
                if user_exists_in_db(engine, self.params['id'], worksheet['id']):
                    continue
                else:
                    new_worksheets.append(worksheet)
            # если нет анкет то получаем еще
            if not new_worksheets:
                worksheets = self.search_worksheets()

        user = new_worksheets.pop()
        photos_user = self.vk_tools.get_photos(user['id'])
        user_url = f"https://vk.com/id{user['id']}"
        attachments = []
        for num, photo in enumerate(photos_user[:3]):
            attachments.append(f'photo{photo["owner_id"]}_{photo["id"]}')
            if num == 2:
                break
        self.message_send(user_id,
                          (f'Встречайте {user["name"]}. '
                           f'Ссылка на профиль: {user_url}'),
                          attachment=','.join(attachments))
        save_users(engine, self.params['id'], user['id'])

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send', {'user_id': user_id,
                                         'message': message,
                                         'attachment': attachment,
                                         'random_id': get_random_id()})

    def change_search_params(self, user_id):
        params = self.vk_tools.get_profile_info(user_id)
        params_received = True
        for param in params:
            if params[param] is None:
                params_received = False
                if param == 'sex':
                    self.message_send(user_id, 'Давайте уточним ваш пол? Ответьте "да" или "нет".')
                    self.get_response(user_id, 'sex')

                elif param == 'bdate':
                    self.message_send(user_id, 'Давайте изменим дату рождения? Ответьте "да" или "нет".')
                    self.get_response(user_id, 'bdate')

                elif param == 'сity':
                    self.message_send(user_id, 'Изменить город? Ответьте "да" или "нет".')
                    self.get_response(user_id, 'city')

                else:
                    self.message_send(user_id, f'Изменить ваш {param} в поисковых параметрах? Ответьте "да" или "нет".')
                    self.get_response(user_id, param)

        if params_received:
            self.message_send(user_id, 'Параметры поиска получены')
            return self.params

    def get_response(self, user_id, parameter):
        while True:
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.user_id == user_id:
                    if event.text.lower() == 'да':
                        if parameter == 'sex':
                            print(self.params['sex'])
                            self.message_send(user_id, 'Введите новое значение для пола только число'
                                                       '(1 - женский, 2 - мужской):')
                            self.update_sex(user_id)
                            self.search_worksheets()
                            return
                        elif parameter == 'bdate':
                            self.message_send(user_id, 'Введите вашу дату рождения (в формате ДД.ММ.ГГГГ):')
                            self.update_bdate(user_id)
                            self.search_worksheets()
                            return
                        elif parameter == 'city':
                            self.message_send(user_id, 'Введите название города для поиска: ')
                            self.update_city(user_id)
                            self.search_worksheets()
                            return
                        break
                    elif event.text.lower() == 'нет':
                        self.message_send(user_id, f'Параметр {parameter} остается без изменений.')
                        break
                    elif event.text.lower() == '':
                        self.message_send(user_id, f'Неизвестная команда.')
                        break


    def update_sex(self, user_id):
        for response_event in self.longpoll.listen():
            if (response_event.type == VkEventType.MESSAGE_NEW and response_event.to_me
                    and response_event.user_id == user_id):
                new_value = response_event.text.lower()
                while True:
                    if new_value == 'отмена':
                        self.message_send(user_id, 'Отменено изменение параметров поиска.')
                        return
                    elif new_value in ['1', '2']:
                        self.params['sex'] = new_value
                        self.message_send(user_id, f"Параметр пола успешно изменен на: {new_value}")
                        print(self.params['sex'])
                        return
                    else:
                        self.message_send(user_id, f"Некорректное значение для пола: {new_value}")
                        break

    def is_valid_date(self, bdate):
        try:
            datetime.datetime.strptime(bdate, '%d.%m.%Y')
            return True
        except ValueError:
            return False

    def update_bdate(self, user_id):
        while True:
            for response_event in self.longpoll.listen():
                if (response_event.type == VkEventType.MESSAGE_NEW and response_event.to_me
                        and response_event.user_id == user_id):
                    bdate = response_event.text.lower()
                    if bdate == 'отмена':
                        self.message_send(user_id, 'Отменено изменение параметров поиска.')
                        return  # Выход из метода после отмены команды
                    elif self.is_valid_date(bdate):
                        self.params['bdate'] = bdate
                        self.message_send(user_id, f"Параметр даты рождения успешно изменен на: {bdate}")
                        return  # Выход из метода после успешного изменения параметра
                    else:
                        self.message_send(user_id, f"Некорректное значение для даты рождения.\n"
                                                   f"Повторите ввод или отмените команду, написав 'отмена'")
                        break  # Повтор цикла для запроса правильного значения

    def update_city(self, user_id):
        for response_event in self.longpoll.listen():
            if (response_event.type == VkEventType.MESSAGE_NEW and response_event.to_me
                    and response_event.user_id == user_id):
                if response_event.text.lower() == 'отмена':
                    self.message_send(user_id, 'Отменено изменение параметров поиска.')
                    break
                else:
                    city_name = response_event.text
                    if len(city_name) < 2:
                        self.message_send(user_id,
                                          'Слишком короткое название города. '
                                          'Попробуйте еще раз или отмените команду.')
                        break
                    city_id = self.vk_tools.get_city_id(city_name)
                    if city_id:
                        self.params['city'] = city_id
                        self.message_send(user_id, f"Город успешно изменен на: {city_name}")
                        break
                    else:
                        self.message_send(user_id,
                                          f"Город '{city_name}' не найден. Проверьте правильность "
                                          f"ввода или отмените команду.")
                        break

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()
                if command == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.change_search_params(event.user_id)
                    self.message_send(event.user_id, f'Здравствуй {self.params["name"]} '
                                                     f'введи команду "поиск" или "помощь')
                elif command == 'поиск':
                    if not self.params:
                        self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.search_process(event.user_id)
                elif command == 'пока':
                    self.message_send(event.user_id, 'пока')
                elif command == 'другой город':
                    self.message_send(event.user_id, 'Хотите сменить город поиска? да/нет')
                    self.get_response(event.user_id, 'city')
                elif command == 'дата рождения':
                    self.message_send(event.user_id, 'Хотите сменить дату рождения? да/нет')
                    self.get_response(event.user_id, 'bdate')
                elif command == 'помощь':
                    self.message_send(event.user_id, help_text)

                else:
                    self.message_send(event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot = BotInterface(community_token, access_token)
    bot.event_handler()
