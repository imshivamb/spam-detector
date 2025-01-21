# Spam Detector API - Setup and Usage Manual

This document provides step-by-step instructions for setting up and using the Spam Detector API. Follow the instructions carefully to ensure a smooth installation and usage experience.

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

Ensure you have the following:

- Python version 3.8 or above
- PostgreSQL (via Neon DB or a local instance)
- pip (Python package manager)

## Setup Instructions

### Option 1: Using Neon DB (Cloud-Based PostgreSQL)

1. Sign up at [Neon.tech](https://neon.tech) and obtain your database connection URL.
2. Create a virtual environment for your project using Python.
3. Activate the virtual environment.
4. Install the required Python dependencies listed in the `requirements.txt` file.
5. Create a `.env` file in your project directory and configure the following environment variables:

   ```plaintext
   DJANGO_SECRET_KEY='django-insecure-4@w=9rk^&uzh187+1&=sr#dr#)4+c*ct0qnk=^s_n$_qp2Z3ix'
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL='your-neon-database-url'
   ```

### Option 2: Using Docker for a Local PostgreSQL Instance

1. Install Docker and Docker Compose on your system.
2. Set up a PostgreSQL instance using a `docker-compose.yml` file configured with the following settings:

   - Database: `spamdb`
   - Username: `postgres`
   - Password: `postgres`
   - Port: `5432`

3. Create a virtual environment for your project using Python.
4. Activate the virtual environment.
5. Install the required Python dependencies listed in the `requirements.txt` file.
6. Create a `.env` file in your project directory and configure the following environment variables:

   ```plaintext
   DJANGO_SECRET_KEY='anysecretkey'
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL='postgresql://postgres:postgres@localhost:5432/spamdb'
   ```

### Common Steps After Database Setup

1. Apply database migrations to set up the necessary tables.
2. Optionally, populate the database with test data using the provided data population script.
3. Start the Django development server to access the API.

## API Endpoints

### Authentication

- Register: `POST /api/auth/register/`
- Login: `POST /api/auth/login/`
- Refresh Token: `POST /api/auth/refresh/`
- Logout: `POST /api/auth/logout/`

### User Management

- View Profile: `GET /api/users/profile/`
- Update Profile: `PUT /api/users/profile/`
- Change Password: `POST /api/users/change-password/`
- Deactivate Account: `DELETE /api/users/deactivate/`

### Contact Management

- List Contacts: `GET /api/contacts/`
- Create Contact: `POST /api/contacts/`
- View Contact: `GET /api/contacts/{id}/`
- Update Contact: `PUT /api/contacts/{id}/`
- Delete Contact: `DELETE /api/contacts/{id}/`
- Bulk Create Contacts: `POST /api/contacts/bulk-create/`
- Search by Phone Number: `GET /api/contacts/phone/{number}/`

### Search

- Search by Name: `GET /api/search/name/?q={query}`
- Search by Phone Number: `GET /api/search/phone/?q={number}`

### Spam Management

- Report Spam: `POST /api/spam/report/`
- Retract Spam Report: `DELETE /api/spam/{number}/retract/`
- Check Spam Status: `GET /api/spam/status/{number}/`
- Spam Statistics: `GET /api/spam/statistics/`

## Testing

- Use the included data population script to generate test users, contacts, and spam reports for testing purposes.
- Ensure that phone numbers follow the E.164 format (e.g., `+1234567890`).

## Notes

- Email is optional for user accounts.
- All endpoints require user authentication except for register and login.
- If using Docker, ensure the `DATABASE_URL` in the `.env` file points to the local PostgreSQL instance.

For any issues or additional information, refer to the project documentation or contact the development team.

