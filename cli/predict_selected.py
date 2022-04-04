import json
import os
import time
from threading import Thread
from subprocess import Popen, PIPE

# Where the images should be exported to.  Also where the results will be written to.
working_path = r'C:\Projects\RestData\Exports\Enron Images\Items\sub'

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
    results_file = os.path.join(path_to_results, 'inference.json')
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
                    print(str(status['status']['progress']) + ' [' + str(status['status']['current_item']) +
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
    return exporter


def export_selection(output_dir):
    items_to_export = [item for item in current_selected_items if
                       item.getName().lower().endswith('.jpg') or item.getName().lower().endswith('.jpeg')]
    exporter = build_exporter(output_dir)
    exporter.exportItems(items_to_export)
    return len(items_to_export)


if __name__ == "__builtin__":
    count_to_export = export_selection(working_path)
    if count_to_export == 0:
        # No items to export
        print('No items to export or analyze.')
    else:
        initialize_environment()
        execute_scoring(working_path)
        monitor_progress(working_path)
