from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Crear el engine de la base de datos
engine = create_engine(settings.DATABASE_URL,
                       pool_pre_ping=True,)

# Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear la base para los modelos
Base = declarative_base()

def drop_all_tables():
    """Eliminar todas las tablas"""
    try:
        Base.metadata.drop_all(bind=engine, checkfirst=True)
        logger.info("Tablas eliminadas correctamente")
    except Exception as e:
        logger.error(f"Error eliminando tablas: {e}")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename NOT LIKE 'pg_%' 
                    AND tablename NOT LIKE 'sql_%'
                """))
                tables = [row[0] for row in result]
                
                for table in tables:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                
                conn.commit()
                logger.info("Tablas eliminadas")
        except Exception as e2:
            logger.error(f"Error: {e2}")
            raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()