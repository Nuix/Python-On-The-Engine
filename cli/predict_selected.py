"""
Author: Steven Luke (steven.luke@nuix.com)
Date: 2022.04.04
Engine Version: 9.6.8

Summary: Perform an image classification on the selected images in Nuix Workstation.

Description:
This script is intended to be used from inside the Nuix Workstation Scripting Console.  It will
launch a subprocess to run an image classification routine on selected JPG files.  It will read
the results of the classification and add it as metadata to the images.

This script will first export any selected JPGs to a file specified in this script.  It will
then run an external Python process to do the classification.  The Python environment and
application path are provided in this script.  Once the external Python application is started,
this script will monitor a JSON file for progress and results.  When the Python application
is finished it will read the results and add them to the appropriate image as custom metadata
named 'image_classifications_top3'

Requirements:
A Python environment capable of running the image classification.  For this example, the
cli.predict_from_folder.py script is used as the entry point for the analysis, and that uses the
img_classifier.predictor.py to run the classification.  Both of these scripts and the conda
environment file used to run them are provided in the same repository as this script.

Before running this script, have an open case and select some JPEG images.

Setup the working_path variable to be a path to the folder you want to export results to.  It will
also be used to store the JSON results before they get red in to custom metadata.  If the folder
does not exist, it will be created.  The contents of the folder will be cleaned out at the end of the
script but the folder itself will not be (even if this script creates it). WARNING: This folder will be
completely cleaned out at the end of the process.  DO NOT USE A FOLDER WITH EXISTING CONTENT!

This script relies on an external Python application, as mentioned, that requires a configured
environment.  Use the python_env_path to define the path to the Python environment - the folder
where the python.exe is located.  This application will set up temporary environment variables
when running the Python application.  There could be issues if there is an existing Python
environment on the system path.

Use the python_project_path variable to configure the path to the downloaded reposity.  It should
point to the top level of the repository - it should have /cli and /img_classifier subfolders of the
repository this script came in.


"""
import json
import os
import re
import time
from subprocess import Popen, PIPE

# Where the images should be exported to.  Also where the results will be written to.
# WARNING: The contents WILL be deleted at the end - don't use a folder with existing content!
working_path = r'C:\Projects\RestData\Exports\temp'

# Top level of the python path to find the CLI and classification scripts.
python_project_path = r'C:\Projects\Python\Python-On-The-Engine'
# Module and Script file to run
predict_script = r'cli\predict_from_folder.py'

# Path to the Python environment
python_env_path = r'C:\Projects\Python\Python-On-The-Engine\env'

# Amount of time between polls of the results file when monitoring for progress
results_poll_time = 3  # in seconds
# The name of the results file generated during image classification
results_json_filename = 'inference.json'


def initialize_environment():
    """
    Prepare the Python Environment using environment variables so the called Python application runs the correct version
    and with the expected libraries.  Adds the Python executable and libraries on the environment's PATH and creates and
    sets the PYTHONPATH.  These environment changes are transient but having other python libraries on the PATH could
    interfere.

    :return: Nothing
    """
    python_path = python_project_path + ';' + python_env_path + ';' + python_env_path + r'\Lib;' + \
        python_env_path + r'\DLLs;' + python_env_path + r'\Library\user\bin;' + \
        python_env_path + r'\Library\bin;' + python_env_path + r'\bin'
    path = python_path + ";" + os.getenv('PATH')

    os.environ['PYTHONPATH'] = python_path
    os.environ['PATH'] = path


def monitor_export_process(item_process_info):
    """
    This is the callback used with the batch exporter.
    :param item_process_info: The ItemProcessInfo object with details about the processing step.
    :return: Nothing
    """
    print(item_process_info.getStage() + ' #' + str(item_process_info.getStageCount()) + \
          ': ' + item_process_info.getItem().getName() + \
          ' (' + item_process_info.getState() + ')'
          )


def execute_scoring(path_to_images):
    """
    Start the external Python process for image classification.  This method is asynchronous - the process will be
    started and this method will return immediately.

    :param path_to_images:  Full path to the images that need to be classified.
    :return: The Process object inside which the Python application is run, incase it is needed for monitoring purposes.
             The stdout is PIPEd so it can be read from the returned Process object.
    """
    python_script = python_project_path + '\\' + predict_script

    cmd_args = ['python.exe', python_script, path_to_images]

    predict_process = Popen(cmd_args, stdout=PIPE, universal_newlines=True, shell=True)

    return predict_process


def monitor_progress(path_to_results):
    """
    Use the JSON file created by the classification tool to monitor the progress of the operation.  This does not read
    the stdout of the process, rather it reads the JSON file and parses it for progress.  This method will block until
    the JSON file signals the work is done.
    :param path_to_results: Full path to where the results file will be stored (without the results file name).
    :return: Nothing
    """
    results_file = os.path.join(path_to_results, results_json_filename)
    while not os.path.exists(results_file):
        # File not made yet, keep trying
        time.sleep(results_poll_time)

    done = False

    while not done:
        with open(results_file, 'r') as status_file:
            try:
                status = json.load(status_file)

                done = status['status']['done']
                if not done:
                    print('Progress: ' + str(status['status']['progress']) + '% [' + str(
                        status['status']['current_item']) +
                          '/' + str(status['status']['total']) + ']')
            except ValueError as err:
                # Don't care, this happens when the file is written at same time as reading, just skip and continue
                pass

        time.sleep(results_poll_time)
    print('Finished prediction')


