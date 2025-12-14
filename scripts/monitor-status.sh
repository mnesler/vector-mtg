#!/bin/bash
# Real-time process and command monitor for Claude Code workflow

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

while true; do
    clear
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         CLAUDE CODE WORKFLOW DASHBOARD                   ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo -e "${CYAN}Updated: $(date '+%Y-%m-%d %H:%M:%S')${NC}\n"

    # Active Claude Code Agents/Processes
    echo -e "${YELLOW}┌─ Claude Code Agents ─────────────────────────────────────┐${NC}"
    CLAUDE_PROCS=$(ps aux | grep -E "claude|node.*claude" | grep -v grep)
    if [ -z "$CLAUDE_PROCS" ]; then
        echo -e "${RED}  ✗ No active Claude Code processes${NC}"
    else
        echo "$CLAUDE_PROCS" | awk '{printf "  '"${GREEN}"'✓'"${NC}"' PID: '"${CYAN}"'%-8s'"${NC}"' CPU: '"${YELLOW}"'%-6s'"${NC}"' MEM: '"${MAGENTA}"'%-6s'"${NC}"'\n    %s\n", $2, $3"%", $4"%", substr($0, index($0,$11))}'
    fi
    echo -e "${YELLOW}└──────────────────────────────────────────────────────────┘${NC}\n"

    # Running Commands & Scripts
    echo -e "${YELLOW}┌─ Active Commands & Scripts ──────────────────────────────┐${NC}"
    ACTIVE_CMDS=$(ps aux | grep -E "(bash|python|node|npm|git)" | grep -v grep | grep -v "monitor-status" | head -10)
    if [ -z "$ACTIVE_CMDS" ]; then
        echo -e "  ${RED}No active commands${NC}"
    else
        echo "$ACTIVE_CMDS" | awk '{
            cmd = substr($0, index($0,$11))
            if (length(cmd) > 50) cmd = substr(cmd, 1, 47) "..."
            printf "  '"${GREEN}"'●'"${NC}"' [%s] %s\n", $2, cmd
        }'
    fi
    echo -e "${YELLOW}└──────────────────────────────────────────────────────────┘${NC}\n"

    # Python/Training Processes
    echo -e "${YELLOW}┌─ Python Training/Inference ──────────────────────────────┐${NC}"
    PYTHON_PROCS=$(ps aux | grep python | grep -E "(train|inference|test_qwen|format)" | grep -v grep)
    if [ -z "$PYTHON_PROCS" ]; then
        echo -e "  ${RED}No training/inference running${NC}"
    else
        echo "$PYTHON_PROCS" | awk '{
            cmd = substr($0, index($0,$11))
            if (length(cmd) > 50) cmd = substr(cmd, 1, 47) "..."
            printf "  '"${GREEN}"'▶'"${NC}"' PID: '"${CYAN}"'%-8s'"${NC}"' CPU: '"${YELLOW}"'%-6s'"${NC}"' MEM: '"${MAGENTA}"'%-6s'"${NC}"'\n    %s\n", $2, $3"%", $4"%", cmd
        }'
    fi
    echo -e "${YELLOW}└──────────────────────────────────────────────────────────┘${NC}\n"

    # GPU Status
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${YELLOW}┌─ GPU Status ─────────────────────────────────────────────┐${NC}"
        nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | \
        awk -F', ' '{
            util_color = ($4 > 80) ? "'"${RED}"'" : ($4 > 50) ? "'"${YELLOW}"'" : "'"${GREEN}"'"
            printf "  GPU %s: '"${CYAN}"'%s'"${NC}"'\n", $1, $2
            printf "    Temp: '"${YELLOW}"'%s°C'"${NC}"' | Util: "util_color"%s%%'"${NC}"' | Mem: '"${MAGENTA}"'%s/%s MB'"${NC}"'\n", $3, $4, $5, $6
        }'
        echo -e "${YELLOW}└──────────────────────────────────────────────────────────┘${NC}\n"
    fi

    # System Resources
    echo -e "${YELLOW}┌─ System Resources ───────────────────────────────────────┐${NC}"
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    CPU_COLOR=$(echo "$CPU_USAGE > 80" | bc -l 2>/dev/null | grep -q 1 && echo "${RED}" || (echo "$CPU_USAGE > 50" | bc -l 2>/dev/null | grep -q 1 && echo "${YELLOW}" || echo "${GREEN}"))
    echo -e "  CPU Usage: ${CPU_COLOR}${CPU_USAGE}%${NC}"
    echo -e "  Memory: ${MAGENTA}$(free -h | awk '/^Mem:/ {printf "%s / %s (%.1f%%)", $3, $2, ($3/$2)*100}')${NC}"
    echo -e "  Disk: ${CYAN}$(df -h / | awk 'NR==2 {printf "%s / %s (%s)", $3, $2, $5}')${NC}"
    echo -e "  Load Avg: ${YELLOW}$(uptime | awk -F'load average:' '{print $2}')${NC}"
    echo -e "${YELLOW}└──────────────────────────────────────────────────────────┘${NC}\n"

    # Background Jobs
    echo -e "${YELLOW}┌─ Background Jobs ────────────────────────────────────────┐${NC}"
    JOBS=$(jobs -l 2>/dev/null)
    if [ -z "$JOBS" ]; then
        echo -e "  ${RED}No background jobs${NC}"
    else
        echo "$JOBS"
    fi
    echo -e "${YELLOW}└──────────────────────────────────────────────────────────┘${NC}\n"

    echo -e "${GREEN}[Press Ctrl+C to exit]${NC}"

    sleep 2
done
