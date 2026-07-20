import sys
from pathlib import Path

from alembic import command
from alembic.config import Config


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


def main() -> None:
    alembic_config = Config(
        str(
            PROJECT_ROOT
            / "alembic.ini"
        )
    )

    alembic_config.set_main_option(
        "script_location",
        str(
            PROJECT_ROOT
            / "alembic"
        ),
    )

    command.upgrade(
        alembic_config,
        "head",
    )

    print(
        "Database migrations completed."
    )


if __name__ == "__main__":
    main()