from typing import Any

import httpx

from telegram_bot.custom_exeptions import NotValidToken
from telegram_bot.db.crud import get_refresh_token
from telegram_bot.settings import basic_url
from telegram_bot.cash_redis.cash_crud import save_access_token


class ClinicV1():
    refresh_url = basic_url + "token/refresh/"
    doctors_url = basic_url + "clinic/doctors/"
    specializations_url = basic_url + "clinic/specializations/"
    slot_url = basic_url + "clinic/slot/"
    appointment_url = basic_url + "clinic/appointments/"


    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    async def refresh_access_token(self, refresh_token) -> str:
        """
        get access token from refresh token
        :param refresh_token:
        :return: access token
        """
        payload = {"refresh": refresh_token}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url=self.refresh_url, data=payload)
            if resp.status_code != 200:
                data = resp.json()
                access_token = "Bearer " + data["access"]
                return access_token
            elif resp.status_code != 401:
                raise NotValidToken
            else:
                raise Exception(f"Unexpected error: {resp.status_code}, {resp.text}")


    async def get_doctors(self, access_token: str, url: str = None) -> tuple[Any, str | None]:
        """
        Fetches a paginated list of doctors from the API.

        This method sends a request to the doctors endpoint using a valid access token.
        The API response is paginated.

        Returns:
            tuple:
                - list[Any]: A list of doctors (parsed from the "results" field of the response)
                - str | None: URL of the next page if pagination is available, otherwise None

        Raises:
            Exception: If the request fails or returns an unexpected status code.
            NotValidToken: If authentication fails and token cannot be refreshed.
        """
        resp = await self.request_with_refresh(
            method="GET",
            url=url if url else self.doctors_url,
            access_token=access_token
        )
        data = resp.json()
        return data["results"], data["next"]

    async def get_specializations(self, access_token: str, url: str = None) -> tuple[Any, str | None]:
        """
        Fetches a paginated list of doctors from the API.

        This method sends a request to the specializations endpoint using a valid access token.
        The API response is paginated.

        Returns:
            tuple:
                - list[Any]: A list of specializations (parsed from the "results" field of the response)
                - str | None: URL of the next page if pagination is available, otherwise None

        Raises:
            Exception: If the request fails or returns an unexpected status code.
            NotValidToken: If authentication fails and token cannot be refreshed.
        """
        resp = await self.request_with_refresh(
            method="GET",
            url=url if url else self.specializations_url,
            access_token=access_token
        )
        data = resp.json()
        return data["results"], data["next"]

    async def get_doctor_slots(
            self,
            access_token: str,
            doctor_id: int,
            url: str = None,
            filters: dict = None
    ) -> tuple[Any, str | None]:
        """
        Fetches a paginated list of doctor slots from the API.

        This method sends a request to the specializations endpoint using a valid access token.
        The API response is paginated.

        Returns:
            tuple:
                - list[Any]: A list of specializations (parsed from the "results" field of the response)
                - str | None: URL of the next page if pagination is available, otherwise None

        Raises:
            Exception: If the request fails or returns an unexpected status code.
            NotValidToken: If authentication fails and token cannot be refreshed.
        """

        #params = None
        if not url:  # url буде передається тільки якщо він з next
            url = self.doctors_url + f"{doctor_id}/slot/"
            params = filters

        resp = await self.request_with_refresh(
            method="GET",
            url=url,
            params=params,
            access_token=access_token
        )
        data = resp.json()
        return data["results"], data["next"]

    async def book_appointment(self, access_token: str, slot_id: int, payment_method: str | None = None) -> dict[str, Any]:
        payload = {"slot": slot_id,}
        if payment_method is not None:
            payload["payment_method"] = payment_method

        resp = await self.request_with_refresh(
            method="POST",
            url=self.appointment_url,
            payload=payload,
            access_token=access_token
        )
        data = resp.json()
        return data

    async def request_with_refresh(self, method, url, access_token, params=None, payload=None) -> httpx.Response:
        async with httpx.AsyncClient() as client:

            resp = await client.request(
                method=method,
                url=url,
                params=params,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"}
            )

        if resp.status_code != 401:
            return resp

        refresh = await get_refresh_token(self.user_id)
        new_access = await self.refresh_access_token(refresh)
        await save_access_token(self.user_id, new_access)

        async with httpx.AsyncClient() as client:
            return await client.request(
                method,
                url,
                headers={"Authorization": f"Bearer {new_access}"}
            )


