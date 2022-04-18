# Python-On-The-Engine
There are multiple ways to use Python with the Nuix Engine.  This repository is made as a companion to the "Python On
The Engine" blog post. <TODO Create a Link>  It demonstrates some of the methods to methods described in the blog.

## Run Python from the Command Line Interface
The `cli` package is designed as an example of calling an external Python application using the command line or shell.
It consists of three parts:
1. The `img_classifier` package: An external application that uses Keras to do some image classification.  See the 'Image Classification Side Project' for more information.
2. `cli.predict_from_folder.py`: A Command Line Interface wrapper around the above code so it can take in parameters and run the prediction.  This needs an external Python environment to run in.  See 'The External Environment' below for details.
3. `cli.predict_selected.py`: A script to run from the Interactive Scripting Console inside Nuix Workstation.

To run this example, ensure you have a properly configured external Python environment as described below to run the
prediction and command line application in.  Launch Nuix Workstation, open a case, and select some images - at least
some that are JPEGs (with jpg, or jpeg extensions).  Launch the interactive scripting console from the Scripting menu
using the Show Console action.  Copy the contents of `cli.predict_selected.py` into the console.  You will need to 
modify some values at the top of the script:

```python
# Where the images should be exported to.  Also where the results will be written to.
# WARNING: The contents WILL be deleted at the end - don't use a folder with existing content!
working_path = r'C:\Projects\RestData\Exports\temp'

# Top level of the python path to find the CLI and classification scripts.
python_project_path = r'C:\Projects\Python\Python-On-The-Engine'
# Module and Script file to run
predict_script = r'cli\predict_from_folder.py'

# Path to the Python environment
python_env_path = r'C:\Projects\Python\Python-On-The-Engine\env'
```

The `working_path` should be set to a temporary directory where images will be exported.  The entire contents of the 
folder will be deleted when the script is done - so use a new empty folder.

The `python_project_path` should be the full path to the top of this repository.  There should be a subfolder 'cli'
and a different subfolder called 'img_classifier'.

The `predict_script` is the Python file the console script will execute.  It should be the package.file format
relative to the `python_project_path`.  Assuming you are running the code present in this repository it should not need
to change.

The final one is `python_env_path`.  This script makes no assumptions about your Python environment being added to your
environment PATH, being naturally executable from the command / shell, and the PYTHONPATH being configured.  This helps
running the application on systems with multiple Python environments.  To do this, the script needs to know the path to
the Python.exe.  Use the `python_env_path` variable to point to the folder where the external Python environment is
located (this should be the folder, and should not include the python.exe file itself).  Ensure this variable points to
the path where the external Python environment described below in 'The External Environment'.

Once these modifications are made you can execute the script, during which the progress of the export and processing
will be displayed at the bottom of the Console.

Note that this script could run from the Script menu by copying the `predict_selected.py` file into your user script
directory.  However, when you do this, you don't get to see the output in the console.  There are other ways to show
progress in scripts (see the NX repository on our GitHub) but doing so was beyond the scope of these examples.

## Connect to a Python Microservice
The `microservice` package is an example of using an external Python microservice from inside the Nuix Workstation.  It
is similar to the `cli` package in design and purpose, the difference being how the external application runs and
therefore how you interact with it.  This package consists of three parts:
1. The `img_classifier` package: An external application that uses Keras to do some image classification.  See the 'Image Classification Side Project' for more information.
2. `microservice.predict_service.py`: A Flask application that wraps the image classifier so the prediction can be accessed as a microservice.  This needs the external Python environment to run.  See 'The External Environment' below for details.
3. `microservice.predict_selected.py`: A script to run from the Interactive Scripting Console inside Nuix Workstation.

To run this example, ensure you have a  properly configured external Python environment described below to run the
prediction and Flask application in.  In addition to installing the environment, you will also need to configure some
parameters for the Flask application.  When testing this code, I used the following Environment Variables to do so:
* `FLASK_RUN_PORT=8982`: Configures the port to use to access the service.
* `FLASK_ENV=development`: Turns debug on, limits access to localhost, and reloads code changes
* `FLASK_APP=microservice.predict_service`: Sets the `microservice.predict_service` as the Flask entry point

When running the Flask application, the root of this repository should be the Working Directory so the `microservice.
predict_service` script can be found.  See the Flask documentation for more detailed configuration options.

You should launch the Flask microservice prior to trying to connect to it from Workstation.  Once you have it running
launch Nuix Workstation, load a case, and select some images with at least a few JPG images selected.  Then open
the interactive scripting console using Scripts > Show Console.  Copy the contents of `microservice.predict_selected` to
the Script part of the console.  You may need to make some adjustments to script as follows:
```python
HOST = 'http://127.0.0.1:8982'
```

Adjust the HOST to properly reflect the URL of the host computer running the microservice.  If the microservice is
running on the local computer and is in development mode, then leave the IP address as `127.0.0.1`, otherwise you may
need to adjust it to the correct IP or Host Name for the computer.  Additionally, you should change the Port Number to
match that provided to the `FLASK_RUN_PORT` environment variable.  If this value is not set then it defaults to 5000.

