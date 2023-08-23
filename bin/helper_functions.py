import argparse
from typing import List, Tuple
from bin.config import *

def print_info(text):

    print("[INFO] -", text)

def print_warning(text, wait_for_user_input=False):

    print("[WARNING] -", text)

    if wait_for_user_input:
        input("Press any key to continue ...")

def throw_error(text):

    print("[ERROR] -", text)
    exit()

def map_team_identifer_to_string(team_identifier):
    global KOBRA_IDENTIFIER

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

def get_jira_status_name(issue):

    return issue.fields.status.name

def get_jira_summary(issue):

    return issue.fields.summary

def get_jira_acceptance_criterias(issue):

    return issue.fields.customfield_11100

def get_jira_status_name(issue):

    status = issue.fields.status.name

    if status.lower() == "resolved":
        return "Closed"
    
    return issue.fields.status.name

def get_jira_url(issue):

    return JIRA_SERVER_URL + "/browse/" + get_jira_ispi(issue)

def get_jira_priority(issue):

    return issue.fields.priority

def get_jira_sprints(issue):

    return [s.split('name=')[1].split(',')[0] for s in issue.fields.customfield_10000] if issue.fields.customfield_10000 else None

def get_jira_epic_ispi(issue):

    return issue.fields.customfield_10001



def isIssueSkipped(issue, existing_titles):

    issue_ispi = get_jira_ispi(issue)
    issue_summary = get_jira_summary(issue)

    # Skip if issue was already sent to notion
    if issue_ispi in existing_titles:
        print_info("Skipping JIRA issue, as the issue already exists in the Notion db: " + issue_summary)
        return True
    
    # DONT skip by default
    return False

def print_issue_information(issue, advanced = False):

    issue_ispi          = get_jira_ispi(issue)
    issue_summary       = get_jira_summary(issue)
    issue_status        = get_jira_status_name(issue)
    issue_url           = get_jira_url(issue)
    issue_priority      = get_jira_priority(issue)
    issue_sprints       = get_jira_sprints(issue)
    issue_epic          = get_jira_epic_ispi(issue)
    issue_assignee      = get_jira_assigned_person(issue)

    print("ISPI:", issue_ispi)
    print("Issue summary:", issue_summary)
    print("Issue URL:", issue_url)
    print("Sprint:", issue_sprints)
    print("Priority:", issue_priority)
    print("Status:", issue_status)
    print("Epic:", issue_epic)
    print("Assignee:", issue_assignee)

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

    global KOBRA_IDENTIFIER
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


def update_jira_issues_message(updated_notion_issues, jira_issues):

    jira_issues_dict = {get_jira_ispi(jira_issue): jira_issue for jira_issue in jira_issues}

    print_info("The following Issues will be updated in Jira: ")
    for notion_issue in updated_notion_issues:

        notion_assignee = get_assignee_from_notion_issue(notion_issue)
        notion_status = get_status_from_notion_issue(notion_issue)
        notion_ispi = get_ispi_from_notion_issue(notion_issue)
        notion_summary = get_summary_from_notion_issue(notion_issue)

        jira_status = get_jira_status_name(jira_issues_dict[notion_ispi])
        jira_assignee = get_jira_assigned_person(jira_issues_dict[notion_ispi])

        print_info("")
        print_info("Updating " + notion_ispi + ": " + notion_summary)
        print_info("\tStatus:")
        print_info("\t\tWas:\t\t" + jira_status)
        print_info("\t\tWill be:\t" + notion_status)
        print_info("\tAssignee:")
        print_info("\t\tWas:\t\t" + jira_assignee if jira_assignee else "\t\tWas:\t\tNone")
        print_info("\t\tWill be:\t" + notion_assignee if notion_assignee != "Unassigned" else "\t\tWill be:\t" + jira_assignee)

    continue_answer = input("Do you want to continue? Enter 'Yes' to continue ...\n")
    if continue_answer != "Yes":
        print_info("NOT updating Jira Issues!")
        return False
    
    return True