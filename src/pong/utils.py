from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist


class CustomError(Exception):
    def __init__(self, exception, model_name=None, status=None):
        if isinstance(exception, ObjectDoesNotExist):
            self.message = (
                f"{model_name} does not exist"
                if model_name
                else "Object does not exist"
            )
            self.status = status.HTTP_404_NOT_FOUND
        else:
            self.message = str(exception)
            self.status = status if status else status.HTTP_500_INTERNAL_SERVER_ERROR

    def __str__(self):
        return self.message


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, CustomError):
        return Response({"error": exc.message}, status=exc.status)

    if response is not None:
        response.data["error"] = str(exc)
    return response


def wrap_data(**kwargs):
    return Response({"data": kwargs})
