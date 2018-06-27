import pytest
import ethan_portfolio


@pytest.fixture
def app():
    """Create a new app for each test."""
    app = ethan_portfolio.create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'TestingKey'
    return app


@pytest.fixture
def client(app):
    """Test client for the created app."""
    return app.test_client()


@pytest.fixture
def normal_equipment():
    """Create a list of normal equipment items."""
    return {
        "Normal0": "Hitchhiker's Guide to the Galaxy",
        "Normal1": "Towel",
        "Normal2": "Extra Head",
        "Normal3": "Chain Armor",
        "Normal4": "Plate Armor"}


@pytest.fixture
def oversized_equipment():
    """Create a list of oversized equipment items."""
    return {
        "Over0": "Marvin",
        "Over1": "Infinite Improbability Drive",
        "Over2": "Krikkit bat"}
