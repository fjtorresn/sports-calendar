from app.core.database import SessionLocal
from app.models.sports import Nation, Sport


def seed_data():
    db = SessionLocal()

    try:
        # Idempotent: running the seeder twice must not duplicate data.
        if db.query(Nation).first():
            print("⚠️ The database already has data. Skipping seed.")
            return

        print("🌱 Seeding data...")

        # 1. Insertar Naciones
        nations = [
            Nation(name="Chile", iso_code="CHI", flag_url="https://flagcdn.com/w320/cl.png"),
            Nation(name="Argentina", iso_code="ARG", flag_url="https://flagcdn.com/w320/ar.png"),
            Nation(name="Spain", iso_code="ESP", flag_url="https://flagcdn.com/w320/es.png"),
            Nation(name="Mexico", iso_code="MEX", flag_url="https://flagcdn.com/w320/mx.png"),
            Nation(name="England", iso_code="ENG", flag_url="https://flagcdn.com/w320/gb-eng.png"),
        ]
        db.add_all(nations)

        # 2. Insertar Deportes
        sports = [
            Sport(name="Football", participant_type="team"),
            Sport(name="Tennis", participant_type="player"),
            Sport(name="Formula 1", participant_type="mixed"),
        ]
        db.add_all(sports)

        db.commit()
        print("✅ Nations and sports inserted.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar datos: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
