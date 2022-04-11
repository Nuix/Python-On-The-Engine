"""
Author: Steven Luke (steven.luke@nuix.com)
Date: 2022.04.04
Engine Version: 9.6.8
Python Version: 3.9

Summary: Use Python to connect to the Nuix Engine Java API, using the example of getting a license from a license server.

Description:
This is a simple command line application that uses the Java API to the Nuix Engine to connect to a cloud-server for
and get an enterprise-workstation license.  It is used as a demo on how it could be done, not as a full blown workflow.

This module relies on the environment variables 'nuix_user' and 'nuix_password' to be set in order to log in to the
license server.

This module relies on an installed Java JRE to run properly, and needs a reference to the Nuix Engine Java API.  It
will use the JRE shipped with the nuix-engine as the Java Runtime.  You must provide the full path to the Nuix
Engine in the appropriate variable.
"""
import os

# Path to the Nuix Engine
nuix_engine_path = r'C:\Projects\nuix-engine'

# The case worker that will be used to track changes made this session
NUIX_USER = 'Inspector Gadget'
# Path to the user data directories for this case worker.
USER_DATA_DIR = r'C:\Projects\RestData'

# License configuration settings
LICENSE_TYPE = 'enterprise-workstation'
LICENSE_SOURCE_TYPE = 'cloud-server'
LICENSE_SOURCE_LOCATION = 'https://licence-api.nuix.com'
WORKER_COUNT = 4


def initialize_environment():
    """
    Setup the JAVE_PATH, CLASSPATH, and PATH environment variables needed to load the JAVA environment.  All the JARs in
    the Engine's lib and lib/non-fips directories are added to the CLASSPATH.  The Engine's bin, jre and bin/server are
    added to the PATH.  And the JAVA_HOME is set to the Engine's JRE.  These changes are local to this running
    process and will not affect the outside system or linger longer than the application's lifetime.

    This method muse be called prior to importing the pyjnius Java environment module.

    :return: Nothing
    """

    engine_bin = os.path.join(nuix_engine_path, 'bin')
    engine_lib = os.path.join(nuix_engine_path, 'lib', '*')
    engine_ssl = os.path.join(nuix_engine_path, 'lib', 'non-fips', '*')
    engine_jre = os.path.join(nuix_engine_path, 'jre')
    engine_jvm = os.path.join(engine_jre, 'bin', 'server')

    classpath = ';'.join(['.', engine_lib, engine_ssl])
    java_home = engine_jre
    path_update = ';'.join([java_home, engine_jvm, engine_bin])

    os.environ['JAVA_HOME'] = java_home
    os.environ['CLASSPATH'] = classpath
    os.environ['PATH'] = f'{path_update};{os.environ["PATH"]}'


initialize_environment()

# IDEs identify java_method as not existing - it does, it is just created and not visible to intellisense type tools.
from jnius import autoclass, PythonJavaClass, java_method


class PCredentialsCallback(PythonJavaClass):
    """
    implements nuix.engine.CredentialsCallback

    This is a Python extension of a Java class used to implement a Java interface.  This particular interface is a
    callback from the Engine when it needs to get the credentials needed to authenticate with the license server.
    """
    __javainterfaces__ = ['nuix/engine/CredentialsCallback']

    @java_method('(Lnuix/engine/CredentialsCallbackInfo;)V')
    def execute(self, info):
        """
        Called when the Engine needs to log in to the license server.  This provides the passed in
        CredentialsCallbackInfo object the user name and password needed to log in.  This implementation uses the
        environment variables 'nuix_user' and 'nuix_password' to retrieve the credentials.
        :param info: A nuix.engine.CredentialsCallbackInfo object to receive the username and password
        :return: Nothing
        """
        print('Credentials Callback Called')
        info.setUsername(os.environ['nuix_user'])
        info.setPassword(os.environ['nuix_password'])


class PLicenseSourcePredicate(PythonJavaClass):
    """
    implements java.util.function.Predicate

    This is a Python extension of a Java class used to implement the Predicate interface.  It is designed to be used
    to filter all possible license sources to the one we define in the LICENSE_SOURCE_LOCATION variable.
    """
    __javainterfaces__ = ['java/util/function/Predicate']

    @java_method('(Ljava/lang/Object;)Z')
    def test(self, licence_source):
        """
        Called when filtering License Source Streams.  Returns True if the passed-in license source matches the
        desired location as defined by the LICENSE_SOURCE_LOCATION variable.  False otherwise.
        :param licence_source: The nuix.engine.LicenseSource to check for matching our requirements
        :return: True if the license_source matches our requirements, False otherwise
        """
        print('License Test Called')
        return LICENSE_SOURCE_LOCATION == licence_source.getLocation()


