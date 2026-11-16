from datetime import datetime

from fastapi import APIRouter, HTTPException, Header
from models import NewsCreate, News
from database import news_db, get_user_by_token

router = APIRouter(
    prefix="/news",
    tags=["Новости"]
)


@router.post("/", response_model=News)
def create_news(
    news_data: NewsCreate,
    token: str = Header(...)
):
    user = get_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )

    if user.role != "staff":
        raise HTTPException(
            status_code=403,
            detail="Только сотрудники могут публиковать новости"
        )

    news_id = len(news_db) + 1

    new_news = News(
        id=news_id,
        title=news_data.title,
        content=news_data.content,
        author_id=user.id,
        author_name=user.name,
        created_at=datetime.now().strftime("%d.%m.%Y %H:%M")
    )

    news_db[news_id] = new_news
    return new_news


@router.get("/", response_model=list[News])
def get_news():
    return list(news_db.values())