from app import *


import app

def test_reported_issue():
    assert app.factorial(0) == 1
    assert app.factorial(1) == 1
    assert app.factorial(2) == 2
    assert app.factorial(3) == 6
    assert app.factorial(4) == 24
    assert app.factorial(5) == 120
