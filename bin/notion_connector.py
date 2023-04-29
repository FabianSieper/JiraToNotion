from bin.helper_functions import *
from bin.jira_connector import *
from tqdm import tqdm

def get_already_migrated_entries(notion, database_id):
    # Retrieve existing pages in the Notion database
    all_entries = []
    start_cursor = None
    page_size = 100

    print_info("Detecting existing entries.")

    while True:
        result = notion.databases.query(database_id=database_id, start_cursor=start_cursor, page_size=page_size)
        all_entries.extend(result["results"])

        print_info("Fetching existing jira issues in Notion: " + str(len(all_entries)))
        if "next_cursor" in result and result["next_cursor"]:
            start_cursor = result["next_cursor"]
        else:
            break

    # Create list of JIRA issues, which were already added to notion
    already_contained_issue_ispis = {entry["properties"]["ISPI"]["rich_text"][0]["text"]["content"] for entry in all_entries if len(entry["properties"]["ISPI"]["rich_text"]) > 0}

    return already_contained_issue_ispis


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



def get_notion_page_id_by_jira_issue(notion_client, database_id, jira_issue):
    # Replace "Issue_key" with the name of the property where you store the Jira issue key in Notion
    jql_query = {
        "property": "ISPI",
        "title": {
            "equals": jira_issue.key
        }
    }
    response = notion_client.databases.query(database_id=database_id, filter={"and": [jql_query]})
    results = response.get("results")
    return results[0]["id"] if results else None

def update_notion_issue_status(notion_client, database_id, jira_issue):
    # Find the corresponding Notion page by Jira issue key
    issue_ispi = get_jira_issue_information(jira_issue)[0]

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
        print(f'No Notion page found for Jira issue: {jira_issue.key}')      



def update_all_notion_issues(notion_client, database_id, jira_issues):

    for jira_issue in tqdm(jira_issues, "Updating issues ... "):
        update_notion_issue_status(notion_client, database_id, jira_issue)

