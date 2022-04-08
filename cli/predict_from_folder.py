import json
import os
import sys

from PIL import Image
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


def get_file_list(folder):
    """
    Generate a list of all the files in the folder which will be processed.  The folder itself, and all subfolders
    recursively will be examined for JPEG files.  All found JPEG files will have their full path added to the list.
    :param folder: The root path to search for images to analyze
    :return: A list of all JPEGs in the root folder or any of its children.
    """
    file_paths = []
    for root, dirs, names in os.walk(folder):
        for name in names:
            file_paths.append(os.path.join(root, name))
    return [name for name in file_paths
            if name.lower().endswith('.jpg') or name.lower().endswith('.jpeg')]


def get_image_generator(file_list, output_obj, output_file):
    """
    This is an enclosure for the Image Generator to be provided to the predictor.  This method holds the
    data source and returns the generator function.
    :param file_list: List of files to predict
    :param output_obj: The data object to use for storing status results in
    :param output_file: The file to which status updates should be written
    :return: A function which will yield images in PIL format when called.
    """
    status_obj = output_obj['status']
    item_count = len(file_list)

    def read_image():
        """
        Open images from the provided list, turn them into PIL formatted RGB images, and
        return them one at a time.
        :return: Yields 1 RGB PIL image at a time.
        """
        for index, image in enumerate(file_list):
            img_pixels = Image.open(image).convert('RGB')
            print(f'{image}: {img_pixels.size}')
            yield img_pixels
            status_obj['current_item'] = index + 1
            percent_complete = int((index / item_count) * 100)
            status_obj['progress'] = percent_complete
            with open(output_file, mode='w') as status:
                json.dump(output_obj, status)

    return read_image


def main(input_dir):
    results = os.path.join(input_dir, 'inference.json')

    # Get the list of images to predict
    image_list = get_file_list(input_dir)

    # Build the objects that will hold results
    errors = []
    status_obj = {'total': len(image_list), 'done': False, 'progress': 0, 'current_item': 0, 'errors': errors}
    inference_results = {}
    output_obj = {'status': status_obj, 'results': inference_results}

    # Initialize the results file
    with open(results, mode='w') as status:
        json.dump(output_obj, status)

    # Call the prediction, using the image generator as source
    inferences = predictor.predict(get_image_generator(image_list, output_obj, results))

    # Write the predictions into the results file
    for index, inference in enumerate(inferences):
        img = image_list[index]
        img_classes = []

        if 'ERROR' == inference[0]:
            # If there was an error predicting an image, pass the error along with the image that caused it
            errors.append(f'{img}: {inference[1]}')
        else:
            # Add the predictions for each image to a list, and assign the list to the image's results
            for result in inference:
                img_classes.append({result[0]: str(result[1])})
            inference_results[img] = img_classes

        # Output the results for the image
        with open(results, mode='w') as status:
            json.dump(output_obj, status)

    # Signal the completion of work
    output_obj['status']['done'] = True
    output_obj['status']['progress'] = 100

    with open(results, mode='w') as status:
        json.dump(output_obj, status)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Missing input directory argument.  Run this application as')
        print('> python.exe predict_from_folder.py <absolute path to images>')
    else:
        main(sys.argv[1])
