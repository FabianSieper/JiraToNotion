from bin.helper_functions import *
from bin.jira_connector import *
from tqdm import tqdm


_existing_sprint_pages = None

def get_already_migrated_entries(notion_client, database_id, filter=None, convert_to_ispis_strings=True):

    # Retrieve existing pages in the Notion database
    all_entries = []
    start_cursor = None
    page_size = 100
    result = None

    print_info("Detecting existing entries.")

    while True:

        if filter:
            result = notion_client.databases.query(database_id=database_id, filter=filter, start_cursor=start_cursor, page_size=page_size)
        else:
            result = notion_client.databases.query(database_id=database_id, start_cursor=start_cursor, page_size=page_size)

        all_entries.extend(result["results"])

        print_info("Fetching existing jira issues in Notion: " + str(len(all_entries)))

        if "next_cursor" in result and result["next_cursor"]:
            start_cursor = result["next_cursor"]
        else:
            break

    if convert_to_ispis_strings:
        # Convert to ISPI-strings as a set
        return {entry["properties"]["ISPI"]["rich_text"][0]["text"]["content"] for entry in all_entries if len(entry["properties"]["ISPI"]["rich_text"]) > 0}
    else:
        # Convert all_entries to a set
        return all_entries

    

def get_or_create_sprint_page(notion_client, sprints_database_id, sprint_name):

    global _existing_sprint_pages

    if "CaVORS" in sprint_name:
        sprint_name = sprint_name.replace("CaVORS-", "CV-")

    # Fetch all sprint pages, if not already done
    if not _existing_sprint_pages:

        print_info("Fetching already migrated sprint pages")
        existing_sprint_pages_list = get_already_migrated_entries(notion_client, sprints_database_id, convert_to_ispis_strings = False)

        _existing_sprint_pages = {sprint_page['properties']['Name']['title'][0]['plain_text'] : sprint_page for sprint_page in existing_sprint_pages_list if len(sprint_page['properties']['Name']['title'][0]) > 0}
    
    # Check if pages exists
    if sprint_name in _existing_sprint_pages:
        return _existing_sprint_pages[sprint_name]
    else:
        # Create a new sprint page
        new_sprint_page = {
            "Name": {"title": [{"text": {"content": sprint_name}}]}
        }

        new_sprint_page = create_notion_page(notion_client, sprints_database_id, new_sprint_page)
        _existing_sprint_pages[sprint_name] = new_sprint_page
        return new_sprint_page


def create_notion_page(notion_client, database_id, page):

        return notion_client.pages.create(parent={"database_id": database_id}, properties=page)


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


def get_notion_page_id_by_jira_issue(notion_client, database_id, jira_issue):
    # Replace "Issue_key" with the name of the property where you store the Jira issue key in Notion
    jql_query = {
        "property": "ISPI",
        "title": {
            "equals": jira_issue.key
        }
    }
    results = get_notion_pages(notion_client, database_id, jql_query)
    return results[0]["id"] if results else None


def get_notion_pages(notion_client, database_id, filter_query=None):
    all_pages = []
    start_cursor = None
    page_size = 100

    while True:
        if filter_query:
            results = notion_client.databases.query(database_id=database_id, filter=filter_query, start_cursor=start_cursor, page_size=page_size)
        else:
            results = notion_client.databases.query(database_id=database_id, start_cursor=start_cursor, page_size=page_size)

        all_pages.extend(results.get("results"))

        print_info("Fetched jira issues: " + str(len(all_pages)))

        if "next_cursor" in results and results["next_cursor"]:
            start_cursor = results["next_cursor"]
        else:
            break

    return all_pages


def update_notion_issue_status(notion_client, database_id, jira_issue):

    notion_page_id = get_notion_page_id_by_jira_issue(notion_client, database_id, jira_issue)

    if notion_page_id:
        # Update the "Status" property of the Notion page with the Jira issue status
        issue_status = jira_issue.fields.status.name
        notion_client.pages.update(
            notion_page_id,
            properties={
                "Status": {"status": {"name": issue_status}}
            }
        )
    else:
        print_info(f'No Notion page found for Jira issue: {jira_issue.key}')      


def get_updated_jira_issues(jira_issues, notion_issues):

    updated_jira_issues = []

    notion_issues_dict = {issue['properties']['ISPI']['rich_text'][0]['text']['content'] : issue for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0}

    for jira_issue in jira_issues:

        notion_issue = notion_issues_dict[jira_issue.key]

        jira_status = jira_issue.fields.status.name
        notion_status = notion_issue['properties']['Status']['status']['name'] if "Status" in notion_issue['properties'] else None

        if jira_status != notion_status:
            updated_jira_issues.append(jira_issue)

    return updated_jira_issues
