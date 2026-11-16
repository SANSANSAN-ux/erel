from pydantic import BaseModel
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


class TaskCreate(BaseModel):
    title: str
    description: str
    reward: int


class Task(TaskCreate):
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
    is_sold: bool = False


class NewsCreate(BaseModel):
    title: str
    content: str


class News(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_name: str
    created_at: str