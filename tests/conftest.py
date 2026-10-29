from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def example_path() -> Path:
    return Path(__file__).resolve().parents[1] / "examples" / "organization.ttl"
