# Online Poll System Backend

## Overview

The **Online Poll System Backend** is a Django REST Framework project
designed to simulate a real-world voting platform.  
It provides APIs for **poll creation, voting, and real-time result
computation**, with secure **JWT authentication** and **role-based
access control**.

This backend is built to be scalable, efficient, and easy to integrate
with frontend applications.

---

## Major Functions & Features

### 🔑 Authentication & User Management

- **Custom User Model** based on email instead of username.
- Secure login/logout using **JWT authentication** (`djangorestframework-simplejwt`).
- Role-based access control (Admins can create/manage polls, Users can vote).

### 📊 Poll Management

- Create polls with multiple options.
- Each poll includes metadata (creation date, expiry date).

### 🗳️ Voting System

- Authenticated users can cast votes.
- Duplicate voting prevention per poll per user.

### 📈 Real-Time Result Computation

- Instant tally of votes for each poll option.
- Optimized PostgreSQL queries for scalability.

### 📖 API Documentation

- Endpoints documented using **Swagger/OpenAPI**.
- Accessible at `/api/docs/` after deployment.

---

## Tech Stack

- **Django REST Framework (DRF)** -- API development
- **PostgreSQL** -- Relational database for poll & vote storage
- **djangorestframework-simplejwt** -- JWT authentication
- **Swagger (drf-yasg)** -- API documentation
- **Gunicorn + Nginx** -- Production deployment

---

## Key Endpoints (Examples)

- `POST /api/token/` -- Obtain JWT token
- `POST /api/token/refresh/` -- Refresh JWT token
- `POST /api/polls/` -- Create a new poll (Admin only)
- `GET /api/polls/` -- List all polls
- `POST /api/polls/{id}/vote/` -- Cast a vote (Authenticated users)
- `GET /api/polls/{id}/results/` -- Get real-time results of a poll
- `POST /api/register/` -- Register a new user
- `POST /api/login/` -- Login and obtain JWT token
- `GET /api/users/` -- List users (Admin only)

---

## Installation & Setup (Development)

1. Clone the repository:
    ```bash
    git clone <repository_url>
    cd Online_Poll_System
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv polls_venv
    source polls_venv/bin/activate   # Linux / WSL2
    polls_venv\Scripts\activate      # Windows
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Apply migrations:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5. Run the development server:
    ```bash
    python manage.py runserver
    ```

---

## API Usage (Examples)

### Register a User
```bash
POST /api/register/
{
    "first_name": "John",
    "surname": "Doe",
    "email": "john@example.com",
    "confirm_email": "john@example.com",
    "password": "MySecret123",
    "confirm_password": "MySecret123"
}
