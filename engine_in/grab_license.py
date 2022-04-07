import os


def initialize_environment():
    nuix_engine_path = r'C:\Projects\nuix-engine'

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
from jnius import autoclass, PythonJavaClass, java_method

NUIX_USER = 'Inspector Gadget'
USER_DATA_DIR = r'C:\Projects\RestData'

LICENSE_TYPE = 'enterprise-workstation'
LICENSE_SOURCE_TYPE = 'cloud-server'
LICENSE_SOURCE_LOCATION = 'https://licence-api.nuix.com'
WORKER_COUNT = 4


class PCertificateTrustCallback(PythonJavaClass):
    __javainterfaces__ = ['nuix/engine/CredentialsCallback']

    @java_method('(Lnuix/engine/CredentialsCallbackInfo;)V')
    def execute(self, info):
        print('Credentials Callback Called')
        info.setUsername(os.environ['nuix_user'])
        info.setPassword(os.environ['nuix_password'])


class PLicenseSourcePredicate(PythonJavaClass):
    __javainterfaces__ = ['java/util/function/Predicate']

    @java_method('(Ljava/lang/Object;)Z')
    def test(self, licence_source):
        print('License Test Called')
        return LICENSE_SOURCE_LOCATION == licence_source.getLocation()


def dict_to_immutablemap(items_dict):
    ImmutableMap = autoclass('com.google.common.collect.ImmutableMap')
    map_builder = ImmutableMap.builder()
    for item in items_dict.items():
        map_builder.put(item[0], item[1])
    return map_builder.build()


def get_engine(user, user_dir, container):
    configs = dict_to_immutablemap({'user': user, 'userDataDirs': user_dir})
    engine = container.newEngine(configs)

    return engine


def claim_license(engine):
    engine.whenAskedForCredentials(PCertificateTrustCallback())

    license_config = dict_to_immutablemap({'sources': [LICENSE_SOURCE_TYPE]})
    worker_config = dict_to_immutablemap({'workerCount': WORKER_COUNT})
    found_licenses = engine.getLicensor().findLicenceSourcesStream(license_config) \
        .filter(PLicenseSourcePredicate()) \
        .collect(Collectors.toList())

    for license_source in found_licenses:
        print(f'{license_source.getType()}: {license_source.getLocation()}')

        for available_license in license_source.findAvailableLicences():
            license_type = available_license.getShortName()
            print(f'Inspecting License Type {license_type}')

            can_choose_workers = available_license.canChooseWorkers()
            available_workers = available_license.getWorkers()
            if LICENSE_TYPE == license_type:
                print(f'Candidate License Source Found.')

                if can_choose_workers:
                    available_license.acquire(worker_config)
                else:
                    available_license.acquire()

                print(f'Acquired {license_type} from [{license_source.getType()}] {license_source.getLocation()}')

                return engine


def main(licensed_engine):
    nuix_license = licensed_engine.getLicence()
    if nuix_license is not None:
        print(f'Successfully acquired a license: {nuix_license.getShortName()} ({nuix_license.getWorkers()}): '
              f'{nuix_license.getDescription()}')


if __name__ == '__main__':
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

