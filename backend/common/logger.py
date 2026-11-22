import logging
import sys
from datetime import datetime

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        time_str = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Penanda level & service tag
        levelname = record.levelname
        msg = record.getMessage()

        if record.levelno >= logging.ERROR:
            color = RED + BOLD
        elif record.levelno >= logging.WARNING:
            color = YELLOW
        elif "[PROMOTION]" in msg or "[FAILOVER]" in msg:
            color = GREEN + BOLD
        elif "[HEARTBEAT]" in msg:
            color = MAGENTA
        elif "[COORDINATOR]" in msg or "[PRIMARY]" in msg:
            color = CYAN
        elif "[FOLLOWER]" in msg or "[STANDBY]" in msg:
            color = YELLOW
        else:
            color = WHITE

        prefix = f"{DIM}{time_str}{RESET} {color}[{levelname}]{RESET} {BOLD}{record.name}{RESET}: "
        return prefix + msg

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger
