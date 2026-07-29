from fastapi.testclient import TestClient
from app.main import app


def test_admin_panel_routes_render_without_js_errors():
    client = TestClient(app)
    res = client.get('/')
    assert res.status_code == 200
    html = res.text
    assert 'view-admin' in html
    assert 'adminPanel-dashboard' in html
    assert 'adminPanel-schemes' in html
    assert 'adminPanel-rules' in html
    assert 'adminPanel-users' in html
    assert 'adminPanel-applications' in html
    assert 'adminPanel-documents' in html
    assert 'adminPanel-notifications' in html
    assert 'adminPanel-reports' in html
    assert 'adminPanel-profile' in html
