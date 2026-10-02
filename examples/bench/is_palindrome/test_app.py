from app import is_palindrome

def test_case_and_spaces():
    assert is_palindrome('A man a plan a canal Panama') is True

def test_not_palindrome():
    assert is_palindrome('hello') is False
