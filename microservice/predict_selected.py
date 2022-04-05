import json


def get(host, endpoint, query=None):
    from org.apache.http.impl.client import HttpClients
    from org.apache.http.client.methods import HttpGet
    from org.apache.http.util import EntityUtils
    from java.nio.charset import Charset

    utf8 = Charset.forName('UTF-8')
    http_client = HttpClients.createDefault()
    status_code = None
    response_body = None

    try:
        url = host + '/' + endpoint + (('?' + query) if query is not None else '')
        get_command = HttpGet(url)
        response = http_client.execute(get_command)

        status_code = response.getStatusLine().getStatusCode()
        response_body = EntityUtils.toString(response.getEntity(), utf8)
        return status_code, response_body
    finally:
        http_client.close()


if __name__ == '__builtin__':
    status, body = get('http://127.0.0.1:8982', '')
    json_body = json.loads(body)
    print('Status: ' + str(status))
    print('Greet: ' + json_body['greet'])