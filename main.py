from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import users, tasks, bank #подключаем модули пользователей, поручений и банка


app = FastAPI(title="ЭРЭЛ")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(bank.router) #строки регистрируют группы API-запросов в основном приложении


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse("templates/index.html")
#подключаем папку со стилями и JavaScript, чтобы браузер мог загрузить их



@app.get("/news-page", include_in_schema=False)
def news_page():
    return FileResponse("templates/news.html")


@app.get("/tasks-page", include_in_schema=False)
def tasks_page():
    return FileResponse("templates/tasks.html")


@app.get("/bank-page", include_in_schema=False)
def bank_page():
    return FileResponse("templates/bank.html")