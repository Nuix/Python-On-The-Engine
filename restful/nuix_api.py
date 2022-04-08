import json


class ContentTypes:
    """
    Stores common Content Types used by the RESTful service to determine what version of different
    endpoints to deliver.
    """
    V1 = "application/vnd.nuix.v1+json"
    V2 = "application/vnd.nuix.v2+json"
    JSON = "application/json"


class NuixRestApi:
    """
    Basic wrapper around some of the API endpoints such that the parameter substitutions can be done through a
    method call in a central spot rather than at the calling point.
    """
    with open("config.json") as config_file:
        config = json.load(config_file)['rest']

    service = "nuix-restful-service/svc"

    login_path = "authenticatedUsers/login"
    logout_path = "authenticatedUsers/{username}"
    case_list_path = "inventory/digest"
    case_count_path = "cases/{case_id}/count"
    case_search_path = "v2/cases/{case_id}/search"
    case_export_path = "cases/{case_id}/export"
    case_tags_list_path = "cases/{case_id}/tags"
    case_tags_modify_path = "cases/{case_id}/itemTags"
    case_tags_edit_path = "cases/{case_id}/tags"
    case_close_path = "cases/{case_id}/close"
    async_status_path = "v1/asyncFunctions/{function_key}"
    health_path = "system/health"

    @staticmethod
    def login_url():
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{NuixRestApi.login_path}"

    @staticmethod
    def logout_url(username):
        logout_path = NuixRestApi.logout_path.format(username=username)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{logout_path}"

    @staticmethod
    def case_list_url():
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{NuixRestApi.case_list_path}"

    @staticmethod
    def case_count_url(case_id):
        case_count_path = NuixRestApi.case_count_path.format(case_id=case_id)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{case_count_path}"

    @staticmethod
    def case_search_url(case_id):
        case_search_path = NuixRestApi.case_search_path.format(case_id=case_id)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{case_search_path}"

    @staticmethod
    def case_export_url(case_id):
        case_export_path = NuixRestApi.case_export_path.format(case_id=case_id)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{case_export_path}"

    @staticmethod
    def case_tags_list_url(case_id):
        case_tags_path = NuixRestApi.case_tags_list_path.format(case_id=case_id)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{case_tags_path}"

    @staticmethod
    def case_tags_modify_url(case_id):
        case_tags_path = NuixRestApi.case_tags_modify_path.format(case_id=case_id)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{case_tags_path}"

    @staticmethod
    def case_tags_edit_url(case_id):
        case_tags_path = NuixRestApi.case_tags_edit_path.format(case_id=case_id)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{case_tags_path}"

    @staticmethod
    def case_close_url(case_id):
        case_close_path = NuixRestApi.case_close_path.format(case_id=case_id)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{case_close_path}"

    @staticmethod
    def async_status_url(function_key):
        async_status_path = NuixRestApi.async_status_path.format(function_key=function_key)
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{async_status_path}"

    @staticmethod
    def health_url():
        return f"{NuixRestApi.config['host']}:{NuixRestApi.config['port']}/{NuixRestApi.service}/{NuixRestApi.health_path}"
