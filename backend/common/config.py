import os
from pathlib import Path
from dotenv import load_dotenv

# Temukan file .env di root proyek
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
dotenv_path = ROOT_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()

class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Frontend
    PORT: int = int(os.getenv("PORT", 3000))
    NEXT_PUBLIC_APP_URL: str = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")

    # Server 1: RPC Transaksi
    SERVER1_RPC_PRIMARY_HOST: str = os.getenv("SERVER1_RPC_PRIMARY_HOST", "127.0.0.1")
    SERVER1_RPC_PRIMARY_PORT: int = int(os.getenv("SERVER1_RPC_PRIMARY_PORT", 6001))
    SERVER1_RPC_BACKUP_HOST: str = os.getenv("SERVER1_RPC_BACKUP_HOST", "127.0.0.1")
    SERVER1_RPC_BACKUP_PORT: int = int(os.getenv("SERVER1_RPC_BACKUP_PORT", 6101))
    SERVER1_RPC_HEARTBEAT_PORT: int = int(os.getenv("SERVER1_RPC_HEARTBEAT_PORT", 6201))

    # Server 2: RMI Stok
    SERVER2_RMI_PRIMARY_HOST: str = os.getenv("SERVER2_RMI_PRIMARY_HOST", "127.0.0.1")
    SERVER2_RMI_PRIMARY_PORT: int = int(os.getenv("SERVER2_RMI_PRIMARY_PORT", 6002))
    SERVER2_RMI_BACKUP_HOST: str = os.getenv("SERVER2_RMI_BACKUP_HOST", "127.0.0.1")
    SERVER2_RMI_BACKUP_PORT: int = int(os.getenv("SERVER2_RMI_BACKUP_PORT", 6102))
    SERVER2_RMI_HEARTBEAT_PORT: int = int(os.getenv("SERVER2_RMI_HEARTBEAT_PORT", 6202))

    # Server 3: REST API Katalog, Auth, Order
    SERVER3_API_PRIMARY_HOST: str = os.getenv("SERVER3_API_PRIMARY_HOST", "127.0.0.1")
    SERVER3_API_PRIMARY_PORT: int = int(os.getenv("SERVER3_API_PRIMARY_PORT", 6003))
    SERVER3_API_BACKUP_HOST: str = os.getenv("SERVER3_API_BACKUP_HOST", "127.0.0.1")
    SERVER3_API_BACKUP_PORT: int = int(os.getenv("SERVER3_API_BACKUP_PORT", 6103))
    SERVER3_API_HEARTBEAT_PORT: int = int(os.getenv("SERVER3_API_HEARTBEAT_PORT", 6203))

    # Server 4: Data Persisten & Replikasi
    SERVER4_DATA_PRIMARY_HOST: str = os.getenv("SERVER4_DATA_PRIMARY_HOST", "127.0.0.1")
    SERVER4_DATA_PRIMARY_PORT: int = int(os.getenv("SERVER4_DATA_PRIMARY_PORT", 6004))
    SERVER4_DATA_BACKUP_HOST: str = os.getenv("SERVER4_DATA_BACKUP_HOST", "127.0.0.1")
    SERVER4_DATA_BACKUP_PORT: int = int(os.getenv("SERVER4_DATA_BACKUP_PORT", 6104))
    SERVER4_DATA_REPLICATION_PORT: int = int(os.getenv("SERVER4_DATA_REPLICATION_PORT", 6204))

    # Engine Database
    DATABASE_ENGINE: str = os.getenv("DATABASE_ENGINE", "sqlite")
    DATABASE_SQLITE_PRIMARY_PATH: str = os.getenv("DATABASE_SQLITE_PRIMARY_PATH", str(ROOT_DIR / "backend" / "server4_data" / "primary_ecommerce.db"))
    DATABASE_SQLITE_BACKUP_PATH: str = os.getenv("DATABASE_SQLITE_BACKUP_PATH", str(ROOT_DIR / "backend" / "server4_data" / "backup_ecommerce.db"))

    # Parameter Toleransi Kesalahan
    HEARTBEAT_INTERVAL: float = float(os.getenv("HEARTBEAT_INTERVAL", 2.0))
    HEARTBEAT_TIMEOUT: float = float(os.getenv("HEARTBEAT_TIMEOUT", 5.0))
    MAX_MISSED_HEARTBEATS: int = int(os.getenv("MAX_MISSED_HEARTBEATS", 3))
    SOCKET_TIMEOUT: float = float(os.getenv("SOCKET_TIMEOUT", 1.5))

    # Keamanan JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super_secure_jwt_secret_key_sister_trunojoyo_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

settings = Settings()
