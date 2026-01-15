#!/bin/bash

# Start Celery Beat for periodic tasks

echo "Starting Celery Beat for CallFairy..."
echo "Make sure Celery Worker is running in another terminal!"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

echo "Starting Celery Beat..."
echo "To stop: Press Ctrl+C"
echo ""

# Start Celery beat
celery -A callfairy.core beat --loglevel=info
