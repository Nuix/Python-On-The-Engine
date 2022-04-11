"""
Author: Steven Luke (steven.luke@nuix.com)
Date: 2022.04.06
Nuix RESTful Service: 9.6.8
Python Version 3.9

Summary: Example application using the RESTful API through Python.  It exports files in pages so the process can be
chunked.

Description:
Uses a Paged Search to create tags for chunks of items to export, and can be used to export those items.  This
module can be run in two modes:

1: First, run the application with no command line.  This will iterate over the case and tag items for export.
2: Then run the application with date and page number to identify what group of items to export to actually
   export those items

This application uses a JSON file to configure things like the size of a page, the format of the tag to make,
and the directory where items will be exported to.  Items will be exported with their original names when possible
and containers will be unpacked.

To mark items for export run:
`> python restful.paged_export.py`
This will mark items with tags as follows (if run on April 6, 2022):
export
  2022.04.06
    pg1
    pg2
    pg3
    ...

To export the items run:
`> python restful.paged_export.py <year>.<month>.<day> <page num>`
Where <year> is the four digit year, <month> is the two-digit month, and <day> is the two-digit day of the date the
export tags were created, and <page num> is the page number to export.  For example:
`> python restful.paged_export.py 2022.04.06 3`
Would export all items with the following tag:
export
  2022.04.06
    pg3

The tags are persistent and can be removed from the items using the restful.remove_export_tags application.
"""
import datetime
import math
import sys
import json

from rest_base import put, post
from nuix_api import NuixRestApi as nuix
from nuix_api import ContentTypes
import nuix_utility as ute

with open("config.json") as config_file:
    config = json.load(config_file)['rest']

headers = {
    "Content-Type": ContentTypes.JSON,
    "Accept": ContentTypes.JSON
}


def count_of_items(case, search_query):
    """
    Get the count of items that match the search query.

    :param case: GUID of the case to search
    :param search_query: Query string for items to count
    :return: A tuple. [0] Boolean for success of the operation
                      [1] The count of items found or the message of any error received
    """
    data = json.dumps({
        "query": search_query
    })
    status_code, count_body = post(nuix.case_count_url(case), headers, data)
    if status_code == 200:
        return True, count_body["count"]
    else:
        return False, count_body


def tag_items(case, items_to_tag, tag):
    """
    Add the given tag to all items in the list.

    :param case: GUID of the case holding the items
    :param items_to_tag: List of item ids for the items to tag
    :param tag: Tag to add to the items
    :return: A tuple.  [0] A boolean with the Success of the tagging.  If any 1 item's tagging failed, this will return False
                           but tagging will continue
                       [1] A dictionary of error messages for tag operations keyed to the item GUID that had the error.
    """

    messages = {}
    success = True
    tags = [tag]
    for item_guid in items_to_tag:
        data = json.dumps({
            "tagList": tags,
            "query": f"guid:{item_guid}"
        })
        status_code, tag_results = post(nuix.case_tags_modify_url(case), headers, data)
        if status_code == 201:
            if len(tag_results["failedTags"]) > 0:
                success = False
                messages[item_guid] = f"Adding tag {tag} failed."
            # Default to not changing Success
        else:
            messages[item_guid] = tag_results
            success = False

    return success, messages


def start_export_items(case, item_queries, page_id):
    """
    Kick of the asynchronous export of items in the query.  The path to export files to is stored in the
    "EXPORT_PATH" environment variable.  The "native" file contents will be exported, containers will be unpacked and
    exported.

    :param case: GUID for the case to export from
    :param item_queries: List of queries for the items to export
    :param page_id: Page number being exported.  This is used to add a subfolder under the target path to export into.
                    For example, if the page_id is 2, this will export to a directory "export_2".
    :return: A Tuple. [0] A boolean marking the success of the request (though not necessarily of the operation, which
                          must come from asking on the status of the async function).
                      [1] The response body containing the functionKey for to monitor the export progress or the error
                          message uf there was a problem with the request.
    """

    count_to_export = count_of_items(case, item_queries[0])
    print(f'Export Count: {count_to_export}')

    folder_id = config["export"]["subfolder"].format(id=page_id)
    data = json.dumps({
        "id": folder_id,
        "path": config["export"]["path"],
        "export_type": "ITEM",
        "productTypes": ["NATIVE"],
        "parallelProcessingSettings": {"workerCount": config["export"]["workers"]},
        "queries": item_queries
    })
    print(f'Export: {data}')

    status_code, function = put(nuix.case_export_url(case), headers, data)
    if status_code == 200:
        return True, function
    else:
        print(f"Unexpected status code from exporting: {status_code} [{function}]")
        return False, function