def dict_to_immutablemap(items_dict):
    """
    Python dicts (dictionaries) aren't auto-convertable to java.util.Maps and so can't be passed natively to Engine
    methods that expect Maps for configuration.  This is a common need in the Java API.  Use this method to convert
    a dict to a com.google.common.collect.ImmutableMap with the same contents so it can be used as a config parameter.
    :param items_dict: The Python dictionary to translate to a Java Map
    :return: An immutable java.util.Map implementation with the same contents as the items_dict.
    """
    ImmutableMap = autoclass('com.google.common.collect.ImmutableMap')
    map_builder = ImmutableMap.builder()
    for item in items_dict.items():
        map_builder.put(item[0], item[1])
    return map_builder.build()


def get_engine(user, user_dir, container):
    """
    Factory method to build a new Nuix Engine
    :param user: The case worker used to track work done this session
    :param user_dir: The case worker's data directory root
    :param container: The nuix.engine.GlobalContainer to build the Engine intance in
    :return: A new, un-licensed nuix.engine.Engine
    """
    configs = dict_to_immutablemap({'user': user, 'userDataDirs': user_dir})
    engine = container.newEngine(configs)

    return engine


def claim_license(engine):
    """
    Claim a license for the Engine using the license configuration defined in the LICENSE_SOURCE_... variables, with
    the number of worked in WORKER_COUNT (if allowed by the license), and authenticated by the PCredentialsCallback.

    :param engine: An (assumed) unlicensed nuix.engine.Engine to get a license for.
    :return: If a proper license is found, the licensed nuix.engine.Engine, otherwise None.
    """
    engine.whenAskedForCredentials(PCredentialsCallback())

    license_config = dict_to_immutablemap({'sources': [LICENSE_SOURCE_TYPE]})
    worker_config = dict_to_immutablemap({'workerCount': WORKER_COUNT})

    # Filter license options down to the one(s) we want based on their location
    found_licenses = engine.getLicensor().findLicenceSourcesStream(license_config) \
        .filter(PLicenseSourcePredicate()) \
        .collect(Collectors.toList())

    for license_source in found_licenses:
        print(f'{license_source.getType()}: {license_source.getLocation()}')

        # Then further filter down base on their type
        for available_license in license_source.findAvailableLicences():
            license_type = available_license.getShortName()
            print(f'Inspecting License Type {license_type}')

            can_choose_workers = available_license.canChooseWorkers()
            available_workers = available_license.getWorkers()
            if LICENSE_TYPE == license_type:
                print(f'Candidate License Source Found.')

                # Claim our desired number of workers
                if can_choose_workers:
                    available_license.acquire(worker_config)
                else:
                    available_license.acquire()

                print(f'Acquired {license_type} from [{license_source.getType()}] {license_source.getLocation()}')

                # And return the licensed engine after the first matching license is claimed
                return engine

    # No matching license was found, so return None
    return None


def main(licensed_engine):
    """
    This would be the main work for the application.  This implementation just celebrates the fact we get here.
    :param licensed_engine: The fully licensed nuix.engine.Engine instance.
    :return: Nothing
    """
    nuix_license = licensed_engine.getLicence()
    if nuix_license is not None:
        print(f'Successfully acquired a license: {nuix_license.getShortName()} ({nuix_license.getWorkers()}): '
              f'{nuix_license.getDescription()}')


if __name__ == '__main__':
    """
    Begin licensing the Engine and get working if running from the Command Line.  If this file is imported as a module
    it will not start any work, buts is methods and objects would be available to outside callers.
    """
    GlobalContainerFactory = autoclass('nuix.engine.GlobalContainerFactory')
    Collectors = autoclass('java.util.stream.Collectors')
    global_container = GlobalContainerFactory.newContainer()
    try:
        nuix_engine = get_engine(NUIX_USER, USER_DATA_DIR, global_container)

        try:
            nuix_engine = claim_license(nuix_engine)
            main(nuix_engine)

        finally:
            nuix_engine.close()
    finally:
        global_container.close()

