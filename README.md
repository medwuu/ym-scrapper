# ym-scrapper

## Что это?
Нужно получить список песен из Яндекс Музыки? Этот репозиторий для тебя

- Дружелюбный интерфейс
- Экспорт в формате _TXT_, _JSON_, _CVS_
- Экспорт как "любимого плейлиста", так любого указанного

## Атрибуты
```
usage: scrapper.py [-h] (-u USERNAME | -U USER_URL) [-o OUTPUT] [-t {txt,json,csv}]

options:
  -h, --help            Справка по программе
  -u, --username USERNAME
                        Поиск по имени пользователя
  -U, --user-url USER_URL
                        Поиск по ссылке на профиль пользователя
  -o, --output OUTPUT   Файл для записи результатов
  -t, --type {txt,json,csv}
                        Тип вывода: txt (по умолчанию), json или csv
```