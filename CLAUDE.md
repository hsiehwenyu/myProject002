# CLAUDE.md — MYPROJECT002

投資資產管理系統：追蹤多個投資組合的各類資產，自動計算市值、交易費用與證交稅。

## Tech Stack

- **Frontend**: Vue 3 + TypeScript + Vite (port 5174)
- **Backend**: Python + FastAPI + SQLite (port 8001)

## Project Structure

```
myProject002/
├── backend/
│   ├── main.py                     # FastAPI entry, DB init via lifespan
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── core/
│       │   ├── config.py           # pydantic-settings
│       │   └── database.py         # SQLAlchemy engine + get_db
│       ├── models/
│       │   ├── portfolio.py        # Portfolio ORM model
│       │   └── security.py        # Security ORM model + ASSET_TYPE_TAX_RATES
│       ├── schemas/
│       │   ├── portfolio.py        # PortfolioCreate/Update/Response/Summary
│       │   └── security.py        # SecurityCreate/Update/Response (計算欄位於此)
│       └── api/v1/
│           ├── router.py
│           └── endpoints/
│               ├── portfolios.py   # CRUD + GET /{id} 含彙整邏輯
│               └── securities.py  # CRUD + PATCH price + GET /asset-types
└── frontend/
    └── src/
        ├── types/index.ts          # TypeScript 型別定義
        ├── api/index.ts            # fetch 封裝
        ├── stores/portfolio.ts     # Pinia store
        ├── router/index.ts
        ├── views/
        │   ├── HomeView.vue        # 投資組合列表
        │   └── PortfolioDetailView.vue  # 明細 + 彙整 + 圓餅圖
        └── components/
            ├── PieChart.vue        # Chart.js 圓餅圖
            └── SecurityFormModal.vue    # 新增/編輯資產彈窗
```

## Commands

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --reload --port 8001
```

- **Swagger UI**: http://localhost:8001/docs

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5174
```

## Business Logic

### 計算公式

| 欄位 | 公式 |
|------|------|
| 市值(1) | `curr_price × shares`（price_unavailable=True 時為 0） |
| 交易費用 | `mv_1 × fee_rate`（預設 0.1425%） |
| 證交稅 | `mv_1 × tax_rate` |
| 市值(2) | `mv_1 - tx_fee - tx_tax` |

### 預設稅率（依資產類別）

| 類別 | 證交稅率 |
|------|--------|
| 股票-個股 | 0.3% |
| 股票ETF | 0.1% |
| 債券-ETF | 0%（目前停徵） |
| CB | 0.1% |
| CBAS | 0.1% |

### 彙整邏輯

`GET /api/v1/portfolios/{id}` 回傳：
- `securities[]` — 所有資產含計算欄位
- `totals` — 全組合加總（mv_1, tx_fee, tx_tax, mv_2）
- `by_asset_type[]` — 依資產類別分組加總

## API Design

所有路由在 `/api/v1/` 下：

```
GET    /portfolios/                         # 列表
POST   /portfolios/                         # 新增
GET    /portfolios/{id}                     # 詳情含彙整
PUT    /portfolios/{id}                     # 更新
DELETE /portfolios/{id}                     # 刪除（cascade）

GET    /portfolios/{id}/securities          # 列出資產
POST   /portfolios/{id}/securities          # 新增資產
GET    /securities/{id}                     # 取得單筆
PUT    /securities/{id}                     # 更新
PATCH  /securities/{id}/price               # 更新股價（異常處理）
DELETE /securities/{id}                     # 刪除

GET    /asset-types                         # 取得資產類別與預設稅率
```
