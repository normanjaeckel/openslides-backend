from typing import Any

import requests
from authlib import COOKIE_NAME, HEADER_NAME
from werkzeug.test import Client as WerkzeugClient
from werkzeug.wrappers import BaseResponse

from openslides_backend.shared.exceptions import AuthenticationException
from openslides_backend.shared.interfaces.wsgi import WSGIApplication
from openslides_backend.shared.patterns import (
    KEYSEPARATOR,
    Collection,
    FullQualifiedField,
    FullQualifiedId,
)


class Client(WerkzeugClient):
    def __init__(
        self, application: WSGIApplication, username: str = None, password: str = None
    ):
        super().__init__(application, BaseResponse)

        # login admin
        if username and password is not None:
            auth_endpoint = (
                application.services.authentication().auth_handler.http_handler.get_endpoint()
            )
            url = f"{auth_endpoint}/system/auth/login"
            try:
                response = requests.post(
                    url, json={"username": username, "password": password}
                )
            except requests.exceptions.ConnectionError as e:
                raise AuthenticationException(
                    f"Cannot reach the authentication service on {url}. Error: {e}"
                )
            assert response.status_code == 200
            # save access token and refresh id for subsequent requests
            self.set_cookie("localhost", COOKIE_NAME, response.cookies.get(COOKIE_NAME))
            self.headers = {HEADER_NAME: response.headers[HEADER_NAME]}
        else:
            self.headers = {}

    def post(self, *args: Any, **kwargs: Any) -> Any:
        return super().post(*args, headers=self.headers, **kwargs)


def get_fqid(value: str) -> FullQualifiedId:
    """
    Returns a FullQualifiedId parsed from the given value.
    """
    collection, id = value.split(KEYSEPARATOR)
    return FullQualifiedId(Collection(collection), int(id))


def get_fqfield(value: str) -> FullQualifiedField:
    """
    Returns a FullQualifiedField parsed from the given value.
    """
    collection, id, field = value.split(KEYSEPARATOR)
    return FullQualifiedField(Collection(collection), int(id), field)


def get_id_from_fqid(fqid: str) -> int:
    id = fqid.split(KEYSEPARATOR)[1]
    return int(id)


def get_collection_from_fqid(fqid: str) -> Collection:
    return Collection(fqid.split(KEYSEPARATOR)[0])
