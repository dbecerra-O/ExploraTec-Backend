import logging
from app.utils.seeder import run_seeder


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    confirm = input("ADVERTENCIA: Esto eliminará y recreará las tablas de la base de datos. ¿Desea continuar? (y/N): ")
    if confirm.lower() != 'y':
        logger.info("Cancelando...")
        return

    try:
        run_seeder()
    except Exception as e:
        logger.exception(f"Error ejecutando seeder: {e}")


if __name__ == "__main__":
    main()
