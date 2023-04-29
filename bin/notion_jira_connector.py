from bin.config import *
from bin.helper_functions import *
from bin.notion_connector import *
from bin.jira_connector import *

def get_issue_list_from_notion_epics(jira, notion_client):

    print_info("Fetching Issues for already created Notion Epics")

    # Retrieve the epic database
    epic_database_id = get_database_id(notion_client, EPICS_DATABASE_URL, EPICS_DATABASE_NAME)

    # Get all epics
    existing_epic_pages = notion_client.databases.query(
        database_id=epic_database_id
    ).get("results")

    epic_list = [page["properties"]["ISPI"]["rich_text"][0]["text"]["content"] for page in existing_epic_pages if len(page["properties"]["ISPI"]["rich_text"]) > 0]
    print_info("Successfully fetched list of existing notion epic pages")

    issue_list = get_issue_list_from_epics(jira, epic_list)
    print_info("Successfully fetched list of existing notion issue pages")

    return issue_list



def get_issue_list(jira, notion_client, database_id):

    epics, issues, update_issues = parse_cmd_args()
    issue_list = []
    if epics:
        issue_list = get_issue_list_from_epics(jira, epics)
    elif issues:
        issue_list = issues
    elif update_issues:
        migrated_issue_ispis = get_already_migrated_entries(notion_client, database_id)
        issue_list = get_jira_issues_for_ispis(jira, migrated_issue_ispis)
    else:
        issue_list = get_issue_list_from_notion_epics(jira, notion_client)

    return issue_list


def get_jira_issues(jira, notion_client, database_id):
    
    issue_list = get_issue_list(jira, notion_client, database_id)

    jql_query = create_jira_jql_query(issue_list)

    # Get JIRA issues using the specified filter
    issues = get_jira_issues_for_jql_query(jira, jql_query)

    return issues


def get_or_create_epic_page(jira, notion_client, epic_database_id, epic_ispi):

    print_info("Creating or fetching epic entry for epic " + epic_ispi)

    # Retrieve the epics database
    epic_database_id = get_database_id(notion_client, EPICS_DATABASE_URL, EPICS_DATABASE_NAME)

    # Check if the epic page already exists
    existing_epic_pages = notion_client.databases.query(
        database_id=epic_database_id,
        filter={
            "property": "ISPI",
            "title": {
                "equals": epic_ispi,
            },
        }
    ).get("results")

    if existing_epic_pages:
        return existing_epic_pages[0]["id"]
    else:
        # Create a new sprint page
        
        epic = get_jira_issues_for_ispis(epic_ispi)[0]

        _, summary, _, description, url, _, _, _, _ = get_jira_entry_information(epic)

        new_epic_page = {
            "Name": {"title": [{"text": {"content": summary}}]},
            "URL": {"url": url},
            "ISPI": {"rich_text": [{"text": {"content": epic_ispi}}]},
            "Description": {"rich_text": [{"text": {"content": description if description else ""}}]},
        }

        new_epic_page_id = notion_client.pages.create(parent={"database_id": epic_database_id}, properties=new_epic_page).get("id")
        return new_epic_page_id
