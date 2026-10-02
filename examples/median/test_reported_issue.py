from median import *


import median

def test_reported_issue():
    assert median([1, 2, 3, 4, 5]) == 3
    assert median([1, 2, 3, 4, 5, 6]) == 3.5
    assert median([1, 2, 3, 4, 5, 6, 7]) == 4
