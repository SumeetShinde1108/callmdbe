#!/bin/bash

# Start Celery Worker and Beat for CallFairy

echo "Starting Celery Worker and Beat for CallFairy..."
echo "Make sure Redis is running before starting Celery!"
echo ""

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: Redis is not running!"
    echo "Start Redis with: redis-server"
    exit 1
fi

echo "Redis is running ✓"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

echo "Starting Celery Worker..."
echo "To stop: Press Ctrl+C"
echo ""

# Start Celery worker
celery -A callfairy.core worker --loglevel=info