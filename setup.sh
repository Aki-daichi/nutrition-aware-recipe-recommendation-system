#!/bin/bash
# Quick setup script for Linux/macOS

echo "🍽️  Nutrition-Aware Recipe Recommendation System - Setup"
echo "=================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )(.*)' | cut -d'.' -f1,2)
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Copy environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file (edit with your database credentials)"
else
    echo "✓ .env file already exists"
fi

# Initialize database
echo "Initializing database..."
python -c "from backend.database import init_db; init_db()"
echo "✓ Database initialized"

# Seed sample data
echo "Seeding database with sample data..."
python seed_db.py
echo "✓ Sample data added"

echo ""
echo "=================================================="
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials (if needed)"
echo "2. Run the server: python backend/main.py"
echo "3. Visit: http://localhost:8000/dashboard"
echo ""
echo "To activate virtual environment in future:"
echo "  source venv/bin/activate"
echo "=================================================="