def tag_for_export(case, items_per_page):
    """
    Add a tag to items to mark them for export.  Tags will be made per page in the format export|<data>|page<n>, with
    <n> being the page number.
    :param case: The case where items should be tagged
    :param items_per_page: The number of items per page being tagged.
    :return: Nothing
    """
    current_time = datetime.datetime.now()

    items_to_export = "*"
    # Get count of items to export
    ok, count = count_of_items(case_id, items_to_export)
    if not ok:
        print(f"There was an error getting the count of items. {count}")
        exit(5)

    if 0 == count:
        print(f"No items to export.")
        exit(0)  # This is not an error.

    # Do a paged search tagging each page
    number_of_pages = math.ceil(count / items_per_page)
    for current_page in range(1, number_of_pages + 1):
        # Find the items in the current page
        ok, list_of_items = ute.paged_search_for_items(case, items_to_export, ["guid"], current_page, items_per_page, headers)
        if not ok:
            print(f"Search failed with message: {list_of_items}")
            exit(3)

        # Create the tag for the current page
        tag_format = config["export"]["tag_format"]
        export_tag = tag_format.format(year=current_time.year, month=current_time.month, day=current_time.day, page=current_page)

        # Tag the items
        ok, problems = tag_items(case_id, list_of_items, export_tag)
        if not ok:
            print(f"Tagging files for export ran into the following problems:")
            for item_guid in problems.keys():
                print(f"    {item_guid}: {problems[item_guid]}")

            print(f"Continuing with export, but not all items may be exported.")


def export_tagged_items(case, tag_date, tag_page):
    """
    Export items given the provided date and page.
    :param case: The GUID for the case to export from
    :param tag_date: The date of the export marking, in the format YYYY.MM.DD
    :param tag_page: The page number to export
    :return: Nothing
    """

    # Generate the tag for searching which items to export
    yr, mo, da = tag_date.split(".")
    tag_format = config["export"]["tag_format"].replace('|', r'\|')
    tag = tag_format.format(year=yr, month=mo, day=da, page=tag_page)

    # Create the query for the items with that tag
    tag_search = config["export"]["tag_query"].format(export_tag=tag)
    export_queries = [tag_search]

    # Export the tagged items
    current_page = int(tag_page)
    ok, export_function = start_export_items(case_id, export_queries, current_page)
    if not ok:
        print(f"Starting the export failed: {export_function}")
        exit(4)

    # Wait for the export to complete
    export_success = ute.wait_for_async_done(export_function, headers)
    print(f"Done [success={export_success}]")


if __name__ == "__main__":
    ok = ute.check_ready(headers)
    if not ok:
        print('Server is not ready')
        exit(9)

    ok = ute.login(headers)
    if not ok:
        print("Failed to Log in.")
        exit(1)

    case_of_interest = config['case_name']
    ok, case_id = ute.find_caseid_for_name(case_of_interest, headers)
    if not ok:
        print(f"The case \"{case_of_interest}\" was not found.  Reason: {case_id}")
        exit(2)

    try:
        if len(sys.argv) == 1:
            # No arguments == label items for export

            # Change this to adjust the number of items to adjust per page #
            page_size = config['search']['page_size']
            tag_for_export(case_id, page_size)

        else:
            page = None
            date = None
            errors = []
            for arg in range(1, len(sys.argv)):
                arg_pair = sys.argv[arg].split(":")
                if len(arg_pair) < 2:
                    errors.append("Argument not formatted correctly.  Expected <key>:<value>, and got {arg}")
                elif "date" in arg_pair[0]:
                    date = arg_pair[1]
                elif "page" in arg_pair[0]:
                    page = arg_pair[1]

            if len(errors) != 0:
                print("Incorrect arguments for exporting:")
                for error in errors:
                    print(f"    {error}")
                print("To export do python.exe Nuix_Paged_Export.py date:<date> page:<page>")
                exit(6)

            if page is None or date is None:
                print("To export, you need to enter the date and page to export.")
                print("To mark items for export: python.exe Nuix_Paged_Export.py")
                print("To export: python.exe Nuix_Paged_Export.py date:<date> page:<page>")
                exit(7)

            export_tagged_items(case_id, date, page)
    finally:
        try:
            ute.close_case(case_id, headers)
        finally:
            ute.logout(headers)
