import pytest


def test_index(client):
    """Does the portfolio's main page render properly?"""
    response = client.get('/')
    assert b'Hire me' in response.data
