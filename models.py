from pydantic import BaseModel #описывает данные
from typing import Optional


class UserRegister(BaseModel):
    name: str
    username: str
    password: str
    role: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    name: str
    username: str
    role: str
    balance: int = 0
    completed_tasks: int = 0


class TaskCreate(BaseModel): #данные, которые сайт отправляет при создании поручения
    title: str
    description: str
    reward: int
   


class Task(TaskCreate): #поручение, которое сохраняет сервер наследует название, описание и награду из TaskCreate и добавляет номер, автора, статус и исполнителя
    id: int
    creator_id: int
    status: str = "open"
    assignee_id: Optional[int] = None


class TransferRequest(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: int


class AuctionCreate(BaseModel):
    item_name: str
    start_price: int


class AuctionLot(BaseModel):
    id: int
    item_name: str
    start_price: int
    current_bid: int
    highest_bidder_id: Optional[int] = None
    is_active: bool = True