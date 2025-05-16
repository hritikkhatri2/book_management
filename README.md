# Book Management System

A FastAPI-based book management system with Google OAuth authentication and semantic search capabilities.

## Features

- Book Management (CRUD operations)
- Check-in/Check-out functionality
- Google OAuth2 Authentication
- Semantic Search using FAISS and OpenAI embeddings
- PostgreSQL database
- Docker support

## Prerequisites

- Python 3.11+
- PostgreSQL
- Docker and Docker Compose (optional)
- Google OAuth2 credentials
- OpenAI API key

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/book_management

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# App Settings
APP_NAME=Book Management System
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
PROJECT_NAME=Book Management API
API_V1_STR=/api/v1
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd book-management
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run database migrations:
```bash
alembic upgrade head
```

## Running the Application

### Using Python

```bash
uvicorn app.main:app --reload
```

### Using Docker

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `GET /api/v1/auth/login` - Initiate Google OAuth login
- `GET /api/v1/auth/callback` - OAuth callback endpoint
- `GET /api/v1/auth/me` - Get current user info

### Books
- `GET /api/v1/books` - List all books
- `POST /api/v1/books` - Create a new book
- `GET /api/v1/books/{book_id}` - Get book details
- `PUT /api/v1/books/{book_id}` - Update book details
- `DELETE /api/v1/books/{book_id}` - Delete a book
- `POST /api/v1/books/{book_id}/checkout` - Checkout a book
- `POST /api/v1/books/{book_id}/checkin` - Check in a book

### Search
- `GET /api/v1/books/search/{query}` - Basic search by title/author/ISBN
- `GET /api/v1/search/semantic/{query}` - Semantic search using FAISS

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License.