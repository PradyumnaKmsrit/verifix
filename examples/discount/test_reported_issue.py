from pricing import *


import pricing

def test_reported_issue():
    assert pricing.apply_discount(200, 10) == 180
