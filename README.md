## mini_social_network - социальная сеть для публикаций.

### Возможности проекта:
- Регистрация пользователя.
- Публикация записей с изображениями.
- Публикация записей в сообщества.
- Комментарии к записям других авторов.
- Подписка на других авторов.
- Лента с записями, на которых оформлена подписка.
- Для проекта написаны тесты Unittest.

#### Технологии

- Python 3.7
- Django 3.2
- SQLite3

## Установка

1. Клонировать репозиторий:

    ```python
    git clone https://github.com/doroshenkokb/mini_social_network
    ```

3. Создать и активировать виртуальное пространство, установить зависимости и запустить тесты:

    Для Windows:

    ```python
    python -m venv venv && source venv/Scripts/activate
    pip install -r requirements.txt
    ```

    Для Mac/Linux:

    ```python
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

4. Для запуска в виртуальном окружении, после создания и активации виртуального пространства, установки зависимостей, запустить проект локально:

    Для Windows:

    ```python
    cd yatube
    python manage.py runserver
    ```

    Для Mac/Linux:

    ```python
    cd yatube
    python3 manage.py runserver
    ```

5. Проверить доступность сервиса:

    ```python
    http://localhost/admin
    ```

#### Автор

Дорошенко Кирилл - [https://github.com/doroshenkokb](https://github.com/doroshenkokb)