import secrets #временное хранилище

from models import User, Task, AuctionLot

users_db: dict[int, User] = {}
tasks_db: dict[int, Task] = {}
auctions_db: dict[int, AuctionLot] = {}

tokens_db: dict[str, int] = {} #хранится соответствие токена и ID пользователя
passwords_db: dict[str, str] = {}


def create_token(user_id: int) -> str: 
    token = secrets.token_hex(16) #создаётся случайный токен, который связывается с пользователем. В следующих запросах сервер по нему определяет аккаунт
    tokens_db[token] = user_id
    return token


def get_user_by_token(token: str): 
    user_id = tokens_db.get(token)

    if user_id is None:
        return None

    return users_db.get(user_id)