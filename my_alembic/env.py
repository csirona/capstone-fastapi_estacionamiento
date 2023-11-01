from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context
from db import Base  # Import your Base class and any other necessary modules
from sqlalchemy import MetaData
# Create a MetaData object
metadata = MetaData()

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
url = config.get_main_option("sqlalchemy.url")

# Create the SQLAlchemy engine directly from the DATABASE_URL
engine = create_engine(url, echo=True)  # Replace echo=True with your desired logging level
Base.metadata.bind = engine

# Set the metadata in the Alembic context
context.configure(
    url=url, target_metadata=metadata, literal_binds=False, dialect_opts={"paramstyle": "named"}
)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata to your metadata object
target_metadata = metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
