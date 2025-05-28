# init_db.py
from app.auth.database import Base, engine
from app.auth.models import User, QueryLog

Base.metadata.create_all(bind=engine)
print("✅ Tables created.")
