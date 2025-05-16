# Book Management System

A modern book management system built with FastAPI and PostgreSQL, featuring Google OAuth authentication, role-based access control, and semantic search capabilities.

## Features

### Authentication & Authorization
- Google OAuth 2.0 integration for secure authentication
- Role-based access control with three levels:
  - CUSTOMER (default): Can browse, search, and checkout books
  - LIBRARIAN: Additional privileges for book management
  - SUPERUSER: Full system access and user management

### Book Management
- Complete CRUD operations for books
- Book checkout and return system
- Semantic search using FAISS and OpenAI embeddings
- Basic search by title, author, or ISBN
- Book availability tracking
- Due date management

### User Management
- User profiles with Google integration
- Role management for administrators
- Activity tracking for checked-out books

## Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Database**: PostgreSQL
- **Authentication**: Google OAuth 2.0
- **Search**: FAISS for semantic search
- **Frontend**: Streamlit

## API Endpoints

### Authentication
- `GET /api/v1/auth/login` - Initiate Google OAuth login
- `GET /api/v1/auth/callback` - OAuth callback handler

### Books
- `GET /api/v1/books` - List all books
- `GET /api/v1/books/my-books` - List user's checked out books
- `POST /api/v1/books` - Create a new book (Librarian/Superuser only)
- `GET /api/v1/books/{book_id}` - Get book details
- `PUT /api/v1/books/{book_id}` - Update book details (Librarian/Superuser only)
- `DELETE /api/v1/books/{book_id}` - Delete a book (Librarian/Superuser only)
- `POST /api/v1/books/{book_id}/checkout` - Checkout a book
- `POST /api/v1/books/{book_id}/checkin` - Return a book

### Search
- `GET /api/v1/books/search/{query}` - Basic search by title/author/ISBN
- `GET /api/v1/search/semantic/{query}` - Semantic search using FAISS

### Users
- `GET /api/v1/users` - List all users (Librarian/Superuser only)
- `GET /api/v1/users/{user_id}` - Get user details (Librarian/Superuser only)
- `PUT /api/v1/users/{user_id}/role` - Update user role (Superuser only)

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd book_management
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `GOOGLE_CLIENT_ID`: OAuth client ID
- `GOOGLE_CLIENT_SECRET`: OAuth client secret
- `SECRET_KEY`: JWT secret key
- `OPENAI_API_KEY`: For semantic search functionality

5. Initialize the database:
```bash
alembic upgrade head
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

7. Run the Streamlit frontend:
```bash
cd streamlit_app
streamlit run Home.py
```

## Development

### Database Migrations

To create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:
```bash
alembic upgrade head
```

### Adding a New Feature

1. Create necessary database models in `app/db/models/`
2. Create corresponding schemas in `app/schemas/`
3. Add CRUD operations in `app/crud/`
4. Create API endpoints in `app/api/routes/`
5. Update documentation

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- FastAPI for the excellent web framework
- Streamlit for the intuitive frontend framework
- OpenAI for embeddings support
- FAISS for efficient similarity search
