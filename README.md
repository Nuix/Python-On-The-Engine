# Python-On-The-Engine
There are multiple ways to use Python with the Nuix Engine.  This repository is made as a companion to the "Python On
The Engine" blog post. <TODO Create a Link>  It demonstrates some of the methods to methods described in the blog.

## Worker Side Scripts
What is needed to run the Worker Side Script example

## Interactive Console
What is needed to run the Interactive Console Script example

## Run Python from the Command Line Interface
This package consist of three parts:
1. The `img_classifier` package: An external application that uses Keras to do some image classification.  See the 'Image Classification Side Project' for more information.
2. `cli.predict_from_folder.py`: A Command Line Interface wrapper around the above code so it can take in parameters and run the prediction.  This needs an external Python environment to run in.  See 'The External Environment' below for details.
3. `cli.predict_selected.py`: A script to run from the Interactive Scripting Console inside Nuix Workstation.

To run this example, ensure you have a properly configured external Python environment as described below to run the
prediction and command line application in.  Launch Nuix Workstation, open a case, and select some images - at least
some that are JPEGs (with jpg, or jpeg extensions).  Launch the interactive scripting console from the Scripting menu
using the Show Console action.  Copy the contents of `cli.predict_selected.py` into the console.  You will need to 
modify some values at the top of the script:

```
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
What is needed to run the Microservice example

## Connect to the RESTful Service
What is needed to run the RESTful Client example

## Run the Nuix Engine Java API from Python
What is needed to run the Java API example

## The Image Classifier Side Project
To demonstrate some previous examples, a more complex Python application was created as a stand in for
why you might use the Command Line or Microservice strategies.

What is needed to run the Image Classifier code.

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

