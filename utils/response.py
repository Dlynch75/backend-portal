
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList
from language.language_utils import get_message


def create_message(data, status_code=None, error_message=None):
    """Create message utility for creating responses

    Args:
        error_message:
        data ([list]): [List of objects]
        status_code ([int], mandatory): [Internal system status code for the
                                    response defined in module locale]
                                    Defaults to None.

    Returns:
        [dict]: [Dict with status, message and data keys for client]
    """
    if error_message:
        if "Invalid" in error_message:
            message = get_message(status_code)
        else:
            message = error_message
    else:
        message = get_message(status_code)

    return {
        # internal system codes
        "status": status_code,

        # locale message in the system codes
        # "message": data[0] if data else get_message(status_code),
        "message": message,
        "data": data,
    }


def create_response_json(
        response_body, http_status=None, header_dict=None, mime="application/json"
):
    """Create response utility for creating a generic response

    IMPORTANT : EXPECTS response_body param to be created and passed by
                create_message method.

    Args:
        response_body ([list]): [List of objects]
        http_status (int, optional): [The response HTTP Status code].
        header_dict (dict, optional): [Header data]. Defaults to {}.
        mime (str, optional): [Data type]. Defaults to 'application/json'.

    Returns:
        [HTTPResponse]: [The HTTP response]
    """

    if header_dict is None:
        header_dict = {}
    if http_status is None:
        raise ValueError("No http status code provided")

    resp = JsonResponse(
        data=response_body, status=http_status
    )

    for name, value in header_dict.items():
        resp[name] = value

    return resp


def create_response(
        response_body, http_status=None, header_dict=None, mime="application/json"
):
    """Create response utility for creating a generic response

    IMPORTANT : EXPECTS response_body param to be created and passed by
                create_message method.

    Args:
        response_body ([list]): [List of objects]
        http_status (int, optional): [The response HTTP Status code].
        header_dict (dict, optional): [Header data]. Defaults to {}.
        mime (str, optional): [Data type]. Defaults to 'application/json'.

    Returns:
        [HTTPResponse]: [The HTTP response]
    """

    if header_dict is None:
        header_dict = {}
    if http_status is None:
        raise ValueError("No http status code provided")

    resp = Response(
        data=response_body, status=http_status
    )

    for name, value in header_dict.items():
        resp[name] = value

    return resp


def error_message(errors, default=1):
    if not errors:
        return get_message(default)
    try:
        serialized_error_dict = errors
        # ReturnList of serialized_errors when many=True on serializer
        if isinstance(errors, ReturnList):
            serialized_error_dict = errors[0]

        serialized_errors_keys = list(serialized_error_dict.keys())
        # getting first error message from serializer errors
        try:
            message = serialized_error_dict[serialized_errors_keys[0]][0].replace("This", serialized_errors_keys[0])
            return message.replace("_", " ").capitalize()
        except:
            return serialized_error_dict[serialized_errors_keys[0]][0].replace("_", " ").capitalize()

    except Exception as e:
        print(f"Error parsing serializer errors:{e}")
        return get_message(default)
