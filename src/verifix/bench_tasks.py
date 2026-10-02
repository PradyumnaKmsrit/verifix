"""Fixed benchmark tasks: a buggy function, a hidden test, and a task description."""

TASKS = [
    {
        "id": "add",
        "code": "def add(a, b):\n    return a - b\n",
        "test": (
            "from app import add\n\n"
            "def test_add():\n    assert add(2, 3) == 5\n"
        ),
        "task": "Fix the add function so the tests pass",
    },
    {
        "id": "median",
        "code": (
            "def median(values):\n"
            "    ordered = sorted(values)\n"
            "    return ordered[len(ordered) // 2]\n"
        ),
        "test": (
            "from app import median\n\n"
            "def test_odd():\n    assert median([3, 1, 2]) == 2\n\n"
            "def test_even():\n    assert median([4, 1, 3, 2]) == 2.5\n\n"
            "def test_single():\n    assert median([7]) == 7\n"
        ),
        "task": "Fix the median function so the tests pass",
    },
    {
        "id": "discount",
        "code": "def apply_discount(price, percent):\n    return price - percent\n",
        "test": (
            "from app import apply_discount\n\n"
            "def test_discount():\n    assert apply_discount(200, 10) == 180\n"
        ),
        "task": (
            "apply_discount should reduce price by percent/100 of price, "
            "e.g. apply_discount(200, 10) should return 180, not 190"
        ),
    },
    {
        "id": "bank_withdraw",
        "code": (
            "class Account:\n"
            "    def __init__(self, balance=0):\n"
            "        self.balance = balance\n\n"
            "    def withdraw(self, amount):\n"
            "        self.balance = self.balance - amount\n"
            "        return self.balance\n"
        ),
        "test": (
            "from app import Account\n\n"
            "def test_withdraw_insufficient_funds():\n"
            "    acc = Account(50)\n"
            "    try:\n"
            "        acc.withdraw(100)\n"
            "        assert False, 'expected ValueError'\n"
            "    except ValueError:\n"
            "        pass\n"
            "    assert acc.balance == 50\n"
        ),
        "task": (
            "Fix withdraw so it raises ValueError on insufficient funds "
            "and leaves the balance unchanged"
        ),
    },
    {
        "id": "is_palindrome",
        "code": (
            "def is_palindrome(text):\n"
            "    return text == text[::-1]\n"
        ),
        "test": (
            "from app import is_palindrome\n\n"
            "def test_case_and_spaces():\n"
            "    assert is_palindrome('A man a plan a canal Panama') is True\n\n"
            "def test_not_palindrome():\n"
            "    assert is_palindrome('hello') is False\n"
        ),
        "task": (
            "is_palindrome should ignore case and spaces when checking, "
            "e.g. 'A man a plan a canal Panama' should be a palindrome"
        ),
    },
    {
        "id": "factorial",
        "code": (
            "def factorial(n):\n"
            "    result = 0\n"
            "    for i in range(1, n + 1):\n"
            "        result *= i\n"
            "    return result\n"
        ),
        "test": (
            "from app import factorial\n\n"
            "def test_factorial():\n"
            "    assert factorial(5) == 120\n"
            "    assert factorial(0) == 1\n"
        ),
        "task": "Fix factorial so it returns the correct value for all inputs",
    },
]