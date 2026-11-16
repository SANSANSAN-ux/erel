from fastapi import APIRouter, HTTPException, Header
from models import UserRegister, UserLogin, User
from database import users_db, passwords_db, create_token, get_user_by_token

router = APIRouter(
    prefix="/users",
    tags=["Пользователи"]
)


@router.post("/register", response_model=User)
def register_user(user_data: UserRegister):
    if user_data.role not in ["student", "staff"]:
        raise HTTPException(
            status_code=400,
            detail="Роль должна быть 'student' или 'staff'"
        )

    for user in users_db.values():
        if user.username == user_data.username:
            raise HTTPException(
                status_code=400,
                detail="Такой логин уже занят"
            )

    user_id = len(users_db) + 1

    new_user = User(
        id=user_id,
        name=user_data.name,
        username=user_data.username,
        role=user_data.role
    )

    users_db[user_id] = new_user
    passwords_db[user_data.username] = user_data.password

    return new_user


@router.post("/login")
def login_user(user_data: UserLogin):
    user = None

    for current_user in users_db.values():
        if current_user.username == user_data.username:
            user = current_user
            break

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    if passwords_db.get(user_data.username) != user_data.password:
        raise HTTPException(
            status_code=400,
            detail="Неверный пароль"
        )

    token = create_token(user.id)

    return {
        "token": token,
        "user": user
    }


@router.get("/me")
def get_current_user(token: str = Header(...)):
    user = get_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )

    return user