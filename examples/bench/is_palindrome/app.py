def is_palindrome(text):
    # Normalize the text by removing spaces and converting to lowercase
    normalized_text = text.replace(" ", "").lower()
    return normalized_text == normalized_text[::-1]
