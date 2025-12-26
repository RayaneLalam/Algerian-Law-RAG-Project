```markdown
# Project Setup Guide

This repository contains both the backend and frontend components of the application. Follow the instructions below to get your local development environment running.

---

## 📂 Backend Setup Guide

Follow these steps to configure and run the backend server.

### 1. Navigate to the backend directory
```bash
cd backend

```

### 2. Create a virtual environment

**Linux / macOS:**

```bash
python3 -m venv venv

```

**Windows:**

```bash
python -m venv venv

```

### 3. Activate the virtual environment

**Linux / macOS:**

```bash
source venv/bin/activate

```

**Windows:**

```bash
venv\Scripts\activate

```

> **Note:** You should see `(venv)` appearing in your terminal prompt after activation.

### 4. Install dependencies

```bash
pip install -r requirements.txt

```

### 5. Run the backend server

```bash
python run.py

```

✅ **The backend should now be running successfully.**

*To stop the virtual environment when you are finished, simply run:*

```bash
deactivate

```

---

## 💻 Frontend Setup Guide

The project contains two distinct frontend interfaces. Follow these steps for the specific interface you wish to run.

| Interface | Path | Description |
| --- | --- | --- |
| **User RAG** | `/frontend` | The primary user-facing RAG interface |
| **Evaluation** | `/evaluation-interface` | The interface for system evaluation |

### 1. Navigate to the interface directory

**For the User RAG Interface:**

```bash
cd frontend

```

**For the Evaluation Interface:**

```bash
cd evaluation-interface

```

### 2. Install dependencies

```bash
npm install

```

### 3. Run the development server

```bash
npm run dev

```

✅ **The interface will be available in your browser at the URL shown in the terminal (usually http://localhost:5173).**

