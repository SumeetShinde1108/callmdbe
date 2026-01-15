#!/bin/bash

echo "🚀 Starting CallFairy Application..."
echo ""

# Check prerequisites
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "   Start with: sudo systemctl start redis"
    echo "   Or: redis-server"
    exit 1
fi

echo "✅ Redis is running"
echo ""

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is not installed!"
    echo "   Install with: sudo apt install tmux -y"
    exit 1
fi

# Kill existing session if it exists
tmux has-session -t callfairy 2>/dev/null
if [ $? -eq 0 ]; then
    echo "⚠️  Existing CallFairy session found. Killing it..."
    tmux kill-session -t callfairy
fi

echo "🔄 Starting services in tmux session..."
echo ""

# Create new session
tmux new -s callfairy -d

# Window 0: Django
tmux rename-window -t callfairy:0 'Django'
tmux send-keys -t callfairy:0 "cd /home/rootmaster/PycharmProjects/callmdbe-main" C-m
tmux send-keys -t callfairy:0 "source .venv/bin/activate" C-m
tmux send-keys -t callfairy:0 "echo '🌐 Starting Django Server...'" C-m
tmux send-keys -t callfairy:0 "python manage.py runserver" C-m

# Window 1: Celery
tmux new-window -t callfairy:1 -n 'Celery'
tmux send-keys -t callfairy:1 "cd /home/rootmaster/PycharmProjects/callmdbe-main" C-m
tmux send-keys -t callfairy:1 "sleep 3" C-m  # Wait for Django to start
tmux send-keys -t callfairy:1 "bash start_celery.sh" C-m

# Give services time to start
sleep 5

echo "✅ Services started successfully!"
echo ""
echo "📊 View logs:"
echo "   tmux attach -t callfairy"
echo ""
echo "   Navigation:"
echo "   - Switch windows: Ctrl+B then 0 (Django) or 1 (Celery)"
echo "   - Detach: Ctrl+B then D"
echo ""
echo "🛑 Stop all services:"
echo "   tmux kill-session -t callfairy"
echo ""
echo "🌐 Access application:"
echo "   http://localhost:8000/"
echo ""
echo "🎉 CallFairy is ready!"
