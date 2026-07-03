import json

from config import USERS_FILE


if not USERS_FILE.exists():
    USERS_FILE.write_text(
        "{}",
        encoding="utf-8"
    )


def load_users():

    with open(
        USERS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_users(users):

    with open(
        USERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            users,
            file,
            ensure_ascii=False,
            indent=4
        )


def get_user(user_id):

    users = load_users()

    user_id = str(user_id)

    if user_id not in users:

        users[user_id] = {
            "passport": None,
            "receipt": None,
            "approved": False
        }

        save_users(users)

    return users[user_id]


def update_user(user_id, **kwargs):

    users = load_users()

    user_id = str(user_id)

    if user_id not in users:

        users[user_id] = {}

    for key, value in kwargs.items():

        users[user_id][key] = value

    save_users(users)
