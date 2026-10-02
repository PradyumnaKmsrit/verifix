from app import *


import app

def test_reported_issue():
    assert app.apply_discount(200, 10) == 180
