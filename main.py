import vk_api

# Инициализировать клиент VK API
vk_session = vk_api.VkApi('your_username', 'your_password')

# Войти в ВК
vk_session.auth()

# Create an API object
vk = vk_session.get_api()

# Создать объект API
users = vk.users.search(
    count=3,  # Number of users to retrieve
    age_from=18,  # Minimum age
    age_to=30,  # Maximum age
    sex=1,  # Female gender
    city=1,  # City ID
    status=1  # Single marital status
)

# Обработать результаты поиска
for user in users['items']:
    print(user['id'], user['first_name'], user['last_name'])

# Получить 3 самых популярных фотографии профиля для каждого пользователя
for user in users['items']:
    photos = vk.photos.get(
        owner_id=user['id'],
        album_id='profile',
        extended=1,  # Retrieve extended information about each photo
        count=3,  # Number of photos to retrieve
        rev=1  # Sort photos in reverse order by popularity
    )

    # Обработать фотографии
    for photo in photos['items']:
        print(photo['id'], photo['likes']['count'], photo['comments']['count'], photo['sizes'][0]['url'])

# Отправить фотографии и ссылку на найденного пользователя в чат или пользователю
for user in users['items']:
    for photo in photos['items']:
        attachment = f"photo{photo['owner_id']}_{photo['id']}"
        message = f"Found user: {user['first_name']} {user['last_name']}\n{attachment}"
        vk.messages.send(
            user_id='user_id',  # ID чата или пользователя для отправки сообщения
            message=message,
            attachment=attachment
        )
