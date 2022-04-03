import json
import os

from skimage.io import imread

from img_classifier import predictor

"""
Run an inference on all JPG images in the input directory.  Write the an inference.json file with the results.  The
JSON output will have two sections:
{
    "status": <progress of the analysis>,
    "results": <results of the analysis>
}

The status will contain an object like this:
{
    "done": True|False,
    "progress":<percent complete>,
    "current_item": <index of item being worked on>
    "total": <total count of items>
    "errors": <list of encountered errors>
}

The results will be a map with the name of the image and a list of the classification results
{
    <image name>: [
        {<classification_1>: <score_1>},
        {<classification_2>: <score_2>},
        {<classification_3>: <score_3>}
    ]
}

The results file will be regularly updated with the status and progress, at which point the results section may
be updated as well.  The results should not be considered correct until the "done" status returns true.  If the
errors list is empty then there was no error and all images were successful.
"""

input_dir = r"C:\Projects\RestData\Exports\Enron Images\Items"
results = os.path.join(input_dir, 'inference.json')


def get_file_list(folder):
    return [os.path.join(folder, name) for name in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, name)) and name.endswith('.jpg')]


def get_image_generator(file_list, status_obj):
    item_count = len(file_list)

    def read_image():
        for index, image in enumerate(file_list):
            yield imread(image)
            status_obj['current_item'] = index + 1
            percent_complete = int((index / item_count) * 100)
            status_obj['progress'] = percent_complete
            with os.open(results) as status:
                json.dump(status_obj, status)

    return read_image

def main():
    image_list = get_file_list(input_dir)
    status_obj = {'total': len(image_list), 'done': False, 'progress': 0, 'current_item': 0, 'errors': [], 'results': {}}
    with os.open(results) as status:
        json.dump(status_obj, status)

    inferences = predictor.predict(get_image_generator(image_list, status_obj))

    inference_results = {}
    status_obj['results'] = inference_results
    for index, inference in enumerate(inferences):
        img = image_list[index]
        img_classes = []
        for result in inference:
            img_classes.append({result[0]: result[1]})
        inference_results[img] = img_classes

        with os.open(results) as status:
            json.dump(status_obj, status)

