# Board Management Tool - Setup Guide

This guide will walk you through setting up the Board Management Tool development environment.

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **PostgreSQL 14+** - Database
- **Git** - Version control

## Step 1: Database Setup

### Install PostgreSQL

If you don't have PostgreSQL installed:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (using Homebrew)
brew install postgresql@14
brew services start postgresql@14
```

### Create Database and Enable pgvector

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE board_management_tool;
CREATE USER bmt_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE board_management_tool TO bmt_user;
\q

# Enable pgvector extension
sudo -u postgres psql board_management_tool
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### Install pgvector

pgvector is required for vector embeddings. Build from source:

```bash
# Install build dependencies
sudo apt-get install -y postgresql-server-dev-16 build-essential git

# Clone and build pgvector
cd /tmp
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Verify installation
psql -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
```

## Step 2: Backend Setup

### Create Python Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

Update the following in `.env`:

```bash
DATABASE_URL=postgresql://bmt_user:your_secure_password@localhost:5432/board_management_tool
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Run Database Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Create Admin User (Optional)

You can create a simple script to add an admin user or do it via psql:

```bash
python -c "
from app.core.security import get_password_hash
password_hash = get_password_hash('admin123')
print(f'INSERT INTO users (email, username, hashed_password, full_name, is_active, is_admin) VALUES (\\'admin@atlas.com\\', \\'admin\\', \\'{password_hash}\\', \\'Admin User\\', true, true);')
" | psql $DATABASE_URL
```

## Step 3: Frontend Setup

### Install Dependencies

```bash
cd ../frontend
npm install
```

### Configure Environment

```bash
# Copy example environment file
cp .env.example .env.local

# Edit if needed (defaults should work for local development)
nano .env.local
```

## Step 4: Run the Application

### Terminal 1 - Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at:
- App: http://localhost:3000

## Step 5: Verify Installation

1. Open http://localhost:8000/health - should return `{"status":"healthy"}`
2. Open http://localhost:8000/docs - should show API documentation
3. Open http://localhost:3000 - should show the frontend application

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Test connection
psql -U bmt_user -d board_management_tool -h localhost
```

### pgvector Extension Issues

```bash
# Verify pgvector is installed
psql board_management_tool -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# If not found, install as shown in Step 1
```

### Python Dependency Issues

```bash
# Ensure you're in the virtual environment
which python  # Should show path to venv

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Node Module Issues

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

Now that your development environment is set up, you can:

1. **Phase 2**: Implement authentication endpoints
2. **Phase 3**: Build document management features
3. **Phase 4**: Integrate Claude Agent SDK for AI chat
4. **Phase 5**: Polish and prepare for deployment

## Directory Structure Reference

```
bmt/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration and security
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app
│   ├── alembic/          # Database migrations
│   ├── storage/          # Document storage (auto-created)
│   ├── uploads/          # Temp uploads (auto-created)
│   ├── venv/            # Virtual environment
│   └── .env             # Environment variables
├── frontend/
│   ├── app/             # Next.js pages
│   ├── components/      # React components
│   ├── lib/            # Utilities
│   └── .env.local      # Environment variables
└── docs/               # Documentation
```

## Development Workflow

### Creating New Migrations

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Running Tests

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest

# Frontend tests
cd frontend
npm test
```

### Code Formatting

```bash
# Backend (install black first: pip install black)
cd backend
black app/

# Frontend
cd frontend
npm run lint
```

## Support

For issues or questions:
- Check the main README.md
- Review the project charter at PROJECT_CHARTER.md
- Contact the development team

## Security Notes

- Never commit `.env` files to version control
- Change default passwords in production
- Use strong SECRET_KEY in production
- Keep Anthropic API key secure
- Regularly update dependencies
