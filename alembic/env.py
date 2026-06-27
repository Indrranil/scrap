from logging.config import fileConfig
from os import getenv

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from app.database.connection import Base
from app.models import (  # noqa: F401
    AdminUser,
    EmployeeProfile,
    ItemMaster,
    Plant,
    RejectionDetail,
    ScrapSale,
    Scrapeyard,
    Transfer,
    TransferEvent,
    Vendor,
    VendorItem,
)

load_dotenv()

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

if getenv("TESTING") == "1":
    db_url = "sqlite:///./test.db"
else:
    db_url = (
        f"mysql+pymysql://{getenv('MYSQL_USER')}:{getenv('MYSQL_PASSWORD')}"
        f"@{getenv('MYSQL_HOST')}:{getenv('MYSQL_PORT')}/{getenv('MYSQL_DATABASE')}"
    )
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