def build_exporter(output_dir):
    """
    Generate the BatchExporter object to export the items of interest.  The exported will export to the directory
    specified, will export in GUID naming format, and will de-duplicate the items before export.
    :param output_dir: The full path to the folder where the exporter will save images
    :return: The configured BatchExporter
    """
    exporter = utilities.createBatchExporter(output_dir)
    exporter.addProduct('native', {'naming': 'guid'})
    exporter.setTraversalOptions({
        'strategy': 'items',
        'deduplication': 'md5',
        'sortOrder': 'position'
    })
    exporter.whenItemEventOccurs(monitor_export_process)
    return exporter


def export_selection(output_dir):
    """
    Exports the selected JPEG images to the specified directory.  If the directory does not exist yet it will be
    created.  Only selected images with the extension .jpg or .jpeg (case-insensitive) will be exported.
    :param output_dir: The full path where images should be exported to.
    :return: The number of items exported.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    items_to_export = [item for item in current_selected_items if
                       item.getCorrectedExtension().lower().endswith('jpg') or
                       item.getCorrectedExtension().lower().endswith('jpeg')]
    exporter = build_exporter(output_dir)
    exporter.exportItems(items_to_export)
    return len(items_to_export)


# Images are stored on disk and in the results using the GUID as their name.  This regex parses the GUID
# out of the name and returns is as Group 1.
regex_for_GUID = r'^.*\\([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.[jJ][pP][eE]?[gG]$'


def get_item(item_guid):
    """
    Search for the item that matches the provided GUID
    :param item_guid: The GUID for the item to find
    :return: The first found Item with the provided GUID
    """
    query_string = 'guid:' + item_guid
    found = current_case.searchUnsorted(query_string)
    return found.iterator().next()


def process_image_metadata(image_data):
    """
    Add the predicted classifications as custom metadata to the corresponding Item.

    Find the Item for the image this prediction was made for, then create the custom metadata named
    'image_classifications_top3' and add the results of the top 3 predictions to it.  The metadata will be in the
    format: "<classifier1>:<probability1>%;<classifier2>:<probability2>%;<classifier3>:<probability3>%"

    :param image_data: The data for a single image.  It should be a tuple:
                       [0] = the full path to the exported image this data was created for.  The image should have its
                             GUID for a name - as generated by a BatchExporter with naming='guid'
                       [1] = an array-like with the three dicts mapping the classification to its score.
    :return: Nothing
    """
    image_path = image_data[0]
    predictions = image_data[1]
    image_guid_match = re.match(regex_for_GUID, image_path)
    if image_guid_match is not None:
        image_guid = image_guid_match.group(1)
        prediction_data = ';'.join([list(pred.items())[0][0] + ':' +
                                    str(round(float(list(pred.items())[0][1]) * 100, 2)) + '%'
                                    for pred in predictions]
                                   )
        item_to_update = get_item(image_guid)
        item_custom_metadata = item_to_update.getCustomMetadata()
        item_custom_metadata['image_classifications_top3'] = prediction_data


def process_results(results_path):
    """
    After the classification is complete, parse the results file and assign each prediction to its corresponding image
    as custom metadata.
    :param results_path: The full path (not including the file name) where the results file will be found.
    :return: Nothing
    """
    with open(os.path.join(results_path, results_json_filename), 'r') as results_file:
        process_results_data = json.load(results_file)
        prediction_results = process_results_data['results']

        for image_results in prediction_results.items():
            process_image_metadata(image_results)


def cleanup(output_dir):
    """
    Empties the contents of the output directory.  This directory was the one pointed to for the image export and
    includes the JSON file for the classification results.

    WARNING:  All the contents of this folder will be deleted, so don't use a folder with data you want to keep!

    :param output_dir: The directory to remove
    :return: Nothing
    """
    for root, dirs, files in os.walk(output_dir, topdown=False):
        for file_name in files:
            os.remove(os.path.join(root, file_name))
        for dir_name in dirs:
            os.rmdir(os.path.join(root, dir_name))


if __name__ == "__builtin__":
    """
    This code will be run only when loaded and executed from a '__builtin__' environment such as the Scripting
    Console or Script menu in Nuix Workstation.  It will not be run from the command line, or run when this
    script is imported into another script as a module.
    """
    count_to_export = export_selection(working_path)
    if count_to_export == 0:
        # No items to export
        print('No items to export or analyze.')
    else:
        initialize_environment()
        execute_scoring(working_path)
        monitor_progress(working_path)
        process_results(working_path)
        cleanup(working_path)
