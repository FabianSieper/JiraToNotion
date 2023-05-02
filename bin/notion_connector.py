from bin.helper_functions import *
from bin.jira_connector import *
from tqdm import tqdm


_existing_sprint_pages = None
_existing_sprint_pages_by_page_id = None

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

        print_info("Fetching existing jira pages in Notion: " + str(len(all_entries)))

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

    

def get_or_create_sprint_page(notion_client, sprints_database_id, sprint_name = None, notion_sprint_page_id = None):

    global _existing_sprint_pages
    global _existing_sprint_pages_by_page_id

    if sprint_name == None and notion_sprint_page_id == None:
        print_info("No identifyer for sprint Notion page was given.")
        return None

    # Fetch all sprint pages, if not already done
    if not _existing_sprint_pages:

        print_info("Fetching already migrated sprint pages")
        existing_sprint_pages_list = get_already_migrated_entries(notion_client, sprints_database_id, convert_to_ispis_strings = False)

        _existing_sprint_pages = {sprint_page['properties']['Name']['title'][0]['plain_text'] : sprint_page for sprint_page in existing_sprint_pages_list if len(sprint_page['properties']['Name']['title'][0]) > 0}
        _existing_sprint_pages_by_page_id = {sprint_page['id']: sprint_page for sprint_page in existing_sprint_pages_list}

    # Check if pages exists
    if sprint_name and sprint_name in _existing_sprint_pages:
        return _existing_sprint_pages[sprint_name]
    elif notion_sprint_page_id and notion_sprint_page_id in _existing_sprint_pages_by_page_id:
        return _existing_sprint_pages_by_page_id[notion_sprint_page_id]
    else:
        # Create a new sprint page
        new_sprint_page = {
            "Name": {"title": [{"text": {"content": sprint_name}}]}
        }

        new_sprint_page = create_notion_page(notion_client, sprints_database_id, new_sprint_page)
        _existing_sprint_pages[sprint_name] = new_sprint_page
        _existing_sprint_pages_by_page_id[new_sprint_page["id"]] = new_sprint_page

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

        if "next_cursor" in results and results["next_cursor"]:
            start_cursor = results["next_cursor"]
        else:
            break

    return all_pages


def update_notion_issues(notion_client, database_id, sprints_database_id, jira_issue):

    notion_page_id = get_notion_page_id_by_jira_issue(notion_client, database_id, jira_issue)

    retry_counter = 0
    successfully_updated = False

    if notion_page_id:
        # Update properties: "Status", "Sprint", "Description" property
        _, _, issue_status, issue_description, _, _, issue_sprints, _, _ = get_jira_issue_information(jira_issue)
        sprint_pages = [{"id": get_or_create_sprint_page(notion_client, sprints_database_id, sprint)["id"]} for sprint in issue_sprints] if issue_sprints else []

        while not successfully_updated:
            try:
                notion_client.pages.update(
                    notion_page_id,
                    properties={
                        "Status": {"status": {"name": issue_status}},
                        "Sprint": {"relation": sprint_pages},
                        "Description": {"rich_text": [{"text": {"content": issue_description if issue_description else ""}}]},
                        "Team": {"select": {"name": get_jira_assigned_team(jira_issue)}}

                    }
                )
                successfully_updated = True

            except Exception as e:
                print_info("Not able to update page. Retrying")
                retry_counter += 1
                print_info("Times retried updating: " + str(retry_counter))

    else:
        print_info(f'No Notion page found for Jira issue: {jira_issue.key}')      


def get_updated_jira_issues(notion_client, jira_issues, notion_issues, sprints_database_id):

    updated_jira_issues = []

    notion_issues_dict = {issue['properties']['ISPI']['rich_text'][0]['text']['content'] : issue for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0}

    for jira_issue in jira_issues:

        notion_issue = notion_issues_dict[jira_issue.key]

        # Check for changed status
        jira_status = jira_issue.fields.status.name
        notion_status = notion_issue['properties']['Status']['status']['name'] if "Status" in notion_issue['properties'] else None

        if jira_status != notion_status:
            updated_jira_issues.append(jira_issue)
            continue

        # Check for changed sprints    
        jira_sprints = get_jira_issue_information(jira_issue)[6]
        jira_sprints = jira_sprints if jira_sprints else []

        sprint_pages_notion = notion_issue['properties']['Sprint']['relation']
        sprint_pages_names_notion = [get_or_create_sprint_page(notion_client, sprints_database_id, None, sprint_page_notion["id"])['properties']['Name']['title'][0]['plain_text'] for sprint_page_notion in sprint_pages_notion]

        if jira_sprints != sprint_pages_names_notion:
            updated_jira_issues.append(jira_issue)
            continue

        # Check for changed description
        jira_description = get_jira_issue_information(jira_issue)[3]
        capped_jira_description = jira_description[0:NOTION_TEXT_FIELD_MAX_CHARS] if jira_description else ""
        notion_description = notion_issue['properties']['Description']['rich_text'][0]['plain_text'] if notion_issue['properties']['Description']['rich_text'] else ""

        if capped_jira_description != notion_description:
            updated_jira_issues.append(jira_issue)
            continue

        # Check for changed team
        jira_assigned_team = map_team_identifer_to_string(get_jira_assigned_team(jira_issue))
        notion_assigned_team = notion_issue['properties']['Team']['select']['name'] if notion_issue['properties']['Team']['select'] else None
        
        if jira_assigned_team != notion_assigned_team:
            updated_jira_issues.append(jira_issue)
            continue

    return updated_jira_issues
