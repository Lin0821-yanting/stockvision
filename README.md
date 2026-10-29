# StockVision — 台美股智慧看盤與模擬投資平台

以 **Python FastAPI** 後端與 **Next.js** 前端打造的全端 MVP：台股、美股盤中報價、歷史走勢、模擬交易、價格提醒與多股比較。

> 開發中。完整的安裝、操作與 API 說明會在文件階段補齊。

## 專案結構

```text
stockvision/
├── backend/    # Python 3.11+、FastAPI、SQLAlchemy、Pandas、HTTPX
├── frontend/   # Next.js 16、TypeScript、Tailwind CSS v4、shadcn/ui、Recharts
└── docs/       # 技術文件
```

## 快速開始（Anaconda Prompt）

```powershell
# 建立 conda 環境（只需一次）
conda env create -f environment.yml
conda activate stockvision

# 後端
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 前端（另開一個終端機）
cd frontend
npm install
npm run dev
```

- 網站：http://localhost:3000
- API 文件（Swagger UI）：http://localhost:8000/docs