With those changes made you can execute the script and you should start to see the requests and results show up in the
bottom of the Console window.

## Connect to the RESTful Service
The `restful` package uses a running instance of the Nuix RESTful Service to call into the Nuix Engine from an external
application.  It requires a separate, running instance of the RESTful Service - see this documentation on how to set it
up: https://nuix.github.io/sdk-docs/latest/products/core_engine/rest_api.html.

The external Python application has minimal requirements - just the `requests` library which can be installed from pip
or Anaconda.  The repository has an environment.yml file which can be used to create a full Anaconda environment that
can be used with the code here.  The application will do a paged search for all items in a case, tag each item on a page,
and then export the items of a particular page - for example if you had limited space to export to you could first split
all the items into 1000 items count pages using tags.  Then export one page at a time, process the export, clear the
exported data, and do the next page.  It also has an module which will clear the tags used to mark items for export.

All the configuration for the application can be found in the `config.json` file at the base of the repository.  The
pertinent settings are:
```json
{
  "rest": {
    "host": "http://localhost",
    "port": "8080",
    "case_name": "Enron",
    "search": {
      "search_query": "*",
      "page_size": 1000
    },
    "export": {
      "path": "C:/Projects/Playground/Temp",
      "subfolder": "export_{id}",
      "tag_format": "export|{year}.{month}.{day}|pg{page}",
      "tag_query": "tag:{export_tag}",
      "workers": 2
    }
  },
  "license": {
    "type": "enterprise-workstation",
    "workers": 4,
    "location_type": "cloud-server",
    "location": "https://licence-api.nuix.com"
  }
}
```

The first section, `rest` is used for configuring the connection with the RESTful service:
* `host`: Host name for accessing the REST server
* `port`: Port number the REST uses to communicate on.
* `case_name` The sample code will connect to a particular case to export.  Supply the name of the case name here.
* `search.search_query`: This is the initial search query used to tag items for export.  The setting here tags all items, but you might use some query to limit the items to be exported.
* `search.page_size`: The number of items per 'page' to be exported.
* `export.path`: Full path to the folder where items will be exported.  Items will be exported into a sub-folder in this directory.
* `export.subfolder`: The format of the subfolder name to export.  The {id} will be replaced by the page number being exported
* `export.tag_format`: Format of the tag that will be added to items for export.  Use the `|` character to create sub-tags.  User {page} to insert the page number, and {day}, {month}, and {year} to insert the date
* `export.tag_query`: Query to use to find the items to export.  Use {export_tag} to insert the calculated export tag (as per the `export.tag_format`).  This gives the opportunity to further limit what items to export.
* `export.workers`: Provide the number of workers to dedicate to the export job

The next section is about configuring the `license` to use for this session:
* `type`: The short name of the license type to acquire
* `workers`: Number of workers to claim, if applicable to the license type
* `location_type`: The type of the license source to use, such as cloud-server, or NMS server.
* `location`: The host name of the license source to use.

## Run the Nuix Engine Java API from Python
What is needed to run the Java API example

## The Image Classifier Side Project
To demonstrate some previous examples, a more complex Python application was created as a stand in for
why you might use the Command Line or Microservice strategies.  This is far from a real or complete image prediction
or classification scheme - it just uses the pre-trained ResNet50 with weights from the imagenet library.  It is not
suitable for e-forensics or discovery.  This project consists of a single predict method that takes in a sequence of
PIL images and produces the top 3 predictions and their score.

This application is expected to run in a Python 3.9+ environment with Keras and TensorFlow.  See 'The External 
Environment' below for how to make an environment suitable for running this.  This application itself doesn't actually
run.  It is intended to be used along side the `cli` package to be run as a standalone Command Line application, or with
the `microservice` package to be run inside a Flask application.

## The Python Environment
For this repository, you can think of there being two separate Python environment.

### The 'In Engine' Environment
This is the Python environment provided by Nuix as part of its scripting interface, and is used by Worker Side Scripts,
the Interactive Scripting Console, from the Scripting Menu, and other scripts run from inside Workstation or the Engine.
It is a Jython environment and is compatible with Python version 2.7.2.  The scripts running 'In Engine' here do not
require any specific Python libraries but do make use of Java libraries provided by the engine.  Most notably, the
in engine script part of the Microservice sample uses the Apache Commons HttpClient.

### The External Environment
External scripts were all written using a common Anaconda environment.  The environment configuration file is provided
in the 'environment.yml' file at the top level of this repository.  Note that this environment contains configuration
for the Microservice (Flask), the Image Classifier (SciKit Image, TensorFlow and Keras) the RESTful Service Client 
(requests) as well as the Java In Python example (pyjnius).  So this environment will contain more than would be
needed for any specific application based on one of these approaches.

To duplicate this environment in Anaconda use the following command: 
`conda env create -p C:\Projects\Python\Temp -f environment.yml`

