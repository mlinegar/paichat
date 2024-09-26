# manage_db.py
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import ProgrammingError
from models import Base
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_tables():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if not existing_tables:
        Base.metadata.create_all(engine)
        print(f"Tables created in database '{DB_NAME}'.")
    else:
        print(f"Tables already exist in database '{DB_NAME}'.")

def drop_tables():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if existing_tables:
        Base.metadata.drop_all(engine)
        print(f"All tables dropped from database '{DB_NAME}'.")
    else:
        print(f"No tables found in database '{DB_NAME}'.")

def recreate_tables():
    drop_tables()
    create_tables()
    print(f"Tables recreated in database '{DB_NAME}'.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python manage_db.py [create|drop|recreate]")
    else:
        action = sys.argv[1]
        try:
            if action == 'create':
                create_tables()
            elif action == 'drop':
                drop_tables()
            elif action == 'recreate':
                recreate_tables()
            else:
                print("Invalid action. Use create, drop, or recreate.")
        except ProgrammingError as e:
            print(f"An error occurred: {e}")
            print("Make sure the database exists and you have the necessary permissions.")