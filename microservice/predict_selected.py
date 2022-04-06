import json

from java.nio.charset import Charset

from org.apache.http.impl.client import HttpClients
from org.apache.http.client.methods import RequestBuilder
from org.apache.http.util import EntityUtils
from org.apache.http.entity import ContentType
from org.apache.http.entity.mime import MultipartEntityBuilder, HttpMultipartMode

utf8 = Charset.forName('UTF-8')

HOST = 'http://127.0.0.1:8982'


def do_request(http_request):
    http_client = HttpClients.createDefault()

    try:
        response = http_client.execute(http_request)

        status_code = response.getStatusLine().getStatusCode()
        response_body = EntityUtils.toString(response.getEntity(), utf8)

        if status_code < 300 and response_body is not None:
            return status_code, json.loads(response_body)
        else:
            return status_code, response_body
    finally:
        http_client.close()


def build_url(host, endpoint, query=None):
    url_list = [host]
    if isinstance(endpoint, str):
        url_list.append(endpoint)
    elif isinstance(endpoint, list):
        url_list.extend(endpoint)
    elif endpoint is None:
        pass  # do nothing
    else:
        url_list.append(str(endpoint))
    url = '/'.join(url_list)

    query_list = []
    if query is None:
        pass  # do nothing
    elif isinstance(query, str):
        query_list.append(query)  # assume query string already built
    elif isinstance(query, dict):
        for param in query:  # turn map key:values to key=value
            query_list.append(param[0] + '=' + param[1])
    elif isinstance(query, list):
        query_list.extend(query)  # assume list of key=value strings
    else:
        # do nothing, can't work on it
        pass
    query_string = '&'.join(query_list)

    return url + ('?' + query_string if len(query_string) > 0 else '')


def get(host, endpoint, query=None, headers=None):
    request = RequestBuilder.get(build_url(host, endpoint, query)).build()

    status, body = do_request(request)

    return status < 300, body


def post(host, endpoint, query=None, body=None):
    request = RequestBuilder.post(build_url(host, endpoint, query)).setEntity(body).build()

    status, body = do_request(request)
    return status < 300, body


def write_metadata(item, predictions):
    prediction_data = ';'.join([list(pred.items())[0][0] + ':' +
                                str(round(float(list(pred.items())[0][1]) * 100, 2)) + '%'
                                for pred in predictions]
                               )
    item_custom_metadata = item.getCustomMetadata()
    item_custom_metadata['image_classifier_top3'] = prediction_data


def get_prediction(item):
    if item.getCorrectedExtension() == 'jpeg' or \
            item.getCorrectedExtension() == 'JPEG' or \
            item.getCorrectedExtension() == 'jpg' or \
            item.getCorrectedExtension() == 'JPG':
        item_guid = item.getGuid()
        item_filename = item.getLocalisedName()

        image_data = item.getBinary().getBinaryData().getInputStream().readAllBytes()

        request_body = MultipartEntityBuilder.create() \
            .setMode(HttpMultipartMode.BROWSER_COMPATIBLE) \
            .addBinaryBody(item_guid, image_data, ContentType.DEFAULT_BINARY, item_filename) \
            .build()
        success, response = post(HOST, ['predict', item_guid], body=request_body)
        print(item_filename + ' [' + str(ok) + ']: ' + str(response))

        return success, response
    else:
        return False, 'Not a JPG'


def predict_all(item_list):
    for item in item_list:
        print('Predicting ' + item.getLocalisedName())
        success, prediction = get_prediction(item)
        if success:
            image_predictions = prediction['results'][item.getGuid()]
            write_metadata(item, image_predictions)


if __name__ == '__builtin__':
    ok, content = get(HOST, 'health')
    print('Success: ' + str(ok))

    if ok:
        print('Connected: ' + str(content['success']))
        predict_all(current_selected_items)
    else:
        print('Error, service health check failed: ' + str(content))
