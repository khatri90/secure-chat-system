# Secure Chat Application

A robust and secure real-time messaging platform built with Django Channels and React. This application provides a seamless chat experience with enterprise-grade security features.


## Features

- **Real-Time Messaging:** Instant message delivery using WebSockets (Django Channels).
- **Secure Authentication:** JWT-based authentication for secure API access.
- **Microservices Architecture:** Decoupled backend and frontend for scalability.
- **Database Integration:** Reliable data storage using MySQL.
- **Modern Frontend:** Responsive and interactive UI built with React and Tailwind CSS.
- **Security First:** Environment variable configuration for insensitive data protection.

## Tech Stack

### Backend
- **Framework:** Django & Django REST Framework
- **Real-Time:** Django Channels (WebSocket support)
- **Database:** MySQL
- **Authentication:** SimpleJWT

### Frontend
- **Framework:** React
- **Styling:** Tailwind CSS
- **Build Tool:** Vite

## Project Structure

```
Crypto/
├── chat_backend/       # Django Backend
│   ├── chat_backend/   # Project Configuration
│   ├── chat/           # Chat Application Logic
│   └── accounts/       # User Authentication
├── front/              # React Frontend
│   ├── src/            # Source Code
│   └── public/         # Static Assets
└── .gitignore          # Git Configuration
```

## Getting Started

Follow these instructions to set up the project locally.

### Prerequisites

- Python 3.8+
- Node.js 14+
- MySQL Server

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd chat_backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/MacOS
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If `requirements.txt` is missing, install manually: `django daphne channels djangorestframework djangorestframework-simplejwt mysqlclient django-cors-headers`*

4.  **Configure Environment Variables:**
    Create a `.env` file in the `chat_backend` folder (same level as `manage.py`) and add:
    ```env
    SECRET_KEY=your_secure_random_secret_key
    DEBUG=True
    DB_NAME=secure_chat_db
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=localhost
    DB_PORT=3306
    ```

5.  **Run Migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Start the Development Server:**
    ```bash
    python manage.py runserver
    ```

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd ../front
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Start the Development Server:**
    ```bash
    npm run dev
    ```

## Usage

1.  Open your browser and navigate to the frontend URL (usually `http://localhost:5173`).
2.  Register a new account or log in.
3.  Start chatting in real-time!

## Contribution

We welcome contributions! Please follow these steps:
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

Distributed under the MIT License. See `LICENSE` for more information.
