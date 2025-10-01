import os
import argparse
import requests
import json
from art import tprint
from termcolor import colored
from tqdm import tqdm


def throwError(err_message):
    print(colored(err_message, on_color="on_red"))
    exit(1)


def parseArguments():
    parser = argparse.ArgumentParser(add_help=False,
                                     description="Утилита для сбора информации о плейлистах с Яндекс.Музыки")

    # Служебные
    parser.add_argument("-h", "--help",
                        help="Справка по программе",
                        action="help")

    # TODO: статистика по исполнителям из плейлиста

    # Группа
    user_group = parser.add_mutually_exclusive_group(required=True)
    user_group.add_argument("-u", "--username",
                            type=str,
                            help="Поиск по имени пользователя")
    user_group.add_argument("-U", "--user-url",
                            type=str,
                            help="Поиск по ссылке на профиль пользователя")

    # Обычные
    parser.add_argument("-o", "--output",
                        type=str,
                        default="output.txt",
                        help="Файл для записи результатов")
    parser.add_argument("-t", "--type",
                        type=str,
                        choices=["txt", "json", "csv"],
                        default="txt",
                        help="Тип вывода: txt (по умолчанию), json или csv")

    return parser.parse_args()


def scrapPlaylists(username):
    url = f"https://api.music.yandex.net/users/{username}/playlists/list"
    print("[⏰] Сбор плейлистов...")

    response = requests.get(url).json()
    # TODO
    # if response.status_code == 404:
    #     throwError("Ошибка! Пользователь не найден!")
    # elif response.status_code != 200:
    #     throwError(f"Произошла ошибка при сборе плейлистов пользователя. Код ошибки: {response.status_code}")

    playlists = response['result']
    if 'result' in requests.get(f"https://api.music.yandex.net/users/{username}/playlists/3").json():
        playlists.append({"title": "Мне нравится",
                          "kind": 3})

    print(f"Найдено {len(playlists)} плейлистов")

    playlists_name = [x['title'] for x in playlists]
    for i, name in enumerate(playlists_name, start=1):
        print(i, "--->", name)

    try:
        selected_playlist = int(input("Выберите один из плейлистов: ")) - 1
        if selected_playlist < 0 or selected_playlist > len(playlists_name):
            throwError("Ошибка! Введено число вне диапазона")
        playlist_kinds = playlists[selected_playlist]['kind']
    except ValueError:
        throwError("Ошибка! Ввеедено не число")
    return f"https://music.yandex.ru/handlers/playlist.jsx?owner={username}&kinds={playlist_kinds}"



def scrapData(username, user_url):
    print("[⏰] Формирование ссылки...")
    if username:
        link = scrapPlaylists(username)
    else:
        if not user_url.startswith("https://music.yandex.ru/users/"):
            throwError("Ой! Кажется это не ссылка на плейлист Яндекс.Музыки!")

        try:
            username = user_url.split("/")[4]
            playlist = user_url.split("/")[6]
        except IndexError:
            throwError("Ошибка! Неверный формат ссылки на плейлист!")

        link = f"https://music.yandex.ru/handlers/playlist.jsx?owner={username}&kinds={playlist}"

    print("[⏰] Запрос данных...")
    response = requests.get(link)
    if response.status_code == 404:
        throwError("Ошибка! Плейлист не найден или доступ к нему заблокирован!\n" \
                   "Если ссылка верна, попробуйте изменить аргумент")
    elif response.status_code != 200:
        throwError(f"Произошла ошибка при запросе данных с сайта. Код ошибки: {response.status_code}")

    print("[✅] Успешный ответ от сервера!")
    return response.json()


def writeData(output, type, data):
    print("[⏰] Обработка данных")
    with open(output, "w", encoding="UTF-8") as f:
        if type == "json" or output.endswith(".json"):
            lines = []
            for track in tqdm(data["playlist"]["tracks"]):
                lines.append({track["artists"][0]["name"]: track["title"]})
            json.dump(lines, f, ensure_ascii=False, indent=4)
        elif type == "txt" or output.endswith(".txt"):
            lines = [track["title"] + " – " + track["artists"][0]["name"]
                     for track in tqdm(data["playlist"]["tracks"])]
            f.write("\n".join(lines))
        elif type == "csv" or output.endswith(".csv"):
            lines = ["\"" + track["title"] + "\",\"" + track["artists"][0]["name"] + "\""
                     for track in tqdm(data["playlist"]["tracks"])]
            f.write("name,artist\n" + "\n".join(lines))
        else:
            throwError("Неподдерживаемый тип выходного файла")

        print(f"[✅] Данные успешно записаны в файл '{os.path.realpath(f.name)}'\n" \
            f"[✅] Всего {len(data["playlist"]["tracks"])} песен")


def main():
    tprint("YM-Scrapper")
    args = parseArguments()
    scrapped_data = scrapData(args.username, args.user_url)
    writeData(args.output, args.type, scrapped_data)


if __name__ == "__main__":
    main()