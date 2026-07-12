from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_smc() -> Path:
    """Archivo SMC real del BCV (2020-TI, 3 jornadas, incluye la anomalía CHF 31/03/2020)."""
    return FIXTURES / "2_1_2a20_smc.xls"
