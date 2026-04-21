# 📊 Capital Markets Analytics Platform

A full-stack financial analytics application that simulates trade monitoring, market data ingestion, and portfolio insights. Built to demonstrate backend engineering, data handling, and full-stack integration.

---

## 🚀 Features

* 📈 Market data API (mock + extensible to real data)
* 🧠 Backend built with FastAPI
* 🌐 Frontend built with React
* 🔌 RESTful API integration
* 🐳 Dockerized backend
* ⚡ Scalable architecture (extensible to real-time systems)

---

## 🛠 Tech Stack

| Layer    | Technology                      |
| -------- | ------------------------------- |
| Backend  | Python, FastAPI                 |
| Frontend | React                           |
| Data     | JSON (extensible to PostgreSQL) |
| DevOps   | Docker                          |
| API      | REST                            |

---

## ▶️ Run Locally

### Backend

```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🌐 API Endpoints

* `/` → Health check
* `/market-data` → Get stock prices

---

## 📊 Example Response

```json
[
  {"symbol": "AAPL", "price": 180},
  {"symbol": "TSLA", "price": 250},
  {"symbol": "GOOG", "price": 2700}
]
```

---

## 📸 Screenshot

*Add your screenshot here later*

---

## 🧠 What This Demonstrates

* Backend API design
* Full-stack integration
* Data handling and transformation
* Scalable system thinking
* Real-world financial system simulation

---

## 👤 Author

Jeremiah Arisekola-Ojo
