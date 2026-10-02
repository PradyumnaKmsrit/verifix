from app import median

def test_odd():
    assert median([3, 1, 2]) == 2

def test_even():
    assert median([4, 1, 3, 2]) == 2.5

def test_single():
    assert median([7]) == 7
