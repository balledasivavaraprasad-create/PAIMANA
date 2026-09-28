import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import Response
from app.db.mongodb import connect_to_mongo

@pytest.fixture(autouse=True, scope="session")
def mock_external_network_services():
    """
    Globally mocks external network calls during unit test runs:
    1. SMTP email delivery: prevents connecting to smtp.gmail.com.
    """
    with patch("app.services.email_service._send_smtp_sync", return_value=True):
        yield
