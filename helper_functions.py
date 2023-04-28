import argparse
from typing import List, Tuple

from config import (
    AMOUNT_JIRA_RESULTS,
    EPICS_DATABASE_URL,
    EPICS_DATABASE_NAME,
    NOTION_TEXT_FIELD_MAX_CHARS,
    JIRA_SERVER_URL,
)

def print_info(text):

    print("[INFO] -", text)

def throw_error(text):

    print("[ERROR] -", text)
    exit()

def get_issue_information(issue):

    issue_ispi = issue.key
    issue_summary = issue.fields.summary
    issue_status = issue.fields.status.name
    issue_description = issue.fields.description 
    issue_priority = issue.fields.priority
    issue_sprints = [s.split('name=')[1].split(',')[0] for s in issue.fields.customfield_10000] if issue.fields.customfield_10000 else None
    issue_url = JIRA_SERVER_URL + "/browse/" + issue_ispi
    epic_ispi = issue.fields.customfield_10001

    # Description is only allowed to be <= NOTION_TEXT_FIELD_MAX_CHARS symbols in Notion text field
    if len(issue_description) > NOTION_TEXT_FIELD_MAX_CHARS:
        issue_description = issue_description[0:NOTION_TEXT_FIELD_MAX_CHARS]

    return issue_ispi, issue_summary, issue_status, issue_description, issue_url, issue_priority, issue_sprints, epic_ispi


def isIssueSkipped(issue, existing_titles):

    issue_ispi, issue_summary, _, _, _, _, _, _ = get_issue_information(issue)

    # Skip if issue was already sent to notion
    if issue_ispi in existing_titles:
        print_info("Skipping JIRA issue, as the issue summary already exists in the Notion db: " + issue_summary)
        return True
    
    # DONT skip by default
    return False

def print_issue_information(issue, advanced = False):

    issue_ispi, issue_summary, issue_status, issue_description, issue_url, issue_priority, issue_sprints, issue_epic = get_issue_information(issue)

    print("ISPI:", issue_ispi)
    print("Issue summary:", issue_summary)
    print("Issue URL:", issue_url)
    print("Sprint:", issue_sprints)
    print("Priority:", issue_priority)
    print("Status:", issue_status)
    print("Epic:", issue_epic)
    print("Description:", issue_description)  

    if advanced:
        for field_name, field_value in issue.fields.__dict__.items():
            print(f"{field_name}: {field_value}")

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
        
        jql_query = create_jira_jql_query(epic_ispi)
        # Get JIRA issues using the specified filter
        epic = get_jira_issues_for_jql_query(jira, jql_query)[0]

        _, issue_summary, _, _, issue_url, issue_priority, _, _ = get_issue_information(epic)

        new_epic_page = {
            "Name": {"title": [{"text": {"content": issue_summary}}]},
            "URL": {"url": issue_url},
            "Priority": {"select": {"name": str(issue_priority)}},
            "ISPI": {"rich_text": [{"text": {"content": epic_ispi}}]},



        }

        new_epic_page_id = notion_client.pages.create(parent={"database_id": epic_database_id}, properties=new_epic_page).get("id")
        return new_epic_page_id


def get_already_migrated_entries(notion, database_id, issues):

    # Retrieve existing pages in the Notion database
    database_entries = notion.databases.query(database_id=database_id)

    # Create list of JIRA issues, which were already added to notion
    print_info("Detecting possible duplicate entries.")
    already_contained_issue_ispis = {entry["properties"]["ISPI"]["rich_text"][0]["text"]["content"] for entry in database_entries["results"]}

    return already_contained_issue_ispis


def get_issues_for_epic(jira, epic):

    jql_query = f'"Epic Link" = {epic}'
    return jira.search_issues(jql_query)

def get_issue_list_from_epics(jira, epics):

    issue_list = [issue for single_epic in epics for issue in get_issues_for_epic(jira, single_epic)]

    # Convert each jira issue to a ISPI- String
    issue_list = [str(issue) for issue in issue_list]

    return issue_list


def get_issue_list_from_notion_epics(jira, notion_client):

    print_info("Fetching Issues for already created Notion Epics")

    # Retrieve the epic database
    epic_database_id = get_database_id(notion_client, EPICS_DATABASE_URL, EPICS_DATABASE_NAME)

    # Get all epics
    existing_epic_pages = notion_client.databases.query(
        database_id=epic_database_id
    ).get("results")

    epic_list = [page["properties"]["ISPI"]["rich_text"][0]["text"]["content"] for page in existing_epic_pages if len(page["properties"]["ISPI"]["rich_text"]) > 0]

    issue_list = get_issue_list_from_epics(jira, epic_list)

    return issue_list
    


def get_issue_list(jira, notion_client):

    epics, issues = parse_cmd_args()
    issue_list = []
    if epics:
        issue_list = get_issue_list_from_epics(jira, epics)
    elif issues:
        issue_list = issues
    else:
        issue_list = get_issue_list_from_notion_epics(jira, notion_client)

    return issue_list


def create_jira_jql_query(issue_keys) -> str:
    if isinstance(issue_keys, str):
        issue_keys = [issue_keys]

    query = " OR ".join(f"key = {key}" for key in issue_keys)
    return query


def get_jira_issues_for_jql_query(jira, jql_query):

    return jira.search_issues(jql_query, maxResults=AMOUNT_JIRA_RESULTS)

def get_jira_issues(jira, notion_client):
    
    issue_list = get_issue_list(jira, notion_client)

    jql_query = create_jira_jql_query(issue_list)

    # Get JIRA issues using the specified filter
    issues = get_jira_issues_for_jql_query(jira, jql_query)

    return issues

def get_or_create_sprint_page(notion_client, sprints_database_id, sprint_name):

    print_info("Creating or fetching sprint entry for sprint name " + sprint_name)

    if "CaVORS" in sprint_name:
        sprint_name = sprint_name.replace("CaVORS-", "CV-")

    # Check if the sprint page already exists
    existing_sprint_pages = notion_client.databases.query(
        database_id=sprints_database_id,
        filter={
            "property": "Name",
            "title": {
                "equals": sprint_name,
            },
        }
    ).get("results")

    if existing_sprint_pages:
        return existing_sprint_pages[0]["id"]
    else:
        # Create a new sprint page
        new_sprint_page = {
            "Name": {"title": [{"text": {"content": sprint_name}}]}
        }
        new_sprint_page_id = notion_client.pages.create(parent={"database_id": sprints_database_id}, properties=new_sprint_page).get("id")
        return new_sprint_page_id


def get_database_id(notion_client, database_url, database_name):
    temp_database_id = ""

    # Get all databases for the url provided
    database_result = notion_client.search(filter={"property": "object", "value": "database"}, url=database_url).get("results")

    # Get all names of found databases
    database_names = [result["title"][0]["plain_text"] for result in database_result]

    # Get Index of correct name
    database_index = database_names.index(database_name)

    if database_index == -1:
        print("[ERROR] - Could not find databse for name", database_name)
    
    temp_database_id = database_result[database_index]["id"]
    
    return temp_database_id

def parse_cmd_args() -> Tuple[List[str], List[str]]:
    parser = argparse.ArgumentParser(description="Check for --epic and --issue arguments")

    parser.add_argument("--epics", nargs="*", help="List of epic arguments", default=[])
    parser.add_argument("--issues", nargs="*", help="List of issue arguments", default=[])

    args = parser.parse_args()

    epic_args = args.epics
    issue_args = args.issues

    return epic_args, issue_args