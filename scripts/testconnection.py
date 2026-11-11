
from sqlalchemy import create_engine, text

# Replace with your PostgreSQL password
DB_PASSWORD = "4256"

DATABASE_URL = (
    f"postgresql+psycopg2://postgres:{DB_PASSWORD}"
    "@localhost:5432/finguard_db"
)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT current_database();")
        )

        print("Connected successfully!")
        print("Database:", result.scalar())

except Exception as e:
    print("Connection failed:")
    print(e)
