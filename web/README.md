# Running the App and Server

There are two parts:

- `api/`: FastAPI backend server (`http://localhost:5000`)
- `app/`: React + Vite frontend (`http://localhost:5173`)

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+ (with `pip`)

## 1. Clone the project and navigate to repository

```powershell
git clone https://github.com/COMP2281/software-engineering-group25-26-14.git
cd software-engineering-group25-26-14
```

## 2. Installation

### 2.1 Backend installation

Open a terminal in the project root and run:

#### Windows (PowerShell)

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, run this once in the same terminal first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This installs all required python modules in a virtual environment.

### 2.2 Frontend installation

Also from the project root, run:

```powershell
cd web\app
npm install
```

## 3. Running the app

### 3.1 Running the backend

Open a terminal in the project root and run:

```powershell
cd web\api
python -m uvicorn main:app --port 5000
```

Backend will be available at http://localhost:5000
API docs are at http://localhost:5000/docs

### 3.2 Running the frontend

Open a second terminal in the root folder and run:

```powershell
cd web\app
npm run dev
```

Frontend will be available at http://localhost:5173

## 4. Using the app

Keep both terminals running.

Open http://localhost:5173 in your browser to use the application.