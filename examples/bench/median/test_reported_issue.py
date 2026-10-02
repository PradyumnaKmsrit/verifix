from app import *


import app

def test_reported_issue():
    assert app.median([1, 2, 3, 4, 5]) == 3
    assert app.median([10, 20, 30, 40, 50, 60]) == 35
    assert app.median([1, 2, 3, 4, 5, 6]) == 3.5
    assert app.median([1, 2, 3, 4, 5, 6, 7]) == 4
