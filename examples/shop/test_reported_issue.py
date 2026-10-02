from cart import *


import cart

def test_reported_issue():
    items = [100, 200, 300]
    expected_total = "$600.00"
    assert cart.total_in_cart(items) == expected_total, f"Expected {expected_total}, but got {cart.total_in_cart(items)}"
