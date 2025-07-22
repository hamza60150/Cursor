#!/bin/bash

# Adaptive Job Application Bot API Startup Script

echo "🚀 Starting Adaptive Job Application Bot API Server..."
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs cookies screenshots reports backups

# Load environment variables
if [ -f .env ]; then
    echo "⚙️  Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env file not found. Using default settings."
fi

# Set default values if not provided
export API_HOST=${API_HOST:-"0.0.0.0"}
export API_PORT=${API_PORT:-8000}
export LLM_PROVIDER=${LLM_PROVIDER:-"ollama"}
export LLM_MODEL=${LLM_MODEL:-"llama2"}

echo "🌐 API Configuration:"
echo "   Host: $API_HOST"
echo "   Port: $API_PORT"
echo "   LLM Provider: $LLM_PROVIDER"
echo "   LLM Model: $LLM_MODEL"

# Check if Ollama is running (if using Ollama)
if [ "$LLM_PROVIDER" = "ollama" ]; then
    echo "🤖 Checking Ollama status..."
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "⚠️  Warning: Ollama not running. Starting Ollama..."
        ollama serve &
        sleep 5
        
        # Check if model exists
        if ! ollama list | grep -q "$LLM_MODEL"; then
            echo "📥 Pulling $LLM_MODEL model..."
            ollama pull "$LLM_MODEL"
        fi
    else
        echo "✅ Ollama is running"
    fi
fi

# Start the API server
echo ""
echo "🚀 Starting API server on http://$API_HOST:$API_PORT"
echo "📊 Health check: http://$API_HOST:$API_PORT/api/health"
echo "📖 API documentation available at endpoints:"
echo "   POST /api/apply-job - Start job application"
echo "   GET  /api/session/{id}/status - Check status"
echo "   POST /api/session/{id}/cancel - Cancel session"
echo "   GET  /api/sessions - List all sessions"
echo "   POST /api/test-connection - Test website connection"
echo "   POST /api/parse-resume - Parse resume data"
echo "   POST /api/analyze-website - Analyze website HTML"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="

# Start the server
python3 web_api_interface.py

echo ""
echo "🛑 API server stopped."
