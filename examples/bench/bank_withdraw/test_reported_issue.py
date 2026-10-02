from app import *


import app

def test_reported_issue():
    account = app.Account()
    with pytest.raises(ValueError):
        account.withdraw(100)
    assert account.balance == 0
