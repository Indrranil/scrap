from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from os import getenv
from dotenv import load_dotenv
import logging
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = f"mysql+pymysql://{getenv('MYSQL_USER')}:{getenv('MYSQL_PASSWORD')}@localhost:3308/{getenv('MYSQL_DATABASE')}"
KEYCLOAK_DATABASE_URL = f"mysql+pymysql://{getenv('MYSQL_USER')}:{getenv('MYSQL_PASSWORD')}@localhost:3308/{getenv('MYSQL_DATABASE')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
keycloak_engine = create_engine(KEYCLOAK_DATABASE_URL)
KeycloakSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=keycloak_engine)
KeycloakBase = declarative_base()

def get_keycloak_db():
    db = KeycloakSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_app_db_connection(session=SessionLocal, name="App Database"):
    start_time = time.time()
    try:
        db = session()
        version = db.execute(text('SELECT VERSION()')).scalar()
        connect_time = time.time() - start_time
        logger.info(f"\n{name} Connection Details:")
        logger.info(f"Status: Connected successfully")
        logger.info(f"Version: {version}")
        logger.info(f"Connection time: {connect_time:.3f}s\n")
        return True
    except Exception as e:
        logger.error(f"App database connection failed: {e}")
        return False
    finally:
        db.close()

def test_keycloak_db_connection(session=KeycloakSessionLocal, name="Keycloak Database"):
    start_time = time.time()
    try:
        db = session()
        version = db.execute(text('SELECT VERSION()')).scalar()
        connect_time = time.time() - start_time
        logger.info(f"\n{name} Connection Details:")
        logger.info(f"Status: Connected successfully")
        logger.info(f"Version: {version}")
        logger.info(f"Connection time: {connect_time:.3f}s\n")
        return True
    except Exception as e:
        logger.error(f"{name} connection failed: {e}")
        return False
    finally:
        db.close()

def verify_all_connections():
    app_db_status = test_app_db_connection()
    keycloak_db_status = test_keycloak_db_connection()
    return app_db_status and keycloak_db_status

if __name__ == "__main__":
    verify_all_connections()