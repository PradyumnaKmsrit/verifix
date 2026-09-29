from account import Account
def test_withdraw_insufficient_funds():
    acc = Account(50)
    try:
        acc.withdraw(100)
        assert False, "expected ValueError"
    except ValueError:
        pass
    assert acc.balance == 50
