from sqlalchemy import create_engine, inspect
import os

from dotenv import load_dotenv

load_dotenv()

connection = os.getenv("PG_RDBMS_CONNECTION_STRING")

engine = create_engine(connection)

inspector = inspect(engine)

tables = inspector.get_table_names()

print("\n===== DATABASE TABLES =====")

for table in tables:
    print(table)