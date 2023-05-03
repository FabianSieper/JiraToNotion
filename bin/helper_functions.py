import argparse
from typing import List, Tuple
from bin.config import *

def print_info(text):

    print("[INFO] -", text)

def throw_error(text):

    print("[ERROR] -", text)
    exit()

def map_team_identifer_to_string(team_identifier):

    if team_identifier == KOBRA_IDENTIFIER:
        return "Kobra"
    else:
        return team_identifier
    

def get_assignee_from_notion_issue(notion_issue):

    return notion_issue["properties"]["Assignee"]["select"]["name"] if notion_issue["properties"]["Assignee"]["select"] else "Unassigned"


def get_status_from_notion_issue(notion_issue):

    return notion_issue["properties"]["Status"]["status"]["name"]


def get_summary_from_notion_issue(notion_issue):

    return notion_issue['properties']['Summary']['title'][0]['plain_text'] if notion_issue['properties']['Summary']['title'] else None


def get_ispi_from_notion_issue(notion_issue):

    return notion_issue['properties']['ISPI']['rich_text'][0]['plain_text'] if notion_issue['properties']['ISPI']['rich_text'] else None


def get_jira_ispi(issue):

    return issue.key

def get_jira_assigned_team(issue):

    issue_assigned_team = issue.fields.customfield_11200
    # Map the assigned team to useful strings
    return map_team_identifer_to_string(issue_assigned_team)


def get_jira_assigned_person(issue):

    return issue.fields.assignee.displayName if issue.fields.assignee else None

def get_jira_status(issue):

    return issue.fields.status.name



def get_jira_issue_information(issue):
    
    issue_ispi = issue.key
    issue_summary = issue.fields.summary
    issue_status = issue.fields.status.name
    issue_description = issue.fields.description 
    issue_priority = issue.fields.priority
    issue_sprints = [s.split('name=')[1].split(',')[0] for s in issue.fields.customfield_10000] if issue.fields.customfield_10000 else None
    issue_url = JIRA_SERVER_URL + "/browse/" + issue_ispi
    epic_ispi = issue.fields.customfield_10001
    issue_assignee = issue.fields.assignee.displayName if issue.fields.assignee else ""


    # Description is only allowed to be <= NOTION_TEXT_FIELD_MAX_CHARS symbols in Notion text field
    if issue_description and len(issue_description) > NOTION_TEXT_FIELD_MAX_CHARS:
        issue_description = issue_description[0:NOTION_TEXT_FIELD_MAX_CHARS]

    return issue_ispi, issue_summary, issue_status, issue_description, issue_url, issue_priority, issue_sprints, epic_ispi, issue_assignee


def isIssueSkipped(issue, existing_titles):

    issue_ispi, issue_summary, _, _, _, _, _, _, _ = get_jira_issue_information(issue)

    # Skip if issue was already sent to notion
    if issue_ispi in existing_titles:
        print_info("Skipping JIRA issue, as the issue already exists in the Notion db: " + issue_summary)
        return True
    
    # DONT skip by default
    return False

def print_issue_information(issue, advanced = False):

    issue_ispi, issue_summary, issue_status, issue_description, issue_url, issue_priority, issue_sprints, issue_epic, issue_assignee = get_jira_issue_information(issue)

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

def get_notion_sprint_filter():

    filter = None
    # Add a filter for sprints, if sprints are given
    if get_sprints():
        
        sprint_conditions = []

        for sprint in get_sprints():
            condition = {
                "property": "Sprint",
                "single_select": {
                    "equals": sprint
                }
            }
            sprint_conditions.append(condition)
        
        filter = {"or": sprint_conditions}

    return filter


def convert_jira_issues_into_ispis(issues):

    if not issues:
        return None
    
    return [issue.key for issue in issues]


def get_notion_ISPI_filter(ispis):
    
    filter = None
    # Add a filter for ISPI's, if ISPI's are given
    if ispis:
        
        ispi_conditions = []

        for sprint in ispis:
            condition = {
                "property": "ISPI",
                "title": {
                    "equals": sprint
                }
            }
            ispi_conditions.append(condition)
        
        filter = {"or": ispi_conditions}

    return filter


def create_OR_jira_jql_query(param_name, issue_keys) -> str:

    query = ""

    if issue_keys:
        if isinstance(issue_keys, str):
            issue_keys = [issue_keys]

        issue_keys_string = ",".join(issue_keys)
        query = f"\"{param_name}\" in ({issue_keys_string})"

    # If the list of Issues shall be limited to one or more sprints
    if get_sprints():
        sprint_query = "Sprint in (" + ", ".join(["'" + sprint + "'," for sprint in get_sprints()])[:-1] + ")"
        if query != "":
            query += " And " + sprint_query
        else:
            query = sprint_query

    query += " And Team = " + KOBRA_IDENTIFIER

    return query

def get_sprints():

    return parse_cmd_args()[4]

def parse_cmd_args() -> Tuple[List[str], List[str]]:
    parser = argparse.ArgumentParser(description="Check for --epic and --issue arguments")

    parser.add_argument("--epics", nargs="*", help="List of epic arguments", default=[])
    parser.add_argument("--issues", nargs="*", help="List of issue arguments", default=[])
    parser.add_argument("--update-notion", action="store_true", help="Update issues flag")
    parser.add_argument("--update-jira", action="store_true", help="Update issues flag")
    parser.add_argument("--sprints", nargs='*', default=None, help="Describe which sprints shall be updated. E.g. cavors-91 cavors-92")
                        
    args = parser.parse_args()

    epic_args = args.epics
    issue_args = args.issues
    update_notion = args.update_notion
    update_jira= args.update_jira
    sprints = args.sprints

    return epic_args, issue_args, update_notion, update_jira, sprints