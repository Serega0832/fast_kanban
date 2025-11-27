from sqlmodel import SQLModel, Session, create_engine

# Название файла базы данных
sqlite_file_name = "kanban.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False нужен для SQLite в FastAPI
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session