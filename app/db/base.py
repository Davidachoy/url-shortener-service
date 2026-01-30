# Este archivo es SOLO para que Alembic vea todos los models
from app.db.base_class import Base

# Importar todos los models aquí
from app.db.models.url import URL  # noqa: F401