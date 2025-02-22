from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from os import getenv
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"mysql+pymysql://{getenv('MYSQL_USER')}:{getenv('MYSQL_PASSWORD')}@localhost:3308/{getenv('MYSQL_DATABASE')}"
KEYCLOAK_DATABASE_URL = "mysql+pymysql://root:rootpass@localhost:3308/keycloak_db"

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
        