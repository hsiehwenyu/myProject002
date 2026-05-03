from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.auth import get_current_user, get_current_admin, CurrentUser
from app.core.database import get_db
from app.models.menu_item import MenuItem
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate, MenuItemRead

router = APIRouter()


@router.get("/", response_model=List[MenuItemRead])
def list_menu_items(
    db: Session = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
):
    items = (
        db.query(MenuItem)
        .filter(MenuItem.is_active == True)
        .order_by(MenuItem.sort_order, MenuItem.id)
        .all()
    )
    if current.role != "admin":
        items = [i for i in items if i.min_role == "user"]
    return items


@router.get("/all", response_model=List[MenuItemRead])
def list_all_menu_items(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_admin),
):
    return db.query(MenuItem).order_by(MenuItem.sort_order, MenuItem.id).all()


@router.post("/", response_model=MenuItemRead, status_code=201)
def create_menu_item(
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_admin),
):
    item = MenuItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=MenuItemRead)
def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_admin),
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="選單項目不存在")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_admin),
):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="選單項目不存在")
    db.delete(item)
    db.commit()
