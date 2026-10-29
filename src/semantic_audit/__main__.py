"""Allow ``python -m semantic_audit`` in addition to the installed CLI."""

from semantic_audit.cli import main

raise SystemExit(main())
