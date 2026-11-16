from fastapi import APIRouter, HTTPException, Header
from models import TransferRequest, AuctionCreate, AuctionLot
from database import users_db, auctions_db, get_user_by_token

router = APIRouter(
    prefix="/bank",
    tags=["Банк и аукционы"]
)


@router.post("/transfer")
def transfer_currency(
    data: TransferRequest,
    token: str = Header(...)
):
    sender = get_user_by_token(token)

    if sender is None:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )

    receiver = users_db.get(data.to_user_id)

    if not receiver:
        raise HTTPException(
            status_code=404,
            detail="Получатель не найден"
        )

    if data.amount <= 0 or sender.balance < data.amount:
        raise HTTPException(
            status_code=400,
            detail="Недостаточно средств на балансе"
        )

    sender.balance -= data.amount
    receiver.balance += data.amount

    return {
        "status": "успешно",
        "new_balance": sender.balance
    }


@router.post("/auctions/", response_model=AuctionLot)
def create_auction(
    lot_data: AuctionCreate,
    token: str = Header(...)
):
    user = get_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )

    if lot_data.start_price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Начальная цена должна быть больше нуля"
        )

    lot_id = len(auctions_db) + 1

    new_lot = AuctionLot(
        id=lot_id,
        item_name=lot_data.item_name,
        start_price=lot_data.start_price,
        current_bid=lot_data.start_price
    )

    auctions_db[lot_id] = new_lot
    return new_lot


@router.get("/auctions/", response_model=list[AuctionLot])
def get_auctions():
    return list(auctions_db.values())


@router.post("/auctions/{lot_id}/bid", response_model=AuctionLot)
def place_bid(
    lot_id: int,
    bid_amount: int,
    token: str = Header(...)
):
    user = get_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )

    lot = auctions_db.get(lot_id)

    if not lot or not lot.is_active or lot.is_sold:
        raise HTTPException(
            status_code=404,
            detail="Лот не найден, неактивен или уже продан"
        )

    if bid_amount <= lot.current_bid:
        raise HTTPException(
            status_code=400,
            detail="Ставка должна быть выше текущей цены"
        )

    if user.balance < bid_amount:
        raise HTTPException(
            status_code=400,
            detail="Недостаточно валюты для такой ставки"
        )

    if lot.highest_bidder_id:
        previous_bidder = users_db[lot.highest_bidder_id]
        previous_bidder.balance += lot.current_bid

    user.balance -= bid_amount
    lot.current_bid = bid_amount
    lot.highest_bidder_id = user.id

    return lot


@router.post("/auctions/{lot_id}/close", response_model=AuctionLot)
def close_auction(
    lot_id: int,
    token: str = Header(...)
):
    user = get_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )

    lot = auctions_db.get(lot_id)

    if not lot:
        raise HTTPException(
            status_code=404,
            detail="Лот не найден"
        )

    if not lot.is_active:
        raise HTTPException(
            status_code=400,
            detail="Аукцион уже завершён"
        )

    lot.is_active = False
    return lot


@router.post("/auctions/{lot_id}/buy", response_model=AuctionLot)
def buy_lot(
    lot_id: int,
    token: str = Header(...)
):
    user = get_user_by_token(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Вы не авторизованы"
        )

    lot = auctions_db.get(lot_id)

    if not lot:
        raise HTTPException(
            status_code=404,
            detail="Лот не найден"
        )

    if lot.is_active:
        raise HTTPException(
            status_code=400,
            detail="Сначала завершите аукцион"
        )

    if lot.is_sold:
        raise HTTPException(
            status_code=400,
            detail="Лот уже продан"
        )

    if lot.highest_bidder_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Купить лот может только победитель аукциона"
        )

    lot.is_sold = True
    return lot