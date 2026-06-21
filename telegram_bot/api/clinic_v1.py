import logging
from typing import Any

import httpx

from telegram_bot.custom_exeptions import BadRequest
from telegram_bot.custom_exeptions import NotValidToken, RegistrationFailed, NoTokenFound
from telegram_bot.db.crud import get_refresh_token
from telegram_bot.settings import basic_url
from telegram_bot.cash_redis.cash_crud import save_access_token


class ClinicV1():
    refresh_url = basic_url + "users/token/refresh/"
    doctors_url = basic_url + "clinic/doctors/"
    doctors_by_specialization_id_url = basic_url + "doctors/?specialization="
    specializations_url = basic_url + "clinic/specializations/"
    slot_url = basic_url + "clinic/slot/"
    appointment_url = basic_url + "clinic/appointments/"
    registration_url = basic_url + "users/"
    get_tokens_url = basic_url + "users/token/"


    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

#User####################################################################
    async def refresh_access_token(self, refresh_token) -> str:
        """
        get access token from refresh token
        :param refresh_token:
        :return: access token
        """
        logging.info("Trying to refresh access token")
        payload = {"refresh": refresh_token}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url=self.refresh_url, json=payload, timeout=10)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    access_token = data["access"]
                    return access_token
                elif resp.status_code != 401:
                    raise NotValidToken(f"status code: {resp.status_code}, error message: {resp.text}")
                else:
                    raise Exception(f"Unexpected error: {resp.status_code}, {resp.text}")
        except httpx.RequestError as e:
            raise BadRequest(f"Помилка зв'язку з сервером: {e}")



    async def register_user(self, email: str, password: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=self.registration_url,
                    json={"email": email, "password": password},
                    timeout=10.0
                )
                if response.status_code == 201:
                    user_data = response.json()
                    return user_data
                else:
                    raise RegistrationFailed(f"status code: {response.status_code}, error message: {response.text}")

        except httpx.RequestError as e:
            raise BadRequest(f"Помилка зв'язку з сервером: {e}")


    async def get_tokens(self, email: str, password: str) -> tuple[Any, Any] | None:
        logging.info("Trying to get tokens")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=self.get_tokens_url,
                    json={"email": email, "password": password},
                    timeout=10.0
                )
                if response.status_code in (200, 201):
                    return response.json()["access"], response.json()["refresh"]
                else:
                    raise NoTokenFound(f"status code: {response.status_code}, error message: {response.text}")

        except httpx.RequestError as e:
            BadRequest(f"Помилка зв'язку з сервером: {e}")


    async def get_doctors(
            self,
            access_token: str,
            url: str = None,
            specialization_id: int | None = None
    ) -> tuple[Any, str | None]:
        """
        Fetches a filtered by specialization_id paginated list of doctors from the API.

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

        if url is None and specialization_id is not None:
            url = self.doctors_url + f"?specialization={specialization_id}"

        resp = await self.request_with_refresh(
            method="GET",
            url=url if url else self.doctors_url,
            access_token=access_token
        )
        data = resp.json()
        return data["results"], data["next"]

    async def get_doctor_details(self, access_token: str, doctor_id: int) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url=f"{self.doctors_url}{doctor_id}/",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if response.status_code == 200:
                    logging.info(response.json())
                    return response.json()
                elif response.status_code == 401:
                    raise NotValidToken(f"status code: {response.status_code}, error message: {response.text}")
                else:
                    BadRequest(f"status code: {response.status_code}, error message: {response.text}")

        except httpx.RequestError as e:
            raise BadRequest(e)


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
        try:
            logging.info(access_token)
            resp = await self.request_with_refresh(
                method="GET",
                url=url if url else self.specializations_url,
                access_token=access_token
            )
            logging.info(resp)
            data = resp.json()
            logging.info(data)
            return data["results"], data["next"]
        except httpx.RequestError as e:
            logging.error(e)
            #raise BadRequest(e)
        except Exception as e:
            logging.error(e)
            #raise Exception(e)

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

        # refresh = await get_refresh_token(pool, user_id)
        # new_access = await self.refresh_access_token(refresh)
        # await save_access_token(self.user_id, new_access)

        # async with httpx.AsyncClient() as client:
        #     return await client.request(
        #         method,
        #         url,
        #         headers={"Authorization": f"Bearer {access_token}"}
        #     )


