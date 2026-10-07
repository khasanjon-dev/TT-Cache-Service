"""Allow running the client with ``python -m app.cli``."""

from app.cli.command import main

raise SystemExit(main())
