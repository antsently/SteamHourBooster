import ctypes
import datetime
import json
import os
import requests
import steam.client

CONFIG_FILE = "config.json"

# Функция для загрузки конфигурации из файла
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="UTF-8") as file:
            try:
                config = json.load(file)
                return config.get("login"), config.get("password"), config.get("api_key")
            except json.JSONDecodeError:
                print("Ошибка чтения конфигурации, файл поврежден.")
                return None, None, None
    else:
        return None, None, None

# Функция для сохранения конфигурации в файл
def save_config(login, password, api_key):
    config = {
        "login": login,
        "password": password,
        "api_key": api_key
    }
    with open(CONFIG_FILE, "w", encoding="UTF-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

# Функция для получения списка игр на аккаунте
def get_steam_games(steam_id, api_key):
    """Получаем список игр пользователя по Steam API."""
    url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    
    params = {
        "key": api_key,
        "steamid": steam_id,
        "format": "json",
        "include_played_free_games": "true",
        "include_appinfo": "true",
        "include_game_icons": "true" 
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Возвращаем список ID игр и их названия
    if "response" in data and "games" in data["response"]:
        return [(game["appid"], game["name"]) for game in data["response"]["games"]]
    else:
        print("Не удалось получить список игр.")
        return []

# Функция для выбора игр
def choose_games(available_games):
    """Предлагаем пользователю выбрать игры для накрутки времени."""
    print("Доступные игры:")
    for idx, game in enumerate(available_games, 1):  # Выводим все игры
        print(f"{idx}. {game[1]} (ID: {game[0]})")

    chosen_games = input("Введите номера игр для накрутки (через запятую): ").split(",")
    
    # Отфильтровываем некорректные или пустые значения
    selected_game_ids = []
    for choice in chosen_games:
        choice = choice.strip()
        if choice.isdigit():  # Проверяем, что введено число
            idx = int(choice) - 1  # Индексация с 1
            if 0 <= idx < len(available_games):  # Проверяем, что индекс в допустимом диапазоне
                selected_game_ids.append(available_games[idx][0])
            else:
                print(f"Номер игры {choice} выходит за пределы доступных игр.")
        else:
            print(f"Неверный ввод: {choice} не является числом.")

    # Ограничиваем выбор 32 играми
    return selected_game_ids[:32]

# Загружаем конфигурацию
login, password, api_key = load_config()

if login is None or password is None or api_key is None:
    # Если конфигурация не найдена или повреждена, запрашиваем логин, пароль и API_KEY
    print("Конфигурация не найдена или файл поврежден. Пожалуйста, введите логин, пароль и API_KEY.")
    login = input("Введите логин: ").strip()
    password = input("Введите пароль: ").strip()
    api_key = input("Введите свой Steam API ключ: ").strip()

    # Сохраняем введенные данные в файл
    save_config(login, password, api_key)

# Теперь у нас есть логин, пароль и API_KEY, которые можно использовать для входа
account = (login, password)

# Инициализируем Steam клиент
os.system("title Steam Hour Booster")
client = steam.client.SteamClient()

# Логинимся в Steam и ждем успешной авторизации
try:
    client.cli_login(*account)
    print("Авторизация успешна!")
except Exception as e:
    print(f"Ошибка при авторизации: {e}")
    exit()

# Убедимся, что авторизация прошла успешно
if client.user is None:
    print("Не удалось получить данные пользователя после авторизации.")
    client.logout()
    client.disconnect()
    exit()

# Получаем список игр с Steam
steam_id = client.user.steam_id
available_games = get_steam_games(steam_id, api_key)

if not available_games:
    print("Нет игр для накрутки.")
    client.logout()
    client.disconnect()
    exit()

# Выбираем игры для накрутки
games_to_play = choose_games(available_games)

if not games_to_play:
    print("Не выбраны игры для накрутки.")
    client.logout()
    client.disconnect()
    exit()

# Проверим список выбранных игр
print("Выбранные игры:", games_to_play)

# Устанавливаем все игры сразу
client.games_played(games_to_play)

# Очистим консоль
os.system("cls")

# Запускаем отсчет времени
start = datetime.datetime.now()
while not ctypes.windll.user32.GetAsyncKeyState(0x1B):
    current_time = str(datetime.datetime.now() - start).split(".")[0]
    print(f"\r[SHBooster] -> Ник: [{client.user.name}] | Время: [{current_time}]", end="")

# Завершаем программу по нажатию клавиши ESC
client.logout()
client.disconnect()
