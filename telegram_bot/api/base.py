from abc import ABC, abstractmethod



class ApiService(ABC):

    @staticmethod
    @abstractmethod
    async def refresh_token(refresh_token: str) -> str:
        pass
