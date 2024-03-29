from datetime import datetime
import vk_api
import pprint
from vk_api import ApiError
from my_safe import access_token


class VkTools:
    def __init__(self, access_token):
        self.api = vk_api.VkApi(token=access_token)

    def _bdate_toyear(self, bdate):
        user_year = bdate.split('.')[2] if bdate is not None else None
        now = datetime.now().year
        return now - int(user_year)

    def get_city_id(self, city_name):
        response = self.api.method('database.getCities', {
            'country_id': 1, 'q': city_name, 'need_all': 0, 'count': 1})
        cities = response['items']
        if cities:
            return cities[0]['id']
        else:
            return None

    def get_profile_info(self, user_id):

        try:
            info, = self.api.method('users.get',
                                    {'user_id': user_id,
                                     'fields': 'city,bdate,sex,relation,home_town'
                                     }
                                    )
        except ApiError as e:
            info = {}
            print(f'error = {e}')

        param = {
            'name': info.get('first_name', '') + ' ' + info.get('last_name', ''),
            'id': info.get('id'),
            'bdate': info.get('bdate'),
            'home_town': info.get('home_town'),
            'sex': info.get('sex'),
            'city': info.get('city', {}).get('id')
        }
        return param

    def search_users(self, params, offset, count):
        sex = params['sex']
        if sex == 1:
            sex = 2
        else:
            sex = 1
        city = params['city']
        bdate = params['bdate']
        age = self._bdate_toyear(bdate)
        age_from = age - 1
        age_to = age + 1
        offset = offset

        try:
            users_found = self.api.method('users.search', {
                'count': count,
                'offset': offset,
                'age_from': age_from,
                'age_to': age_to,
                'sex': sex,
                'city': city,
                'status': 6,
                'is_closed': False,
                'has_photo': 1
                }
                )
            users = users_found['items']
        except KeyError:
            return []
        res = []
        for user in users:
            if user['is_closed'] is False:
                res.append({'id': user['id'],
                            'name': user['first_name'] + ' ' + user['last_name']
                            }
                           )
        return res

    def get_photos(self, user_id):
        try:
            photos = self.api.method('photos.get',
                                     {'owner_id': user_id,
                                      'album_id': 'profile',
                                      'extended': 1,

                                      }
                                     )

        except ApiError as e:
            photos = {}
            print(f'error {e}')
            return photos

        result = [{'owner_id': photo['owner_id'],
                   'id': photo['id'],
                   'likes': photo['likes']['count'],
                   'comments': photo['comments']['count']}for photo in photos['items']]

        result.sort(key=lambda x: x['likes'] + x['comments'] * 10, reverse=True)

        return result


if __name__ == '__main__':
    bot = VkTools(access_token)
    params = bot.get_profile_info(268787373)
    users = bot.search_users(params, offset=0, count=15)
    user = users.pop()
    photos = bot.get_photos(user['id'])
    # print(bot.get_photos(users[2]['id']))x
    # pprint.pprint(bot.get_photos(users[2]['id']))
    pprint.pprint(params)
