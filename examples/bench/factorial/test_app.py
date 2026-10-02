from app import factorial

def test_factorial():
    assert factorial(5) == 120
    assert factorial(0) == 1
