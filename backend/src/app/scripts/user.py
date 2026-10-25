"""Manage the MVP user and subscriptions from the command line (no sign-up/login yet).

Examples:
  uv run python -m app.scripts.user create --email me@example.com --timezone America/Santiago
  uv run python -m app.scripts.user follow --email me@example.com --competitor Barcelona --competition champions-league
  uv run python -m app.scripts.user follow --email me@example.com --sport formula-1 --kinds qualifying,sprint,race
  uv run python -m app.scripts.user list --email me@example.com
  uv run python -m app.scripts.user unfollow --email me@example.com --id 3
  uv run python -m app.scripts.user rotate-token --email me@example.com
"""

import argparse
import sys

from app.core.database import SessionLocal
from app.models import Subscription
from app.services import subscriptions as svc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="create a user and print their iCal URL")
    create.add_argument("--email", required=True)
    create.add_argument("--timezone", default="UTC")

    follow = commands.add_parser("follow", help="add a subscription (all given filters must match)")
    follow.add_argument("--email", required=True)
    follow.add_argument("--sport", help="sport slug, e.g. football, formula-1")
    follow.add_argument("--competition", help="competition slug, e.g. champions-league")
    follow.add_argument("--competitor", help="team or athlete name, e.g. Barcelona")
    follow.add_argument("--kinds", help="comma-separated event kinds, e.g. qualifying,race")

    for name, help_text in (("list", "list subscriptions and the iCal URL"), ("rotate-token", "new iCal URL")):
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("--email", required=True)

    unfollow = commands.add_parser("unfollow", help="delete a subscription")
    unfollow.add_argument("--email", required=True)
    unfollow.add_argument("--id", type=int, required=True)

    args = parser.parse_args(argv)
    with SessionLocal() as db:
        try:
            if args.command == "create":
                user = svc.create_user(db, args.email, args.timezone)
                print(f"Created {user.email}.\niCal URL: {svc.ical_url(user)}")
            else:
                user = svc.get_user(db, args.email)
                if args.command == "follow":
                    kinds = [k.strip() for k in args.kinds.split(",")] if args.kinds else None
                    subscription = svc.follow(
                        db,
                        user,
                        sport=args.sport,
                        competition=args.competition,
                        competitor=args.competitor,
                        kinds=kinds,
                    )
                    print(f"Following {svc.describe(db, subscription)}")
                elif args.command == "list":
                    for subscription in user.subscriptions:
                        print(svc.describe(db, subscription))
                    print(f"iCal URL: {svc.ical_url(user)}")
                elif args.command == "unfollow":
                    subscription = db.get(Subscription, args.id)
                    if subscription is None or subscription.user_id != user.id:
                        raise svc.NotFoundError(f"{user.email} has no subscription #{args.id}")
                    db.delete(subscription)
                    print(f"Deleted subscription #{args.id}")
                elif args.command == "rotate-token":
                    print(f"New iCal URL (the old one stops working): {svc.rotate_ical_token(db, user)}")
            db.commit()
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
