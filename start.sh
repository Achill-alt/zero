#!/usr/bin/env bash
# ============================================================
#   Contract Management System  v1.2
#   Linux / macOS 一键启动脚本
# ============================================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""
LOGS_DIR="$ROOT/logs"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null && echo "  Backend stopped (PID $BACKEND_PID)"
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null && echo "  Frontend stopped (PID $FRONTEND_PID)"
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  Contract Management System  v1.2${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# ---- Clean up stale processes on target ports ----
echo -e "${YELLOW}[INFO]${NC} Checking port availability..."
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "  Port 8000 occupied, attempting to free..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi
if lsof -ti:5173 >/dev/null 2>&1; then
    echo "  Port 5173 occupied, attempting to free..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
fi

# ---- Check Python ----
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Python not found. Install Python 3.11+ first."
    exit 1
fi
PYTHON=$(command -v python3 || command -v python)
echo -e "${GREEN}[OK]${NC} $($PYTHON --version)"

# ---- Check Node.js ----
if ! command -v node &>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Node.js not found. Install Node.js 18+ first."
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Node $(node --version)"

# ---- Install backend deps if missing ----
$PYTHON -c "import fastapi, uvicorn, sqlalchemy" 2>/dev/null || {
    echo -e "${YELLOW}[INFO]${NC} Installing backend dependencies..."
    $PYTHON -m pip install -r "$ROOT/backend/requirements.txt" -q
}

# ---- Install frontend deps if missing ----
if [ ! -d "$ROOT/frontend/node_modules" ]; then
    echo -e "${YELLOW}[INFO]${NC} Installing frontend dependencies..."
    cd "$ROOT/frontend" && npm install --silent && cd "$ROOT"
fi

# ---- Init database if missing ----
if [ ! -f "$ROOT/backend/app.db" ]; then
    echo -e "${YELLOW}[INFO]${NC} Initializing database and seed data..."
    cd "$ROOT/backend" && $PYTHON seed.py && cd "$ROOT"
fi

# ---- Create logs directory ----
mkdir -p "$LOGS_DIR"

# ---- Copy .env if not present ----
if [ ! -f "$ROOT/backend/.env" ]; then
    cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
    echo -e "${YELLOW}[INFO]${NC} Created backend/.env from .env.example"
fi
if [ ! -f "$ROOT/frontend/.env" ]; then
    cp "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"
    echo -e "${YELLOW}[INFO]${NC} Created frontend/.env from .env.example"
fi

# ---- Start backend ----
echo ""
echo -e "${YELLOW}[INFO]${NC} Starting backend on port 8000..."
cd "$ROOT/backend"
$PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOGS_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
cd "$ROOT"

# ---- Start frontend ----
echo -e "${YELLOW}[INFO]${NC} Starting frontend on port 5173..."
cd "$ROOT/frontend"
npx vite --host 127.0.0.1 > "$LOGS_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$ROOT"

# ---- Wait for services ----
echo -e "${YELLOW}[INFO]${NC} Waiting for services to start..."
sleep 5

# ---- Open browser (optional) ----
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:5173 2>/dev/null || true
elif command -v open &>/dev/null; then
    open http://localhost:5173 2>/dev/null || true
fi

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
echo -e "  Frontend:  ${GREEN}http://localhost:5173${NC}"
echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Login:     ${GREEN}admin / admin123${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""
echo -e "  Press ${YELLOW}Ctrl+C${NC} to stop all services"
echo ""

# Wait for background processes
wait
