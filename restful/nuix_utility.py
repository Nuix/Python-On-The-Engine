"""
This module contains some re-usable methods used for common tasks with the RESTful interface.
"""
import os
import json
import time

from nuix_api import NuixRestApi as nuix
from nuix_api import ContentTypes
from rest_base import put, get, post, delete

with open("config.json") as config_file:
    config = json.load(config_file)


def check_ready(headers):
    """
    Make a simple health check on the server to ensure it is running
    :param headers:
    :return: True if the server is running and returns success on a health check.  False if the return from the
             server is unexpected, or there was an error connecting to it.
    """
    try:
        status_code, response_body = get(nuix.health_url(), headers)
        return status_code == 200
    except:
        return False


def login(headers):
    """
    Logs in to the REST server and stored the authentication token in the headers.  The username and password
    are expected to be stored in environment variables "NUIX_USER" and "NUIX_PASSWORD" respectively.  If an error
    occurs the nuix-auth-token header will not be set.

    :param headers: json dictionary of headers.  This will have the nuix-auth-token added to it
    :return: True if logged in correctly, False otherwise.
    """
    usr = os.environ['nuix_user']
    pw = os.environ['nuix_password']

    data = json.dumps({
        "username": usr,
        "password": pw,
        "licenseShortName": config["license"]["type"],
        "workers": config["license"]["workers"]
    })

    headers['Content-Type'] = ContentTypes.V1
    headers['Accept'] = ContentTypes.V1

    try:
        status_code, response_body = put(nuix.login_url(), headers, data)
        if status_code == 201:
            auth_token = response_body["authToken"]
            headers["nuix-auth-token"] = auth_token
            return True
        else:
            print(f"Unexpected return status code when Logging In: {status_code} [{response_body}]")
            return False
    finally:
        # Reset headers to default
        headers['Content-Type'] = ContentTypes.JSON
        headers['Accept'] = ContentTypes.JSON


def logout(headers):
    """
    Log the user out of the apllication, releasing its license.
    :param headers: json dictionary of headers to send.  This should include the nuix-auth-token
    :return: A tuple: [0] True/False on the success of logging out, [1] The response from the server.
    """
    usr = os.environ['nuix_user']
    status_code, response_body = delete(nuix.logout_url(usr), headers, None)
    return status_code == 200, response_body


def close_case(case, headers):
    """
    Close the specified case

    :param case: GUID of the case to close
    :param headers: Headers to send with the request
    :return: A tuple.  [0] Boolean for successful request
                       [1] The response body or error if the close failed.
    """
    data = json.dumps({
        "caseId": case
    })
    status_code, response = post(nuix.case_close_url(case), headers, data)
    return status_code == 200, response


def wait_for_async_done(function, headers):
    """
    Wait for the function to get to the done state.  This function will block the collar until the Async Function
    returns <code>done = true</code>.  This method will return true if the Async Function finished successfully, as
    defined by <code>hasSuccessfullyCompleted = true</code>.  This will return false otherwise - including if the
    export was interrupted by some error or exception.

    :param function: The json response body from an Async Function call.  It should have the "functionKey" property for
                    the function to wait on.
    :param headers: The request headers.
    :return: true if the function completed successfully, or false if it was unsuccessful for some reason.
    """
    function_key = function["functionKey"]

    done = False
    success = False
    while not done:
        status_code, status_body = get(nuix.async_status_url(function_key), headers)

        if status_code == 200:
            function_status = status_body
            complete = function_status["hasSuccessfullyCompleted"]
            progress = function_status["progress"]
            total = function_status["total"]
            percent_complete = function_status["percentComplete"]

            # Note for the export, this doesn't seem to produce good progress...
            print(f"{percent_complete}% [complete={complete},({progress}/{total})]")

            done = bool(function_status["done"])
            success = bool(complete)
        else:
            print(f"Unexpected return status code when waiting for Async Function: {status_code} [{status_body}]")
            done = True
            success = False
        if not done:
            time.sleep(10)

    return success


def find_caseid_for_name(case_name, headers):
    """
    Search for a case by name and get its GUID.

    :param case_name: Name of the case to find
    :param headers: Headers to use for the request
    :return: A tuple.  [0] is a boolean marking success.  No case found will return False.
                       [1] is the case's GUID as a String, None if the case wasn't found, or the message from the error.
    """
    status_code, case_list = get(nuix.case_list_url(), headers)
    if status_code == 200:
        for case in case_list:
            print(f"Looking at {case}")
            if case_name == case["name"]:
                return True, case["caseId"]
    else:
        print(f"Unexpected status code from getting case: {status_code} [{case_list}]")
        return False, case_list

    # No case of the given name
    return False, None


def paged_search_for_items(case, search_query, field_list, page_number, page_size, headers):
    """
    Search in a large case, returning one page of results.  This example just returns the items' GUID.  A page is a
    list of the item results.  The size of the list will be from 0 to page_size.

    Example use:  To get items 0 - 99 from the case:
    <code>items = paged_search_for_items(case_id, "*", 1, 100)</code>

    To get items 100 - 199 from the case:
    <code>items = paged_search_for_items(case_id, "*", 2, 100)</code>

    :param case: GUID for the case to search in
    :param search_query: The query for items to find
    :param field_list: List of the names of metadata fields to retrieve for each item
    :param page_number: Which page of data to return, starting with page 1 (not 0 based)
    :param page_size: Number of items to return per page
    :param headers: Headers to include in the request
    :return: A tuple.  [0] A boolean indicating success.
                       [1] If successful, a list of up to page_size item GUIDS in the order they are returned from the
                           search.  If the search succeeded with 0 results the list will be empty.  If the search failed
                            with an error then this return will be the message returned for the error.
    """
    data = json.dumps({
        "caseId": case,
        "query": search_query,
        "fieldList": field_list,
        "startIndex": (page_number - 1) * page_size,
        "numberOfRecordsRequested": page_size
    })

    item_ids = []
    status_code, search = post(nuix.case_search_url(case), headers, data)
    if status_code == 200:
        for found_item in search['resultList']:
            item_ids.append(found_item["guid"])

        return True, item_ids
    else:
        print(f"Unexpected status code when searching: {status_code} [{search}")
        return False, search
