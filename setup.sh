#!/bin/bash

# Simple wrapper script for backend setup
# Usage: ./setup.sh [options]

echo "🚀 Rental Management Backend Setup Helper"
echo "=========================================="

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "setup_backend.py" ]; then
    echo "❌ Please run this script from the rental-backend-fastapi directory"
    exit 1
fi

# Show options
echo "Choose setup option:"
echo "1) Fresh setup (drop existing database)"
echo "2) Update existing setup (keep existing database)" 
echo "3) Quick setup (fresh, skip tests)"
echo "4) Show help"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🔄 Running fresh setup with database drop..."
        poetry run python setup_backend.py --force-drop
        ;;
    2)
        echo "🔄 Running update on existing database..."
        poetry run python setup_backend.py
        ;;
    3)
        echo "🔄 Running quick fresh setup (no tests)..."
        poetry run python setup_backend.py --force-drop --skip-tests
        ;;
    4)
        echo "📖 Backend Setup Options:"
        echo ""
        echo "Available command line options:"
        echo "  poetry run python setup_backend.py --help"
        echo ""
        echo "Examples:"
        echo "  poetry run python setup_backend.py                    # Normal setup"
        echo "  poetry run python setup_backend.py --force-drop       # Fresh setup"
        echo "  poetry run python setup_backend.py --skip-tests       # Setup without tests"
        echo "  poetry run python setup_backend.py --force-drop --skip-tests  # Quick reset"
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "✅ Setup helper completed!"