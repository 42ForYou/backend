from rest_framework.views import exception_handler
from rest_framework.response import Response


class CustomError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status
        super().__init__(self.message)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, CustomError):
        return Response({"error": exc.message}, status=exc.status)

    if response is not None:
        response.data["error"] = str(exc)
    return response


def wrap_data(**kwargs):
    return {"data": kwargs}
