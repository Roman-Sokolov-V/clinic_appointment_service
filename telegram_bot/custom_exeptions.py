
class NotValidToken(Exception):
    def __init__(self, message="Token expired or invalid"):
        super().__init__(message)

class AnyTokensFound(Exception):
    pass

class TokenNotExists(Exception):
    def __init__(self, message="Access token does not exist in cash"):
        super().__init__(message)