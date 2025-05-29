import os
import argparse
import requests
import json
from art import tprint
from termcolor import colored
from tqdm import tqdm
from bs4 import BeautifulSoup


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
    url = f"https://music.yandex.ru/users/{username}/playlists"
    print("[⏰] Сбор плейлистов...")

    response = requests.get(url, cookies={"prevent_next_web": "true"})
    response.encoding = "UTF-8"
    if response.status_code == 404:
        throwError("Ошибка! Пользователь не найден!")
    elif response.status_code != 200:
        throwError(f"Произошла ошибка при сборе плейлистов пользователя. Код ошибки: {response.status_code}")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, "html.parser")

    script_data = soup.find("body").find("script")
    dict_data = json.loads(script_data.text.split("=")[1][:-1]) # срез данных
    uid = dict_data['pageData']['owner']['uid']
    playlists = dict_data['pageData']['playlistIds']
    print(f"Найдено {len(playlists)} плейлистов")

    playlists_url = f"https://music.yandex.ru/handlers/playlists-list.jsx?owner={uid}&ids={str(playlists).replace('[', '').replace(']', '').replace(' ', '')}"
    playlists_name = requests.get(playlists_url).json()
    for i in range(len(playlists_name)):
        print(i+1, "--->", playlists_name[i]['title'])

    try:
        selected_playlist = int(input("Выберите один из плейлистов: ")) - 1
        if selected_playlist < 0 or selected_playlist > len(playlists_name) - 1:
            throwError("Ошибка! Введено число вне диапазона")
    except ValueError:
        throwError("Ошибка! Ввеедено не число")
    return f"https://music.yandex.ru/handlers/playlist.jsx?owner={username}&kinds={playlists_name[selected_playlist]['kind']}"



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
        if type == "json":
            lines = {}
            json.dump(data, f, ensure_ascii=False, indent=4)
        elif type == "txt":
            lines = [track["title"] + " – " + track["artists"][0]["name"]
                     for track in tqdm(data["playlist"]["tracks"])]
            f.write("\n".join(lines))
        elif type == "csv":
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