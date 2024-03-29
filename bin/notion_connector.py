from bin.helper_functions import *
from bin.jira_connector import *
from time import sleep
from tqdm import tqdm

_existing_sprint_pages = None
_existing_sprint_pages_by_page_id = None

def get_already_migrated_entries(notion_client, database_id, issue_list = None, convert_to_ispis_strings=True):

    # If issue_list == -1, return an empty list 
    if issue_list == -1:
        return []

    # Retrieve existing pages in the Notion database
    all_entries = []
    start_cursor = None
    amount_pages = 100
    result = None

    issue_ispis = convert_jira_issues_into_ispis(issue_list)
    filter = get_notion_ISPI_filter(issue_ispis)

    
    if issue_list:
        print_info("Detecting existing entries of the list of given ISPIS: " + ", ".join(issue_ispis))
    else:
        print_info("Detecting existing entries.")

    
    while True:

        result = notion_client.databases.query(database_id=database_id, start_cursor=start_cursor, filter=filter, page_size=amount_pages)

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

    amount_retries = 0
    successfully_searched_notion = False

    # Get all databases for the url provided
    while not successfully_searched_notion:
        try: 
            database_result = notion_client.search(filter={"property": "object", "value": "database"}, url=database_url).get("results")
            successfully_searched_notion = True

        except Exception:
            print_info("Failed to search Notion. Retrying. Amount of retries so far: " + str(amount_retries))
            sleep(1)
            amount_retries += 1

        # Get all names of found databases
    database_names = [result["title"][0]["plain_text"] for result in database_result]

    # Get Index of correct name
    try:
        database_index = database_names.index(database_name)
    except ValueError as e:
        print_warning("Database with name '" + database_name + "' not found in available databases, accessable by Notion API key: " + str(database_names))
        exit()

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
        # Update properties: "Status", "Sprint" property
        issue_status = get_jira_status_name(jira_issue)
        issue_sprints = get_jira_sprints(jira_issue)

        sprint_pages = [{"id": get_or_create_sprint_page(notion_client, sprints_database_id, sprint)["id"]} for sprint in issue_sprints] if issue_sprints else []

        while not successfully_updated:
            try:
                if get_jira_assigned_person(jira_issue):
                    notion_client.pages.update(
                        notion_page_id,
                        properties={
                            "Status": {"status": {"name": issue_status}},
                            "Sprint": {"relation": sprint_pages},
                            "Assignee": {"select": {"name": get_jira_assigned_person(jira_issue)}}
                        }
                    )
                else:
                    notion_client.pages.update(
                        notion_page_id,
                        properties={
                            "Status": {"status": {"name": issue_status}},
                            "Sprint": {"relation": sprint_pages},
                        }
                    )
                successfully_updated = True

            except Exception as e:
                print(e)
                print_info("Not able to update page. Retrying")
                retry_counter += 1
                print_info("Times retried updating: " + str(retry_counter))
                sleep(1)


    else:
        print_info(f'No Notion page found for Jira issue: {jira_issue.key}')      


def get_updated_notion_issues(notion_client, jira_issues, notion_issues, sprints_database_id):

    global NOTION_TEXT_FIELD_MAX_CHARS
    updated_notion_issues = []

    notion_issues_dict = {issue['properties']['ISPI']['rich_text'][0]['text']['content'] : issue for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0}

    for jira_issue in tqdm(jira_issues, "Compute changed Issues ..."):

        notion_issue = notion_issues_dict[jira_issue.key]

        # Check for changed status
        jira_status = jira_issue.fields.status.name
        notion_status = notion_issue['properties']['Status']['status']['name'] if "Status" in notion_issue['properties'] else None

        # No difference shall be made between "Resolved" in JIRA and "Closed" in Notion -> A "Closed" issue in Notion will always be set as "Resolved" in JIRA
        if jira_status != notion_status and not (jira_status == "Resolved" and notion_status == "Closed"):
            updated_notion_issues.append(notion_issue)
            continue

        # Check for changed sprints    
        jira_sprints = get_jira_sprints(jira_issue)
        jira_sprints = jira_sprints if jira_sprints else []

        sprint_pages_notion = notion_issue['properties']['Sprint']['relation']
        sprint_pages_names_notion = [get_or_create_sprint_page(notion_client, sprints_database_id, None, sprint_page_notion["id"])['properties']['Name']['title'][0]['plain_text'] for sprint_page_notion in sprint_pages_notion]

        if jira_sprints != sprint_pages_names_notion:
            updated_notion_issues.append(notion_issue)
            continue

        # Check for changed team
        jira_assigned_team = map_team_identifer_to_string(get_jira_assigned_team(jira_issue))
        notion_assigned_team = notion_issue['properties']['Team']['select']['name'] if notion_issue['properties']['Team']['select'] else None
        
        if jira_assigned_team != notion_assigned_team:
            updated_notion_issues.append(notion_issue)
            continue

        # Check for changed assignment
        jira_assigned_person = get_jira_assigned_person(jira_issue)
        notion_assigned_person = notion_issue['properties']['Assignee']['select']['name'] if notion_issue['properties']['Assignee']['select'] else None

        # A change in the assigne person shall only be relevant, if the status of the issue is not "resolved" or "closed"
        if notion_assigned_person and jira_assigned_person != notion_assigned_person and (jira_status != "Resolved" or notion_status != "Closed"):
            updated_notion_issues.append(notion_issue)
            continue

    return updated_notion_issues


def get_updated_jira_issues(notion_client, jira_issues, notion_issues, sprints_database_id):

    global NOTION_TEXT_FIELD_MAX_CHARS
    
    updated_jira_issues = []

    notion_issues_dict = {issue['properties']['ISPI']['rich_text'][0]['text']['content'] : issue for issue in notion_issues if len(issue['properties']['ISPI']['rich_text']) > 0}

    for jira_issue in jira_issues:

        notion_issue = notion_issues_dict[jira_issue.key]

        # Check for changed status
        jira_status = get_jira_status_name(jira_issue)
        notion_status = notion_issue['properties']['Status']['status']['name'] if "Status" in notion_issue['properties'] else None

        if jira_status != notion_status and not (jira_status.lower() == "resolved" and notion_status.lower() == "closed"):
            updated_jira_issues.append(jira_issue)
            continue

        # Check for changed sprints    
        jira_sprints = get_jira_sprints(jira_issue)
        jira_sprints = jira_sprints if jira_sprints else []

        sprint_pages_notion = notion_issue['properties']['Sprint']['relation']
        sprint_pages_names_notion = [get_or_create_sprint_page(notion_client, sprints_database_id, None, sprint_page_notion["id"])['properties']['Name']['title'][0]['plain_text'] for sprint_page_notion in sprint_pages_notion]

        if jira_sprints != sprint_pages_names_notion:
            updated_jira_issues.append(jira_issue)
            continue

        # Check for changed team
        jira_assigned_team = map_team_identifer_to_string(get_jira_assigned_team(jira_issue))
        notion_assigned_team = notion_issue['properties']['Team']['select']['name'] if notion_issue['properties']['Team']['select'] else None
        
        if jira_assigned_team != notion_assigned_team:
            updated_jira_issues.append(jira_issue)
            continue

        # Check for changed assignment
        jira_assigned_person = get_jira_assigned_person(jira_issue)
        notion_assigned_person = notion_issue['properties']['Assignee']['select']['name'] if notion_issue['properties']['Assignee']['select'] else None

        if jira_assigned_person != notion_assigned_person:
            updated_jira_issues.append(jira_issue)
            continue

    return updated_jira_issues
