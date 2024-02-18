from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail, EmailMessage
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import BaseAuthentication
from rest_framework.pagination import PageNumberPagination


class CustomError(Exception):
    def __init__(self, exception, model_name=None, status_code=None):

        if isinstance(exception, dict):
            self.message = exception
            self.status = status_code if status_code else status.HTTP_400_BAD_REQUEST

        elif isinstance(exception, CustomError):
            self.message = exception.message
            self.status = exception.status

        elif isinstance(exception, ObjectDoesNotExist):
            self.message = {
                "error": (
                    f"{model_name} does not exist"
                    if model_name
                    else "Object does not exist"
                )
            }
            self.status = status.HTTP_404_NOT_FOUND
        else:
            self.message = {"error": str(exception)}
            self.status = (
                status_code if status_code else status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def __str__(self):
        return str(self.message)


def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler

    response = exception_handler(exc, context)

    if isinstance(exc, CustomError):
        return Response(exc.message, status=exc.status)

    if response is not None:
        response.data = {"error": response.data}

    return response


def wrap_data(**kwargs):
    return {"data": kwargs}


class CookieTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token_key = request.COOKIES.get("kimyeonhkimbabo_token")
        if not token_key:
            raise CustomError(
                "Token not provided", status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            token = Token.objects.get(key=token_key)
        except Token.DoesNotExist:
            raise CustomError("Invalid token", status_code=status.HTTP_401_UNAUTHORIZED)

        return (token.user, token)


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            {
                "data": data,
                "pages": {
                    "total_pages": self.page.paginator.num_pages,
                    "count": self.page.paginator.count,
                    "current_page": self.page.number,
                    "previous_page": self.get_previous_link(),
                    "next_page": self.get_next_link(),
                },
            },
            status=status.HTTP_200_OK,
        )


def send_email(subject, message, from_email, recipient_list):
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=f"Planet Pong Support <{from_email}>",
        to=recipient_list,
    )
    email.send()
