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
    """
    Generic Request using HttpClient.  This wil create a new client, send the request, record the response, then
    close the client.
    :param http_request: The fully formed request to send.
    :return: A tuple: [0] The Status Code, [1] If the status code is <300, send the body translated to a json object (
                      dictionary).  If >= 300, then assume the body can't be turned to JSON and return the response
                      directly.
    """
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
    """
    Build a URL out of constituent parts.
    :param host: The host and port number
    :param endpoint: Either a str representing the full path to the endpoint desired, or a list of strs which will be
                     concatenated together with '/' to form the path to the desired resource
    :param query: Either a str representing a fully formed query string minus the '?', a dict which will be translated
                  to a query string, or a list, which is assumed to be in 'key=value' form and will be joined into
                  a single query string.
    :return: A single URL consisting of the host, path to the endpoint, and query string if provided.
    """
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
    """
    Perform a GET request to the given host and endpoint, providing the given query and headers to the request.
    :param host: The host to GET from
    :param endpoint: Either a str representing the full path to the endpoint desired, or a list of strs which will be
                     concatenated together with '/' to form the path to the desired resource
    :param query: Either a str representing a fully formed query string minus the '?', a dict which will be translated
                  to a query string, or a list, which is assumed to be in 'key=value' form and will be joined into
                  a single query string.
    :param headers: A dictionary of headers to send with the request NOTE: Not Implemented!!
    :return: A tuple: [0] Boolean on success, [1] The response body as returned by do_request(http_request)
    """
    request = RequestBuilder.get(build_url(host, endpoint, query)).build()

    status, body = do_request(request)

    return status < 300, body


def post(host, endpoint, query=None, body=None):
    """
    Perform a POST request to the given host and endpoint, providing the given query and body to the request.
    :param host: The host to POST to
    :param endpoint: Either a str representing the full path to the endpoint desired, or a list of strs which will be
                     concatenated together with '/' to form the path to the desired resource
    :param query: Either a str representing a fully formed query string minus the '?', a dict which will be translated
                  to a query string, or a list, which is assumed to be in 'key=value' form and will be joined into
                  a single query string.
    :param body: Something that can be coerced into an org.apache.http.entity.Entity, usually a direct subclass of
                 said type
    :return: A tuple: [0] True / False on the request success, [1] The response body as returned from
                      do_request(http_request)
    """
    request = RequestBuilder.post(build_url(host, endpoint, query)).setEntity(body).build()

    status, body = do_request(request)
    return status < 300, body


def write_metadata(item, predictions):
    """
    Add the predictions to the selected item as custom metadata named 'image_classifier_top3'.  The predictions come
    in as a list of pairs of values: the class and its score.  The class and value are combined using ":" and then the
     pairs are concatenated together using ";".

    :param item:  The item to add metadata to.
    :param predictions: The list of dicts used to represent the prediction results.
    :return: Nothing
    """
    prediction_data = ';'.join([list(pred.items())[0][0] + ':' +
                                str(round(float(list(pred.items())[0][1]) * 100, 2)) + '%'
                                for pred in predictions]
                               )
    item_custom_metadata = item.getCustomMetadata()
    item_custom_metadata['image_classifier_top3'] = prediction_data


def get_prediction(item):
    """
    Get the image classification predictions for the given item.  If the item is a JPEG (has a .jpg or .jpeg extension)
    it's binary will be retrieved and uploaded to the microservice to be classified.
    :param item: The item to be classified
    :return: A tuple: [0] True/False on the success of the classification, [1] The classifications or error if
                      classification failed.
    """
    if item.getCorrectedExtension().lower() == 'jpeg' or \
            item.getCorrectedExtension().lower() == 'jpg':
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
    """
    Classifies all the items on the list.  Sequentially get the classification for and update the metadata for each
    item in the list.
    :param item_list: List of items to classify.  Should be a non-empty list with JPEG files in it.
    :return:  Nothing
    """
    for item in item_list:
        print('Predicting ' + item.getLocalisedName())
        success, prediction = get_prediction(item)
        if success:
            image_predictions = prediction['results'][item.getGuid()]
            write_metadata(item, image_predictions)


if __name__ == '__builtin__':
    # Make sure the microservice is reachable
    ok, content = get(HOST, 'health')
    print('Success: ' + str(ok))

    if ok:
        print('Connected: ' + str(content['success']))
        # Predict all the selected items.
        predict_all(current_selected_items)
    else:
        print('Error, service health check failed: ' + str(content))
