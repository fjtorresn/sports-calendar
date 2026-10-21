from datetime import datetime, timedelta, timezone
from src.app.core.database import SessionLocal
from src.app.models.event import Event, EventParticipant
from src.app.models.sports import Sport
from src.app.models.user import *

def seed_events():
    db = SessionLocal()
    
    try:
        # Verificar que los deportes base existan
        futbol = db.query(Sport).filter(Sport.name == "Fútbol").first()
        tenis = db.query(Sport).filter(Sport.name == "Tenis").first()

        if not futbol or not tenis:
            print("❌ Faltan los deportes en la BD. Ejecuta 'python seed.py' primero.")
            return

        # Limpiar eventos anteriores si existen para evitar duplicados al testear
        if db.query(Event).first():
            print("⚠️ Limpiando eventos anteriores para aplicar el nuevo esquema...")
            db.query(EventParticipant).delete()
            db.query(Event).delete()
            db.commit()

        print("📅 Iniciando la siembra de Eventos actualizados...")

        now_utc = datetime.now(timezone.utc)
        ayer = now_utc - timedelta(days=1)
        manana = now_utc + timedelta(days=1)

        # 1. Evento de Fútbol (asignando el sport_id)
        evento_futbol = Event(
            sport_id=futbol.id,
            start_time=manana,
            status="scheduled",
            result_details=None 
        )
        db.add(evento_futbol)
        db.commit()
        db.refresh(evento_futbol)

        participantes_futbol = [
            EventParticipant(event_id=evento_futbol.id, participant_type="team", participant_id=1, is_home=True),
            EventParticipant(event_id=evento_futbol.id, participant_type="team", participant_id=2, is_home=False)
        ]
        db.add_all(participantes_futbol)

        # 2. Evento de Tenis (asignando el sport_id)
        evento_tenis = Event(
            sport_id=tenis.id,
            start_time=ayer,
            status="finished",
            result_details={
                "sets": [
                    {"player_1": 6, "player_2": 4},
                    {"player_1": 7, "player_2": 5}
                ],
                "winner_id": 3
            }
        )
        db.add(evento_tenis)
        db.commit()
        db.refresh(evento_tenis)

        participantes_tenis = [
            EventParticipant(event_id=evento_tenis.id, participant_type="player", participant_id=3, is_home=True),
            EventParticipant(event_id=evento_tenis.id, participant_type="player", participant_id=4, is_home=False)
        ]
        db.add_all(participantes_tenis)

        db.commit()
        print("✅ ¡Eventos con sport_id insertados correctamente!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar eventos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_events()