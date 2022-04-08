import requests


def put(url, headers, data):
    """
    Executes a PUT request to the provided url with the provided headers and data.

    :param url:
    :param headers:
    :param data:
    :return: A tuple.  [0] is the response status code, and [1] is the response body in json form.
    """
    print("PUT: " + url)
    response = requests.put(url, headers=headers, data=data)
    print(response.status_code)
    try:
        response_body = response.json()
    except:
        response_body = response
    return response.status_code, response_body


def post(url, headers, data):
    """
    Executes a POST request to the provided url with the provided headers and data.

    :param url:
    :param headers:
    :param data:
    :return: A tuple.  [0] is the response status code, and [1] is the response body in json form.
    """
    print("POST: " + url)
    response = requests.post(url, headers=headers, data=data)
    print(response.status_code)
    try:
        response_body = response.json()
    except:
        response_body = response
    return response.status_code, response_body


def get(url, headers):
    """
    Executes a GET request to the provided url with the provided headers and data.

    :param url:
    :param headers:
    :return: A tuple.  [0] is the response status code, and [1] is the response body in json form.
    """
    print("GET: " + url)
    response = requests.get(url, headers=headers)
    print(response.status_code)
    try:
        response_body = response.json()
    except:
        response_body = response
    return response.status_code, response_body


def patch(url, headers, data):
    """
    Execute a PATCH request to the provided url with the provided headers and data

    :param url:
    :param headers:
    :param data:
    :return: A tuple. [0] The response status code.  [1] The response body in json form.
    """
    print(f"PATCH: {url}")
    response = requests.patch(url, headers=headers, data=data)
    print(response.status_code)
    try:
        response_body = response.json()
    except:
        response_body = response
    return response.status_code, response_body


def head(url, headers, data):
    """
    Executes a HEAD request to the provided url with the provided headers and data

    :param url:
    :param headers:
    :param data:
    :return: A tuple. [0] The response status code.  [1] The response body in json form.
    """
    print(f"HEAD: {url}")
    response = requests.head(url, headers=headers, data=data)
    print(response.status_code)
    try:
        response_body = response.json()
    except:
        response_body = response
    return response.status_code, response_body


def delete(url, headers, data):
    """
    Executes a DELETE request to the provided url with the provided headers and data

    :param url:
    :param headers:
    :param data:
    :return: A tuple. [0] The response status code.  [1] The response body in json form.
    """
    print(f"DELETE: {url}")
    response = requests.delete(url, headers=headers, data=data)
    print(response.status_code)
    try:
        response_body = response.json()
    except:
        response_body = response
    return response.status_code, response_body
