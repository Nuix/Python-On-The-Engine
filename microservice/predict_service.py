from flask import Flask, request

import json
from io import BytesIO, BufferedReader

from PIL import Image

from img_classifier import predictor

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def hello():
    """
    Simple health check.
    :return: JSON with {success: True}
    """
    return json.dumps({'success': True})


@app.route('/predict/<image_guid>', methods=['POST'])
def predict(image_guid):
    """
    Run a prediction on the provided image.  The image GUID is provided in the URL and its content is provided in the
    body of the request.  The request should be formatted as a MultiPart Form File Upload.  This runs the classier
    and generates the response stored in the JSON keyed to the image's GUID, so the results can be assigned to the
    correct image upon receipt.
    :param image_guid: The GUID of the image / item to be classified
    :return: JSON - a list of classifications assigned to the image GUID.  The format will be:
             { 'results': { '<image_guid>': [{'<class1>': <score1>}, {'<class2>': <score2>}, ...}}
    """
    if image_guid is None:
        return {'error': 'No GUID provided to identify image.'}, 400

    image_file = request.files[image_guid]

    if image_file is None:
        return {'error': 'Image file not provided.'}, 400

    def get_image_for_pil():
        # Translate the image to PIL format and return it to the caller
        # This is the generator for the predictor operation.

        image_bytes = image_file.stream.read()
        image_mem = BytesIO()
        image_mem.write(image_bytes)

        image_pixels = Image.open(image_mem).convert('RGB')
        print(f'{image_guid} = {image_file.filename}: {image_pixels.size}')
        return [image_pixels]

    # Doing just one image at a time
    inference = predictor.predict(get_image_for_pil)[0]
    print(f'Inference Return: {inference}')

    # if an error
    if 'ERROR' == inference[0]:
        # Handle error
        return {'error': inference[1]}, 500
    else:
        # Handle success
        image_classes = []
        for results in inference:
            image_classes.append({results[0]: str(results[1])})

        results = {'results': {image_guid: image_classes}}
        print(f'{results}')
        return json.dumps(results), 200
