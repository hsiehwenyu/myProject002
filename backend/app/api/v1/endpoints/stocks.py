import time
import requests
from fastapi import APIRouter

router = APIRouter()

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://mis.twse.com.tw/",
}


def _fetch(stock_id: str, market: str) -> dict | None:
    try:
        resp = requests.get(
            "https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
            params={"ex_ch": f"{market}_{stock_id}.tw", "_": str(int(time.time() * 1000))},
            headers=_HEADERS,
            timeout=6,
        )
        data = resp.json()
        arr = data.get("msgArray")
        if not arr:
            return None
        item = arr[0]
        name = item.get("n", "").strip()
        if not name:
            return None
        # z = real-time price, y = previous close
        price = None
        for key in ("z", "y"):
            raw = item.get(key, "-").strip()
            if raw and raw != "-":
                try:
                    price = float(raw.replace(",", ""))
                    break
                except ValueError:
                    pass
        return {"sec_name": name, "curr_price": price}
    except Exception:
        return None


@router.get("/{stock_id}")
def get_stock_info(stock_id: str):
    stock_id = stock_id.strip().upper()
    for market in ("tse", "otc"):
        result = _fetch(stock_id, market)
        if result:
            return {"sec_id": stock_id, "found": True, **result}
    return {"sec_id": stock_id, "found": False, "sec_name": "", "curr_price": None}
