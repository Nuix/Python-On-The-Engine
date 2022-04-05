import json
import os
import re
import time
from threading import Thread
from subprocess import Popen, PIPE

# Where the images should be exported to.  Also where the results will be written to.
working_path = r'C:\Projects\RestData\Exports\temp'
results_json_filename = 'inference.json'

# Top level of the python path to find the CLI and classification scripts.
python_project_path = r'C:\Projects\Python\Python-On-The-Engine'
# Module and Script file to run
predict_script = r'cli\predict_from_folder.py'

# Path to the Python environment
python_env_path = r'C:\Projects\Python\Python-On-The-Engine\env'

# Amount of time between polls of the results file when monitoring for progress
results_poll_time = 3  # in seconds


def initialize_environment():
    python_path = python_project_path + ';' + python_env_path + ';' + python_env_path + r'\Lib;' + \
                  python_env_path + r'\DLLs;' + python_env_path + r'\Library\user\bin;' + \
                  python_env_path + r'\Library\bin;' + python_env_path + r'\bin'
    path = os.getenv('PATH') + ';' + python_path

    os.environ['PYTHONPATH'] = python_path
    os.environ['PATH'] = path


def monitor_export_process(item_process_info):
    print('Exported #' + str(item_process_info.getStageCount()) + \
          ': ' + item_process_info.getItem().getName() + \
          ' (' + item_process_info.getState() + ')'
          )


def get_process_monitor(prediction_process):
    def monitor():
        return_code = None
        while return_code is None:
            return_code = prediction_process.poll()
            if return_code is None:
                output = prediction_process.stdout.readline()
                print(output)
            else:
                print('Return Code: ' + str(return_code))
                output = prediction_process.stdout.readlines()
                print(output)

    return monitor


def execute_scoring(path_to_images):
    python_script = python_project_path + '\\' + predict_script

    cmd_args = ['python.exe', python_script, path_to_images]

    predict_process = Popen(cmd_args, stdout=PIPE, universal_newlines=True, shell=True)

    monitor_thread = Thread(target=get_process_monitor(predict_process), name='Prediction Monitor')
    monitor_thread.start()


def monitor_progress(path_to_results):
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
                    print('Progress: ' + str(status['status']['progress']) + '% [' + str(status['status']['current_item']) +
                          '/' + str(status['status']['total']) + ']')
            except ValueError as err:
                # Don't care, this happens when the file is written at same time as reading, just skip and continue
                pass

        time.sleep(results_poll_time)
    print('Finished prediction')


def build_exporter(output_dir):
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
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    items_to_export = [item for item in current_selected_items if
                       item.getName().lower().endswith('.jpg') or item.getName().lower().endswith('.jpeg')]
    exporter = build_exporter(output_dir)
    exporter.exportItems(items_to_export)
    return len(items_to_export)


regex_for_GUID = r'^.*\\([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.[jJ][pP][eE]?[gG]$'


def get_item(item_guid):
    query_string = 'guid:' + item_guid
    found = current_case.searchUnsorted(query_string)
    return found.iterator().next()


def process_image_metadata(image_data):
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
    with open(os.path.join(results_path, results_json_filename), 'r') as results_file:
        process_results_data = json.load(results_file)
        prediction_results = process_results_data['results']

        for image_results in prediction_results.items():
            process_image_metadata(image_results)


def cleanup(output_dir):
    for root, dirs, files in os.walk(output_dir, topdown=False):
        for file_name in files:
            os.remove(os.path.join(root, file_name))
        for dir_name in dirs:
            os.rmdir(os.path.join(root, dir_name))


if __name__ == "__builtin__":
    count_to_export = export_selection(working_path)
    if count_to_export == 0:
        # No items to export
        print('No items to export or analyze.')
    else:
        initialize_environment()
        execute_scoring(working_path)
        monitor_progress(working_path)
        process_results(working_path)
