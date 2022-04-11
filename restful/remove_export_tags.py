"""
Author: Steven Luke (steven.luke@nuix.com)
Date: 2022.04.06
Nuix RESTful Service: 9.6.8
Python Version 3.9

Summary: Remove all the export tags from items in the current case, and delete those tags.

Description:
A side effect of the paged_export script is each item in the case will be tagged with an export|<date>|pgn tag.  Use
this script to remove those tags.  Note: this will remove ALL tags with the above format.
"""

import json
import re

from rest_base import get, put, post, patch
from nuix_api import NuixRestApi as nuix
from nuix_api import ContentTypes
from nuix_utility import login, find_caseid_for_name, close_case, logout

with open("config.json") as config_file:
    config = json.load(config_file)

headers = {
    "Content-Type": ContentTypes.JSON,
    "Accept": ContentTypes.JSON
}


def tag_list(case, tag_form):
    """
    Find all the tags with the provided format.
    :param case: The GUID for the case to search in
    :param tag_form: The tag or tag search query (regular-expression like) used to find the tags to remove
    :return: A tuple with two values: [0] is True / False on the success of the search, and [1] is a list of the tags or
             error message if the search failed.  A successful search may result in an empty list.
    """
    code, tags = get(nuix.case_tags_list_url(case), headers)
    if code == 200:
        intended_tags = []
        for tag in tags:
            match = re.match(tag_form, tag)
            if match is not None:
                intended_tags.append(tag)
        return True, intended_tags
    else:
        return False, tags


def remove_tags(case, tags, item_query):
    """
    Remove the provided tags from the items found using the provided item query.
    :param case: The GUID for the case whose items should be modified
    :param tags: The list of tags to remove from the items
    :param item_query: Nuix query string used to find the items to remove tags from
    :return: A tuple: [0] True / False on a successful request, and [1] The contents of the response from the server
    """
    data = json.dumps({
        "tagList": tags,
        "query": item_query,
        "operationType": "DELETE"
    })
    status, results = patch(nuix.case_tags_modify_url(case), headers, data)
    return status == 200, results


def delete_tags(case, tags):
    """
    Delete the tags out of the case so they don't clutter the UI.
    :param case: The GUID for the case where the tags should be deleted from
    :param tags: The list of tags to delete from the case.
    :return: A tuple: [0] True / False on the success of the request, and [1] The body of the response
    """
    data = json.dumps({
        "tagList": tags,
        "operationType": "DELETE"
    })
    status, results = patch(nuix.case_tags_edit_url(case), headers, data)
    return status == 200, results


if __name__ == "__main__":
    ok = login(headers)
    if not ok:
        print("Failed to Log in.")
        exit(1)

    case_of_interest = config["case_name"]
    ok, case_id = find_caseid_for_name(case_of_interest, headers)
    if not ok:
        print(f"The case \"{case_of_interest}\" was not found.  Reason: {case_id}")
        exit(2)

    try:
        # First find all the tags with the correct format
        tag_re = config["export"]["tag_format"].format(year="\\d{4}", month="\\d{1,2}", day="\\d{1,2}", page="\\d+")
        ok, case_tags = tag_list(case_id, tag_re)
        if not ok:
            print(f"Failed to get tag list: {case_tags}")
            exit(3)

        if len(case_tags) > 0:
            # First remove the tags from items
            for tag in case_tags:
                # Correct the tag syntax for searching, we have to escape the bar as it has special meaning in searching
                tag = tag.replace("|", "\\|")
                tag_search = f"tag:{tag}"
                ok, response = remove_tags(case_id, case_tags, tag_search)
                if not ok:
                    print(f"Failed to remove tag {tag}.  Continuing to delete others.  {response}")

            # Then remove the tags from the case
            ok, response = delete_tags(case_id, case_tags)
            if not ok:
                print(f"Failed to delete tags.  [{response}]")
    finally:
        try:
            _, response = close_case(case_id, headers)
        finally:
            _, response = logout(headers)
