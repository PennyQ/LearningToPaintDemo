import os

import pytest

from app import server


@pytest.fixture
def client():
    server.app.config['TESTING'] = True

    with server.app.test_client() as client:
        yield client

def test_root(client):
    """Start with root."""

    rv = client.get('/')
    assert b'Learning to Paint Demo 2020' in rv.data
    

def test_tab(client):
    """Start with root."""

    rv = client.get('/test_tab')
    assert b'Test page for camera toggle' in rv.data