from abc import ABC, abstractmethod



class ApiService(ABC):

    @abstractmethod
    async def refresh_access_token(self, *args, **kwargs) -> str:
        pass

    @abstractmethod
    async def get_doctor_slots(self, *args, **kwargs) -> tuple:
        pass