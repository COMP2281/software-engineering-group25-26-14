# Installation Instructions

## Prerequisites

- **Node.js 18+ and npm**: https://nodejs.org/en/download
- **Python 3.10+ (with `pip`)**: https://www.python.org/downloads/
- **Ollama**: https://ollama.com/download

## 1. Clone the project and navigate to repository

```powershell
git clone https://github.com/COMP2281/software-engineering-group25-26-14.git
cd software-engineering-group25-26-14
```

## 2. Set up Ollama

Check if Ollama is running:

```powershell
ollama list
```

If this shows a list of models (or even an empty list), Ollama is running. 

If you get a connection error, start Ollama manually:

```powershell
ollama serve
```

Then download the required model (this may take some time, but only needs to be done once):
```powershell
ollama pull granite3.1-dense:8b
```

You can run `ollama list` again to confirm the model is installed.

Keep Ollama running. The backend will connect to it at http://localhost:11434.

## 3. Backend installation

Open a terminal in the project root and run:

### Windows (PowerShell)

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks script execution, run this once in the same terminal first. This only changes the policy for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This installs all required python modules in a virtual environment.

## 4. Frontend installation

Also from the project root, run:

```powershell
cd web/app
npm install
```

This installs the required node modules. 

## 5. Running the backend

Open a terminal in the project root. Ensure that the virtual environment is active:

### Windows (PowerShell)

```powershell
.\venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
source venv/bin/activate
```

Then, run:

```powershell
cd web/api
python -m uvicorn main:app --port 8000
```

The backend will now be available at http://localhost:8000.
The API docs are at http://localhost:8000/docs.

## 6. Running the frontend

Open a second terminal in the root folder and run:

```powershell
cd web/app
npm run dev
```

The frontend will be available at http://localhost:5173.

## 7. Using the app

Keep both terminals running.

Open http://localhost:5173 in your browser to use the application.