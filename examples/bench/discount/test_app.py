from app import apply_discount

def test_discount():
    assert apply_discount(200, 10) == 180
