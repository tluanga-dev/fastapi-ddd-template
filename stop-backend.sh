#!/bin/bash

# Stop all backend processes
echo "Stopping all backend processes..."

# Kill all uvicorn processes
pkill -f "uvicorn src.main:app"

# Kill any remaining Python processes running main.py
pkill -f "python.*main"

# Kill any remaining FastAPI processes
pkill -f "fastapi"

echo "Backend processes stopped."