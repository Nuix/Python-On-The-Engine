from flask import Flask, request

import json
from io import BytesIO, BufferedReader

from PIL import Image

from img_classifier import predictor

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def hello():
    return json.dumps({'success': True})


@app.route('/predict/<image_guid>', methods=['POST'])
def predict(image_guid):
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
