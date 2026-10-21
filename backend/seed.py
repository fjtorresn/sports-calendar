from src.app.core.database import SessionLocal
from src.app.models.sports import Nation, Sport, Competition, Team, Player
from src.app.models.event import Event, EventParticipant
from src.app.models.user import User, UserPreference

def seed_data():
    # Abrimos una sesión con la base de datos
    db = SessionLocal()
    
    try:
        # Verificamos si ya hay naciones para no duplicar datos si corres el script 2 veces
        if db.query(Nation).first():
            print("⚠️ La base de datos ya contiene datos. Saliendo del seeder...")
            return

        print("🌱 Iniciando la siembra de datos...")

        # 1. Insertar Naciones
        nations = [
            Nation(name="Chile", iso_code="CHI", flag_url="https://flagcdn.com/w320/cl.png"),
            Nation(name="Argentina", iso_code="ARG", flag_url="https://flagcdn.com/w320/ar.png"),
            Nation(name="España", iso_code="ESP", flag_url="https://flagcdn.com/w320/es.png"),
            Nation(name="México", iso_code="MEX", flag_url="https://flagcdn.com/w320/mx.png"),
            Nation(name="Inglaterra", iso_code="ENG", flag_url="https://flagcdn.com/w320/gb-eng.png")
        ]
        db.add_all(nations)

        # 2. Insertar Deportes
        sports = [
            Sport(name="Fútbol", participant_type="team"),
            Sport(name="Tenis", participant_type="player"),
            Sport(name="Fórmula 1", participant_type="mixed")
        ]
        db.add_all(sports)

        # Guardamos los cambios físicamente en la base de datos
        db.commit()
        print("✅ ¡Naciones y Deportes insertados correctamente!")

    except Exception as e:
        # Si algo falla, revertimos cualquier cambio a la mitad para no corromper la BD
        db.rollback()
        print(f"❌ Error al insertar datos: {e}")
    finally:
        # Siempre cerramos la conexión al terminar
        db.close()

if __name__ == "__main__":
    seed_data()