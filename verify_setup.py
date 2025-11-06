#!/usr/bin/env python3
"""
Script to verify the Board Management Tool setup
"""
import os
import sys
import subprocess
from pathlib import Path

def check_command(command: str, name: str) -> bool:
    """Check if a command exists"""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        print(f"✓ {name} is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"✗ {name} is NOT installed")
        return False

def check_file(file_path: str, name: str) -> bool:
    """Check if a file exists"""
    if Path(file_path).exists():
        print(f"✓ {name} exists")
        return True
    else:
        print(f"✗ {name} does NOT exist")
        return False

def check_env_var(var_name: str, env_file: str = None) -> bool:
    """Check if an environment variable is set"""
    if env_file and Path(env_file).exists():
        # Read from .env file
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == var_name and value.strip():
                            print(f"✓ {var_name} is set in {env_file}")
                            return True
        print(f"✗ {var_name} is NOT set in {env_file}")
        return False
    elif os.getenv(var_name):
        print(f"✓ {var_name} is set")
        return True
    else:
        print(f"✗ {var_name} is NOT set")
        return False

def main():
    print("Board Management Tool - Setup Verification")
    print("=" * 60)

    all_good = True

    # Check prerequisites
    print("\n1. Checking Prerequisites...")
    all_good &= check_command("python3", "Python 3")
    all_good &= check_command("node", "Node.js")
    all_good &= check_command("npm", "npm")
    all_good &= check_command("psql", "PostgreSQL client")

    # Check project structure
    print("\n2. Checking Project Structure...")
    all_good &= check_file("backend/app/main.py", "Backend main.py")
    all_good &= check_file("backend/requirements.txt", "Backend requirements.txt")
    all_good &= check_file("frontend/package.json", "Frontend package.json")
    all_good &= check_file("backend/alembic.ini", "Alembic config")

    # Check environment files
    print("\n3. Checking Environment Configuration...")
    backend_env_exists = check_file("backend/.env", "Backend .env")
    frontend_env_exists = check_file("frontend/.env.local", "Frontend .env.local")

    if not backend_env_exists:
        print("  → Copy backend/.env.example to backend/.env")
    if not frontend_env_exists:
        print("  → Copy frontend/.env.example to frontend/.env.local")

    all_good &= backend_env_exists and frontend_env_exists

    # Check critical environment variables
    if backend_env_exists:
        print("\n4. Checking Environment Variables...")
        all_good &= check_env_var("DATABASE_URL", "backend/.env")
        all_good &= check_env_var("SECRET_KEY", "backend/.env")
        all_good &= check_env_var("ANTHROPIC_API_KEY", "backend/.env")

    # Check dependencies
    print("\n5. Checking Dependencies...")
    backend_venv = check_file("backend/venv/bin/python", "Backend virtual environment") or \
                   check_file("backend/venv/Scripts/python.exe", "Backend virtual environment")
    frontend_modules = check_file("frontend/node_modules", "Frontend node_modules")

    if not backend_venv:
        print("  → Run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
    if not frontend_modules:
        print("  → Run: cd frontend && npm install")

    all_good &= backend_venv and frontend_modules

    # Summary
    print("\n" + "=" * 60)
    if all_good:
        print("✓ All checks passed! Your setup looks good.")
        print("\nNext steps:")
        print("1. Run database migrations: cd backend && source venv/bin/activate && alembic upgrade head")
        print("2. Create admin user: python create_admin.py")
        print("3. Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        print("4. Start frontend: cd frontend && npm run dev")
        return 0
    else:
        print("✗ Some checks failed. Please review the issues above.")
        print("\nRefer to SETUP.md for detailed instructions.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
