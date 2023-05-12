from bin.helper_functions import *
from bin.notion_connector import *
from bin.config import *


def get_jira_resolve_done_transition(jira_client, issue):
    possible_transitions = jira_client.transitions(issue)
    resolve_transition = [transition for transition in possible_transitions if transition["name"] == "Resolve"]
    return resolve_transition[0] if resolve_transition else None


# This function shall be used if the status which the issue shall be set to is "Closed"
def set_jira_status_to_done(jira_client, issue):

    done_transition = get_jira_resolve_done_transition(jira_client, issue)
     
    if done_transition is None:
        raise Exception(f"Error: Transition to status 'resolve' not possible.")

    # Update the status
    print_info("Transitioning status of Issue")
    jira_client.transition_issue(issue, done_transition["id"], fields={"resolution": {"name": "Done"}})


# This function shall be used if the status which the issue shall be set to is NOT "Closed"
def update_jira_issue_default(jira_client, issue, status):

    # Get the available transitions for the issue
    print_info("Gathering possible transitions")
    possible_transitions = jira_client.transitions(issue)

    # Find the transition ID for the desired status

    transition = [transition for transition in possible_transitions if transition["name"].lower() == status.lower()]

    if transition is None:
        raise Exception(f"Error: Transition to status '{status}' not found.")

    # Update the status
    print_info("Transitioning status of Issue")
    jira_client.transition_issue(issue, transition["id"])


def update_jira_assignee(jira_client, assignee_name, issue):

    # Search for the assignee using a part of their name
    print_info("Searching Jira users from name")
    users = jira_client.search_users(assignee_name)
    if not users:
        print_info("No user of name '" + assignee_name + "' could be found. Skipping change for Issue '" + issue.key + "'")
        return -1
    
    assignee = users[0]
    # There are two "Patrick Fischer" - use the correct one
    if "Patrick Fischer" in assignee_name and len(users) > 1:
        assignee.name = "qxz10vd"

    # Update the assignee
    print_info("Upding Jira Issue with assignee")
    issue.update(assignee={"name": assignee.name})


def update_jira_issue_status_and_assignee(jira_client, issue, status, assignee_name, is_update_jira_status = True, is_update_jira_assignee = True):

    try:

        if is_update_jira_assignee:

            update_jira_assignee(jira_client, assignee_name, issue)

        if is_update_jira_status:

            # If status is "Closed", some transitions have to be done first
            if status and status.lower() == "closed":
                set_jira_status_to_done(jira_client, issue)

            else:
                update_jira_issue_default(jira_client, issue, status)

        return 1
    
    except Exception as e:
        print_info("Unable to update Jira Issue for Issue '" + issue.key + "'")
        print_info(str(e))
        return -1


def get_all_jira_issues_for_query(jira, query):

    all_issues = []
    start_at = 0
    max_results = 100

    while True:
        try:
            issues = jira.search_issues(query, startAt=start_at, maxResults=max_results)
        except Exception:
            print_info("Not able to search for issue with query: " + str(query))
            print_info("Returning empty list.")
            return []
        
        if not issues:
            break

        all_issues.extend(issues)
        start_at += max_results

        print_info("Fetched jira issues for epics: " + str(len(all_issues)))

    return all_issues


def get_jira_issue_list_from_ispis(jira, ispis, isEpic = False, convert_to_ispi_strings = True):

    if isinstance(ispis, str):
        ispis = [ispis]
    if ispis and not isinstance(ispis, list):
        ispis = list(ispis)

    if isEpic:
        query = create_OR_jira_jql_query("Epic Link", ispis)
    else:
        query = create_OR_jira_jql_query("key", ispis)

    issue_list = get_all_jira_issues_for_query(jira, query)

    if convert_to_ispi_strings:
        issue_list = [str(issue) for issue in issue_list]

    return issue_list if issue_list else -1
