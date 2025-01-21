# Spam Detector API

A REST API for a mobile app that helps users identify spam numbers and search for contacts in a global database.

## Features

- User Authentication
- Contact Management
- Global Search (by name and phone number)
- Spam Reporting & Management

## Tech Stack

- Django + Django REST Framework
- PostgreSQL
- JWT Authentication

## Prerequisites

- Python 3.8+
- PostgreSQL (via Neon DB or Docker)
- pip

## Setup Instructions

You can either use Neon.tech for database hosting or set up a local PostgreSQL instance using Docker.

### Option 1: Using Neon DB

1. Get your database URL from [Neon.tech](https://neon.tech)

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```plaintext
DJANGO_SECRET_KEY='anysecretkey'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL='your-neon-database-url'
```

### Option 2: Using Docker

1. Start PostgreSQL using Docker:
```bash
docker-compose up -d
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```plaintext
DJANGO_SECRET_KEY='django-insecure-4@w=9rk^&uzh187+1&=sr#dr#)4+c*ct0qnk=^s_n$_qp2Z3ix'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL='postgresql://postgres:postgres@localhost:5432/spamdb'
```

### Common Steps (After Setting Up Database)

1. Run migrations:
```bash
python manage.py migrate
```

2. Populate test data (optional):
```bash
python populate_db.py
```

3. Run the server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication

- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Refresh token
- `POST /api/auth/logout/` - Logout user

### User Management

- `GET /api/users/profile/` - Get profile
- `PUT /api/users/profile/` - Update profile
- `POST /api/users/change-password/` - Change password
- `DELETE /api/users/deactivate/` - Deactivate account

### Contact Management

- `GET /api/contacts/` - List all contacts
- `POST /api/contacts/` - Create contact
- `GET /api/contacts/{id}/` - Get single contact
- `PUT /api/contacts/{id}/` - Update contact
- `PATCH /api/contacts/{id}/` - Partially update contact
- `DELETE /api/contacts/{id}/` - Delete contact
- `POST /api/contacts/bulk-create/` - Bulk create contacts
- `GET /api/contacts/phone/{number}/` - Get contact by phone number

### Search

- `GET /api/search/name/?q={query}` - Search by name
- `GET /api/search/phone/?q={number}` - Search by phone number

### Spam Management

- `POST /api/spam/report/` - Report a number as spam
- `DELETE /api/spam/{number}/retract/` - Retract spam report
- `GET /api/spam/status/{number}/` - Get spam status for number
- `GET /api/spam/statistics/` - Get spam statistics

## Testing

The project includes a data population script for testing:

```bash
python populate_db.py
```

This will create:

- Sample users with random phone numbers
- Contacts for each user
- Sample spam reports

## Notes

- All phone numbers should be in E.164 format (e.g., `+1234567890`)
- Email is optional for users
- Authentication is required for all endpoints except register/login

## Additional Notes

- If using Docker, make sure Docker and Docker Compose are installed on your system.
- The Docker setup creates a local PostgreSQL instance with the following credentials:
  - Database: `spamdb`
  - User: `postgres`
  - Password: `postgres`
  - Port: `5432`

You can switch between Neon DB and Docker by updating the `DATABASE_URL` in your `.env` file.

