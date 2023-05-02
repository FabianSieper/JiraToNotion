from bin.config import *
from bin.helper_functions import *
from bin.notion_connector import *
from bin.jira_connector import *

# --------------------------------------------
# Dynamic variables
# --------------------------------------------
amount_issues_skipped = 0
_existing_epic_pages = None

def get_issue_list_from_notion_epics(jira, notion_client, epic_database_id):

    print_info("Fetching Issues for already created Notion Epics")

    existing_epic_pages = get_notion_pages(notion_client, epic_database_id)

    epic_list = [page["properties"]["ISPI"]["rich_text"][0]["text"]["content"] for page in existing_epic_pages if len(page["properties"]["ISPI"]["rich_text"]) > 0]
    print_info("Successfully fetched list of existing Notion epic pages")

    issue_list = get_jira_issue_list_from_ispis(jira, epic_list, isEpic=True, convert_to_ispi_strings=False)
    print_info("Successfully fetched list of existing Notion issue pages based on Notion epics")

    return issue_list


def add_notion_entries_loop(jira, notion, database_id, sprints_database_id, epic_database_id, issues, existing_ispis):
    
    global amount_issues_skipped

    # Add JIRA issues to the Notion database if not already present
    for issue in tqdm(issues, "Writing issues to notion database ..."):

        issue_ispi, issue_summary, issue_status, issue_description, issue_url, issue_priority, issue_sprints, epic_ispi, issue_assignee = get_jira_issue_information(issue)

        # Skip issues
        if isIssueSkipped(issue, existing_ispis):
            amount_issues_skipped += 1
            continue

        # Get or create sprint pages in the sprints database, but only if Sprint name has prefix 
        sprint_pages = []
        if issue_sprints:
            sprint_pages = [{"id": get_or_create_sprint_page(notion, sprints_database_id, sprint)["id"]} for sprint in issue_sprints]
            
        # Get or create epic pages in the epics database
        epic_page = None
        if epic_ispi:
            epic_page = [{"id": get_or_create_epic_page(jira, notion, epic_database_id, epic_ispi)["id"]}]

        # Create page in notion database
        new_page = {
            "Summary": {"title": [{"text": {"content": issue_summary}}]},
            "Status": {"status": {"name": issue_status}},
            "URL": {"url": issue_url},
            "Description": {"rich_text": [{"text": {"content": issue_description if issue_description else ""}}]},
            "ISPI": {"rich_text": [{"text": {"content": issue_ispi}}]},
            "Priority": {"select": {"name": str(issue_priority)}},
            "Sprint": {"relation": sprint_pages},
            "Epic": {"relation": epic_page if epic_page and epic_page[0]["id"] else []},
            "Zeitlicher Fortschritt": {"number": 0},
            "Team": {"select": {"name": get_jira_assigned_team(issue)}}
        }

        notion.pages.create(parent={"database_id": database_id}, properties=new_page).get("id")

    return amount_issues_skipped


def add_missing_notion_issues(jira_client, notion_client, issue_database_id, epic_database_id, sprints_database_id, notion_issues):

    issue_list = get_issue_list_from_notion_epics(jira_client, notion_client, epic_database_id)
    existing_ispis = [issue['properties']['ISPI']['rich_text'][0]['text']['content'] for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0]

    add_notion_entries_loop(jira_client, notion_client, issue_database_id, sprints_database_id, epic_database_id, issue_list, existing_ispis)


def get_jira_issues(jira, notion_client, epic_database_id):

    epics, issues, update, _, _ = parse_cmd_args()
    issue_list = []

    # If a list of epic-ispis is given
    if epics:
        issue_list = get_jira_issue_list_from_ispis(jira, epics, isEpic=True, convert_to_ispi_strings=False)

    # If a list of issue-ispis is given
    elif issues:
        issue_list = get_jira_issue_list_from_ispis(jira, issues, isEpic=False, convert_to_ispi_strings=False)

    # If missing issues for the given notion epics shall be added
    elif update:
        issue_list = get_issue_list_from_notion_epics(jira, notion_client, epic_database_id)

    else:
        print_info("No valid  task was recognized.")

    return issue_list    


def get_or_create_epic_page(jira, notion_client, epic_database_id, epic_ispi):

    global _existing_epic_pages

    if not _existing_epic_pages:

        print_info("Fetching existing epic pages in Notion")

        existing_epic_pages_list = get_notion_pages(notion_client, epic_database_id)

        _existing_epic_pages = {epic_page['properties']['ISPI']['rich_text'][0]['text']['content'] : epic_page for epic_page in existing_epic_pages_list if len(epic_page['properties']['ISPI']['rich_text']) > 0}

    if epic_ispi in _existing_epic_pages:
        return _existing_epic_pages[epic_ispi]
    else:

        print_info("Creating new epic page in Notion")
        epic = get_jira_issue_list_from_ispis(jira, epic_ispi, isEpic=True, convert_to_ispi_strings=False)[0]

        _, summary, _, description, url, _, _, _, _ = get_jira_issue_information(epic)

        new_epic_page = {
            "Name": {"title": [{"text": {"content": summary}}]},
            "URL": {"url": url},
            "ISPI": {"rich_text": [{"text": {"content": epic_ispi}}]},
            "Description": {"rich_text": [{"text": {"content": description if description else ""}}]},
        }

        new_epic_page = create_notion_page(notion_client, epic_database_id, new_epic_page)
        _existing_epic_pages[epic_ispi] = new_epic_page
        return new_epic_page


def update_existing_notion_issues(notion_client, jira_client, database_id, sprints_database_id, notion_issues):


    notion_issues_ispis = [issue['properties']['ISPI']['rich_text'][0]['text']['content'] for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0]

    # Get corresponding jira issues
    print_info("Fetching all Jira Issues for found Notion Issues")
    jira_issues = get_jira_issue_list_from_ispis(jira_client, notion_issues_ispis, convert_to_ispi_strings=False)

    # Get list of jira issues, which have been updated
    updated_jira_issues = get_updated_jira_issues(notion_client, jira_issues, notion_issues, sprints_database_id)
    print_info("Found outdated Notion issues: " + str(len(updated_jira_issues)))

    # Update Notion issues, where the paramter of interest is differnt
    for jira_issue in tqdm(updated_jira_issues, "Updating existing Notion issues ... "):
        update_notion_issues(notion_client, database_id, sprints_database_id, jira_issue)

