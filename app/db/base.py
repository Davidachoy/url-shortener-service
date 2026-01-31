# This file exists so Alembic can discover all models
from app.db.base_class import Base

# Import all models here
from app.db.models.url import URL  # noqa: F401