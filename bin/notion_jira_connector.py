from bin.config import *
from bin.helper_functions import *
from bin.notion_connector import *
from bin.jira_connector import *


def get_issue_list_from_notion_epics(jira, notion_client, epic_database_id):

    print_info("Fetching Issues for already created Notion Epics")

    existing_epic_pages = get_notion_pages(notion_client, epic_database_id)

    epic_list = [page["properties"]["ISPI"]["rich_text"][0]["text"]["content"] for page in existing_epic_pages if len(page["properties"]["ISPI"]["rich_text"]) > 0]
    print_info("Successfully fetched list of existing notion epic pages")

    issue_list = get_issue_list_from_ispis(jira, epic_list, isEpic=True, convert_to_ispi_strings=False)
    print_info("Successfully fetched list of existing notion issue pages")

    return issue_list



def get_jira_issues(jira, notion_client, database_id, epic_database_id):

    epics, issues, update_issues = parse_cmd_args()
    issue_list = []

    # If a list of epic-ispis is given
    if epics:
        issue_list = get_issue_list_from_ispis(jira, epics, isEpic=True, convert_to_ispi_strings=False)

    # If a list of issue-ispis is given
    elif issues:
        issue_list = get_issue_list_from_ispis(jira, issues, isEpic=False, convert_to_ispi_strings=False)

    # If migrated notion issues shall be updated
    elif update_issues:
        migrated_issue_ispis = get_already_migrated_entries(notion_client, database_id)
        issue_list = get_issue_list_from_ispis(jira, migrated_issue_ispis, isEpic=False, convert_to_ispi_strings=False)

    # If missing issues for the given notion epics shall be added
    else:
        issue_list = get_issue_list_from_notion_epics(jira, notion_client, epic_database_id)

    return issue_list    



def get_or_create_epic_page(jira, notion_client, epic_database_id, epic_ispi):

    print_info("Creating or fetching epic entry for epic " + epic_ispi)

    # Retrieve the epics database
    epic_database_id = get_database_id(notion_client, EPICS_DATABASE_URL, EPICS_DATABASE_NAME)

    jql_query={
            "property": "ISPI",
            "title": {
                "equals": epic_ispi,
            },
        }
    existing_epic_pages = get_notion_pages(notion_client, epic_database_id, jql_query)

    if existing_epic_pages:
        return existing_epic_pages[0]["id"]
    else:
        # Create a new sprint page
        
        epic = get_issue_list_from_ispis(jira, epic_ispi, isEpic=True, convert_to_ispi_strings=False)[0]

        _, summary, _, description, url, _, _, _, _ = get_jira_issue_information(epic)

        new_epic_page = {
            "Name": {"title": [{"text": {"content": summary}}]},
            "URL": {"url": url},
            "ISPI": {"rich_text": [{"text": {"content": epic_ispi}}]},
            "Description": {"rich_text": [{"text": {"content": description if description else ""}}]},
        }

        return create_notion_page(notion_client, epic_database_id, new_epic_page)
