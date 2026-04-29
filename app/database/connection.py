import logging
import time
from os import getenv

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if getenv("TESTING") == "1":
    DATABASE_URL = "sqlite:///./test.db"
else:
    DATABASE_URL = f"mysql+pymysql://{getenv('MYSQL_USER')}:{getenv('MYSQL_PASSWORD')}@{getenv('MYSQL_HOST')}:{getenv('MYSQL_PORT')}/{getenv('MYSQL_DATABASE')}"

engine = create_engine(DATABASE_URL, pool_size=50, max_overflow=0)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_app_db_connection(session=SessionLocal, name="App Database"):
    start_time = time.time()
    try:
        db = session()
        version = db.execute(text("SELECT VERSION()")).scalar()
        connect_time = time.time() - start_time
        logger.info(f"\n {name} Connection Details:")
        logger.info("Status: Connected successfully")
        logger.info(f"Version: {version}")
        logger.info(f"Connection time: {connect_time:.3f}s\n")
        return True
    except Exception as e:
        logger.error(f"App database connection failed: {e}")
    return False


def verify_all_connections():
    app_db_status = test_app_db_connection()
    return app_db_status


if __name__ == "__main__":
    verify_all_connections()
