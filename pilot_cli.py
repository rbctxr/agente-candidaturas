
"""CLI do piloto. Não envia candidaturas automaticamente."""

import argparse

from jobagent.storage import connect, set_status
from jobagent.pilot import (
    init,
    confirmed_count,
    enable_auto,
    disable_auto,
)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=[
            "status",
            "confirm-manual",
            "enable-auto",
            "disable-auto",
        ],
    )
    parser.add_argument("--id", default="")
    parser.add_argument("--confirm", default="")

    args = parser.parse_args()

    db = connect()
    init(db)

    if args.action == "confirm-manual":
        if not args.id:
            parser.error("--id obrigatório")

        try:
            set_status(db, args.id, "enviada_manualmente")
        except ValueError as error:
            parser.error(str(error))

    elif args.action == "enable-auto":
        enable_auto(db, args.confirm)

    elif args.action == "disable-auto":
        disable_auto(db)

    print(
        f"Candidaturas manuais confirmadas: "
        f"{confirmed_count(db)}/10"
    )

    mode = db.execute(
        "SELECT mode FROM pilot_settings WHERE singleton=1"
    ).fetchone()[0]

    print("Modo:", mode)


if __name__ == "__main__":
    main()
