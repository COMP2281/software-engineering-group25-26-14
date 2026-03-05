# Running the App and Server

There are two parts:

- `api/`: FastAPI backend server (`http://localhost:5000`)
- `app/`: React + Vite frontend (`http://localhost:5173`)

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+ (with `pip`)

## 1. Clone the project and navigate to branch

```powershell
git clone https://github.com/COMP2281/software-engineering-group25-26-14.git
cd software-engineering-group25-26-14/
git checkout Francis
```

## 2. Set up and run the backend (`api`)

Open a terminal in the project root and run:

### Windows (PowerShell)

```powershell
cd web\api
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 5000
```

If PowerShell blocks activation, run this once in the same terminal first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### macOS/Linux

```bash
cd web\api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 5000
```

Backend should now be running at `http://localhost:5000`.
API docs are available at `http://localhost:5000/docs`.

## 3. Set up and run the frontend (`app`)

Open a second terminal in the root and run:

```powershell
cd web\app
npm install
npm run dev
```

Frontend should now be running at `http://localhost:5173`.

## 4. Use the app

Keep both terminals running:

- Terminal 1: backend (`uvicorn`)
- Terminal 2: frontend (`vite`)

Use the application at `http://localhost:5173`