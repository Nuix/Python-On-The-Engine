import os
from subprocess import Popen, PIPE

# Where the images should be exported to.  Also where the results will be written to.
working_path = r'C:\Projects\RestData\Exports\Enron Images\Items\sub'

# Top level of the python path to find the CLI and classification scripts.
python_project_path = r'C:\Projects\Python\Python-On-The-Engine'
# Module and Script file to run
predict_script = r'cli\predict_from_folder.py'

# Path to the Python environment
python_env_path = r'C:\Projects\Python\Python-On-The-Engine\env'


def initialize_environment():
    python_path = python_project_path + ';' + python_env_path + ';' + python_env_path + r'\Lib;' + \
                  python_env_path + r'\DLLs;' + python_env_path + r'\Library\user\bin;' + \
                  python_env_path + r'\Library\bin;' + python_env_path + r'\bin'
    path = os.getenv('PATH') + ';' + python_path

    os.environ['PYTHONPATH'] = python_path
    os.environ['PATH'] = path


def execute_scoring(path_to_images):
    python_script = python_project_path + '\\' + predict_script

    cmd_args = ['python.exe', python_script, path_to_images]

    predict_process = Popen(cmd_args, stdout=PIPE, universal_newlines=True, shell=True)

    return_code = None
    while return_code is None:
        return_code = predict_process.poll()
        if return_code is None:
            output = predict_process.stdout.readline()
            print(output)
        else:
            print('Return Code: ' + str(return_code))
            output = predict_process.stdout.readlines()
            print(output)


def build_exporter(output_dir):
    exporter = utilities.createBatchExporter(output_dir)
    exporter.addProduct('native', { 'naming': 'item_name' })
    exporter.setTraversalOptions({
        'strategy': 'items',
        'deduplication': 'md5',
        'sortOrder': 'position'
    })
    return exporter


def export_selection(output_dir):
    items_to_export = [item for item in current_selected_items if item.getName().lower().endswith('.jpg') or item.getName().lower().endswith('.jpeg')]
    exporter = build_exporter(output_dir)
    exporter.exportItems(items_to_export)


if __name__ == "__builtin__":
    export_selection(working_path)
    initialize_environment()
    execute_scoring(working_path)
