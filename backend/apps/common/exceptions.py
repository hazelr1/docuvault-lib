from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = detail["detail"]
    else:
        message = "Request failed"
    response.data = {
        "code": response.status_code,
        "message": str(message),
        "details": detail,
    }
    return response
