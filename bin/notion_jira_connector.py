from bin.config import *
from bin.helper_functions import *
from bin.notion_connector import *
from bin.jira_connector import *

from tqdm import tqdm
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
    
    skipped_issues = []

    if issues == -1:
        print_info("No pages were added to Notion.")
        return
    
    # Add JIRA issues to the Notion database if not already present
    for issue in tqdm(issues, "Writing issues to notion database ..."):

        issue_ispi          = get_jira_ispi(issue)
        issue_summary       = get_jira_summary(issue)
        issue_status        = get_jira_status_name(issue)
        issue_url           = get_jira_url(issue)
        issue_priority      = get_jira_priority(issue)
        issue_sprints       = get_jira_sprints(issue)
        epic_ispi           = get_jira_epic_ispi(issue)

        # Skip issues
        if isIssueSkipped(issue, existing_ispis):
            skipped_issues.append(issue)
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
            "ISPI": {"rich_text": [{"text": {"content": issue_ispi}}]},
            "Priority": {"select": {"name": str(issue_priority)}},
            "Sprint": {"relation": sprint_pages},
            "Epic": {"relation": epic_page if epic_page and epic_page[0]["id"] else []}
        }

        notion.pages.create(parent={"database_id": database_id}, properties=new_page).get("id")

    return skipped_issues


def add_missing_notion_issues(jira_client, notion_client, issue_database_id, epic_database_id, sprints_database_id, notion_issues):

    issue_list = get_issue_list_from_notion_epics(jira_client, notion_client, epic_database_id)
    existing_ispis = [issue['properties']['ISPI']['rich_text'][0]['text']['content'] for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0]

    add_notion_entries_loop(jira_client, notion_client, issue_database_id, sprints_database_id, epic_database_id, issue_list, existing_ispis)


def get_jira_issues(jira, notion_client, epic_database_id):

    epics, issues, update_notion, _, _, _ = parse_cmd_args()
    issue_list = []

    # If a list of epic-ispis is given
    if epics:
        issue_list = get_jira_issue_list_from_ispis(jira, epics, isEpic=True, convert_to_ispi_strings=False)

    # If a list of issue-ispis is given
    elif issues:
        issue_list = get_jira_issue_list_from_ispis(jira, issues, isEpic=False, convert_to_ispi_strings=False)

    # If missing issues for the given notion epics shall be added
    elif update_notion:
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

        summary = get_jira_summary(epic)
        url = get_jira_url(epic)

        new_epic_page = {
            "Name": {"title": [{"text": {"content": summary}}]},
            "URL": {"url": url},
            "ISPI": {"rich_text": [{"text": {"content": epic_ispi}}]}
        }

        new_epic_page = create_notion_page(notion_client, epic_database_id, new_epic_page)
        _existing_epic_pages[epic_ispi] = new_epic_page
        return new_epic_page


def update_jira_issues(notion_client, jira_client, sprints_database_id, notion_issues):

    notion_issues_ispis = [issue['properties']['ISPI']['rich_text'][0]['text']['content'] for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0]

    # Get corresponding jira issues
    print_info("Fetching all Jira Issues for found Notion Issues")
    jira_issues = get_jira_issue_list_from_ispis(jira_client, notion_issues_ispis, convert_to_ispi_strings=False)

    if jira_issues == -1:
        print_info("No jira issues found fo the given filter")
        return
    
    # Get list of Notion Issues, which have been updated
    updated_notion_issues = get_updated_notion_issues(notion_client, jira_issues, notion_issues, sprints_database_id)

    if len(updated_notion_issues) == 0:
        print_info("No outdated Jira issues were found.")
        return
    
    print_info("Found outdated Jira issues: " + str(len(updated_notion_issues)))

    is_update = update_jira_issues_message(updated_notion_issues, jira_issues)

    if not is_update:
        return

    amount_skipped_issues = 0
    skipped_issues = []

    if len(updated_notion_issues) == 0:
        print_info("Not outdates Jira Issues found")
        return
    
    jira_issues_dict = {get_jira_ispi(jira_issue): jira_issue for jira_issue in jira_issues}

    # Update Jira issues
    for notion_issue in tqdm(updated_notion_issues, "Updating existing Jira issues ... "):

        notion_assignee = get_assignee_from_notion_issue(notion_issue)
        notion_status = get_status_from_notion_issue(notion_issue)
        notion_ispi = get_ispi_from_notion_issue(notion_issue)

        jira_status = get_jira_status_name(jira_issues_dict[notion_ispi])
        jira_assignee = get_jira_assigned_person(jira_issues_dict[notion_ispi])

        ispi = get_ispi_from_notion_issue(notion_issue)

        result = update_jira_issue_status_and_assignee(jira_client, 
                                                       jira_issues_dict[ispi], 
                                                       notion_status, 
                                                       notion_assignee,
                                                       is_update_jira_status = jira_status != notion_status,
                                                       is_update_jira_assignee = notion_assignee and jira_assignee != notion_assignee )

    if result == -1:
        amount_skipped_issues += 1
        skipped_issues.append(ispi)

    print_info("Successfully updated Jira Issues")
    print_info("Amount of Jira Issues skipped: " + str(amount_skipped_issues) + "/" + str(len(updated_notion_issues)))
    if len(skipped_issues) > 0:
        print_info("Skipped issues: " + ", ".join(skipped_issues))


def update_existing_notion_issues(notion_client, jira_client, database_id, sprints_database_id, notion_issues):

    notion_issues_ispis = [issue['properties']['ISPI']['rich_text'][0]['text']['content'] for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0]

    # Get corresponding jira issues
    print_info("Fetching all Jira Issues for found Notion Issues")
    jira_issues = get_jira_issue_list_from_ispis(jira_client, notion_issues_ispis, convert_to_ispi_strings=False)

    # Get list of jira issues, which have been updated
    updated_jira_issues = get_updated_jira_issues(notion_client, jira_issues, notion_issues, sprints_database_id)
    print_info("Found outdated Notion issues: " + str(len(updated_jira_issues)))

    # Update Notion issues
    for jira_issue in tqdm(updated_jira_issues, "Updating existing Notion issues ... "):
        update_notion_issues(notion_client, database_id, sprints_database_id, jira_issue)

