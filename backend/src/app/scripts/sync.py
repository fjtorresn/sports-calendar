"""Sync competitions from their sources, synchronously (no worker needed).

Usage:
  uv run python -m app.scripts.sync --all                 # every competition with a source
  uv run python -m app.scripts.sync --followed            # only those with subscribers
  uv run python -m app.scripts.sync --competition la-liga
"""

import argparse
import logging
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.ingestion.base import ProviderError
from app.ingestion.runner import followed_competition_ids, sync_from_all_sources, syncable_competition_ids
from app.ingestion.sync import SyncError
from app.models import Competition


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--followed", action="store_true")
    group.add_argument("--competition", metavar="SLUG")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    failures = 0
    with SessionLocal() as db:
        if args.competition:
            query = select(Competition).where(Competition.slug == args.competition)
        else:
            ids = syncable_competition_ids(db) if args.all else followed_competition_ids(db)
            query = select(Competition).where(Competition.id.in_(ids)).order_by(Competition.slug)
        competitions = list(db.scalars(query))
        if not competitions:
            print("Nothing to sync.")
            return 1

        for competition in competitions:
            try:
                for source, result in sync_from_all_sources(db, competition).items():
                    print(f"✓ {competition.name} ({source}): {result}")
            except (SyncError, ProviderError) as exc:
                failures += 1
                print(f"✗ {competition.name}: {exc}", file=sys.stderr)
            db.commit()  # one competition at a time: a later failure keeps earlier syncs
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
