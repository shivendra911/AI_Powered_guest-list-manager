# 🤖 AI-Powered Guest List Manager (V2 Premium)

Welcome to the **AI-Powered Guest List Manager**, a robust and aesthetically premium full-stack application built with Python. This project demonstrates a clean architecture approach to building scalable, AI-integrated web applications using **Flask**, **Tailwind CSS**, and **SQLAlchemy**.

[![GitHub](https://img.shields.io/badge/GitHub-shivendra911-indigo?style=flat&logo=github)](https://github.com/shivendra911)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat&logo=python)
![Flask](https://img.shields.io/badge/Framework-Flask-black?style=flat&logo=flask)
![Theme](https://img.shields.io/badge/Theme-Zinc%20%2F%20Indigo-white?style=flat)

---

## 🚀 Overview

This application is designed for event organizers who need a seamless way to manage guests, track RSVPs, and interact with a smart AI assistant. Unlike typical CRUD apps, it features a **dual LLM strategy** for high availability and a **premium Zinc-based design system** with full dark mode support and glassmorphism.

---

## ✨ Key Features

### 🧠 Intelligent Chat Assistant
- **Dual LLM Logic**: Primary integration with **Google Gemini 2.0 Flash**.
- **Local Fallback**: Automatically switches to **Llama 3.2** (via Ollama) if the cloud API is unreachable.
- **Context-Aware Analytics**: The AI understands your events and guest data to provide insights.

### 🎭 Mood & Sentiment Analysis
- **Review Analyzer**: Real-time sentiment analysis for guest feedback.
- **Glassmorphism UI**: Beautifully rendered results with dynamic accent colors (Indigo/Zinc).
- **Sample Prompts**: Interactive quick-start prompts for rapid testing.

### ⚙️ Advanced Control Center
- **Theme Personalization**: Custom accent color selector that persists across sessions.
- **Dark/Light Mode**: Premium Zinc-950 dark theme for eye-friendly management.
- **Notification Settings**: Granular control over email, audio, and SMS alerts.
- **Security Management**: 2FA setup and active session tracking.

### 🛡️ Enterprise-Grade Backend
- **Clean Architecture**: Strict separation of concerns (Models, Services, Routes).
- **Role-Based Access (RBAC)**: Admin-only sections for sensitive event management.
- **Secure RDBMS**: SQLite with SQLAlchemy ORM (SQL Injection protected).

---

## 🏗️ Project Structure

The project follows a modular pattern to ensure maintainability:

```text
/
├── app/                        # Main Application Package
│   ├── models/                 # Data Layer (Database Entities)
│   ├── routes/                 # Interface Layer (Blueprints & Endpoints)
│   ├── services/               # Logic Layer (AI Logic & Business Rules)
│   ├── templates/              # Presentation Layer (Jinja2 Templates)
│   └── static/                 # Frontend Assets (CSS/JS/Images)
├── database/                   # Database Storage
├── .env                        # Environment Variables (API Keys)
├── init_db.py                  # Database Initializer & Admin Creator
├── requirements.txt            # Dependency Manifest
├── run.py                      # Application Entry Point
└── Dockerfile                  # Containerization Instructions
```

---

## 🛠️ Installation & Setup

### 1. Clone & Environment
```bash
git clone https://github.com/shivendra911/zzzchatbotfinal.git
cd zzzchatbotfinal
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 2. Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_SECRET_KEY=your_random_secret_string
```

### 4. Database Setup
Initialize the SQLite database and create the default admin account:
```bash
python init_db.py
```
*Default Credentials: `admin@example.com` / `admin123`*

---

## 🐳 Docker Deployment

The application is fully containerized. To run without local Python setup:

```bash
docker-compose up --build
```

---

## 👨‍💻 Author

**Shivendra Pratap**
- GitHub: [@shivendra911](https://github.com/shivendra911)
- LinkedIn: [Shivendra Pratap](https://www.linkedin.com/in/shivendra--pratap/)
- Registration No: 12323629

---

## ⚖️ License
This project is for educational and portfolio purposes. Feel free to explore and build upon it!