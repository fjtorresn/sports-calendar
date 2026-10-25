from datetime import UTC, datetime, timedelta

from app.core.database import SessionLocal
from app.models.event import Event, EventParticipant
from app.models.sports import Sport


def seed_events():
    db = SessionLocal()

    try:
        football = db.query(Sport).filter(Sport.name == "Football").first()
        tennis = db.query(Sport).filter(Sport.name == "Tennis").first()

        if not football or not tennis:
            print("❌ Base sports are missing. Run 'python seed.py' first.")
            return

        if db.query(Event).first():
            print("⚠️ Deleting existing events...")
            db.query(EventParticipant).delete()
            db.query(Event).delete()
            db.commit()

        print("📅 Seeding events...")

        now_utc = datetime.now(UTC)
        yesterday = now_utc - timedelta(days=1)
        tomorrow = now_utc + timedelta(days=1)

        event_football = Event(sport_id=football.id, start_time=tomorrow, status="scheduled", result_details=None)
        db.add(event_football)
        db.commit()
        db.refresh(event_football)

        participants_football = [
            EventParticipant(event_id=event_football.id, participant_type="team", participant_id=1, is_home=True),
            EventParticipant(event_id=event_football.id, participant_type="team", participant_id=2, is_home=False),
        ]
        db.add_all(participants_football)

        event_tennis = Event(
            sport_id=tennis.id,
            start_time=yesterday,
            status="finished",
            result_details={"sets": [{"player_1": 6, "player_2": 4}, {"player_1": 7, "player_2": 5}], "winner_id": 3},
        )
        db.add(event_tennis)
        db.commit()
        db.refresh(event_tennis)

        participants_tennis = [
            EventParticipant(event_id=event_tennis.id, participant_type="player", participant_id=3, is_home=True),
            EventParticipant(event_id=event_tennis.id, participant_type="player", participant_id=4, is_home=False),
        ]
        db.add_all(participants_tennis)

        db.commit()
        print("✅ Events inserted.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al insertar eventos: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_events()
