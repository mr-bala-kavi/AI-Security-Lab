"""Smoke tests: the app builds and every top-level page renders."""
import pytest


def test_app_factory(app):
    assert app is not None
    assert app.config['TESTING'] is True


@pytest.mark.parametrize('path', [
    '/',
    '/about',
    '/reference',
    '/solutions',
    '/achievements',
    '/analytics',
])
def test_static_pages_render(client, path):
    resp = client.get(path)
    assert resp.status_code == 200


@pytest.mark.parametrize('module_path', [
    '/modules/prompt-injection',
    '/modules/output-handling',
    '/modules/data-poisoning',
    '/modules/model-inversion',
    '/modules/adversarial-examples',
    '/modules/dos-attacks',
    '/modules/insecure-plugins',
    '/modules/data-disclosure',
    '/modules/vector-weaknesses',
    '/modules/misinformation',
])
def test_module_pages_render(client, module_path):
    resp = client.get(module_path)
    assert resp.status_code == 200


def test_solution_detail_valid(client):
    resp = client.get('/solutions/prompt_injection')
    assert resp.status_code == 200


def test_solution_detail_unknown_404(client):
    resp = client.get('/solutions/not_a_real_module')
    assert resp.status_code == 404


def test_unknown_page_404(client):
    resp = client.get('/this-does-not-exist')
    assert resp.status_code == 404
