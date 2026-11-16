from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from database import users_db, get_user_by_token
import time

router = APIRouter(prefix="/news", tags=["News"])

news_db: dict[int, dict] = {}


class NewsCreate(BaseModel):
    title: str
    content: str


@router.post("/")
def create_news(
    news_data: NewsCreate,
    token: Optional[str] = Header(default=None)
):
    user = get_user_by_token(token) if token else None

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Войдите в аккаунт, чтобы создать новость."
        )

    if user.role != "staff":
        raise HTTPException(
            status_code=403,
            detail="Только сотрудники могут публиковать новости."
        )

    title = news_data.title.strip()
    content = news_data.content.strip()

    if not title or not content:
        raise HTTPException(
            status_code=400,
            detail="Заполните заголовок и текст новости."
        )

    news_id = max(news_db.keys(), default=0) + 1

    news_db[news_id] = {
        "id": news_id,
        "title": title,
        "content": content,
        "author_id": user.id,
        "author_name": user.name,
        "created_at": time.strftime("%d.%m.%Y %H:%M")
    }

    return news_db[news_id]


@router.get("/")
def get_news():
    return sorted(
        news_db.values(),
        key=lambda news: news["id"],
        reverse=True
    )


@router.get("/{news_id}")
def get_news_by_id(news_id: int):
    news = news_db.get(news_id)

    if not news:
        raise HTTPException(
            status_code=404,
            detail="Новость не найдена."
        )

    return news