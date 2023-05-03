from bin.helper_functions import *
from bin.notion_connector import *
from bin.config import *

def update_jira_issue_status_and_assignee(jira_client, issue, status, assignee_name, update_jira_status = True, update_jira_assignee = True):

    try:

        if update_jira_assignee:
            # Search for the assignee using a part of their name
            print_info("Searching Jira users from name")
            users = jira_client.search_users(assignee_name)
            if not users:
                print_info("No user of name '" + assignee_name + "' could be found. Skipping change for Issue '" + issue.key + "'")
                return -1

            assignee = users[0]

            # Update the assignee
            print_info("Upding Jira Issue with assignee")
            issue.update(assignee={"name": assignee.name})

        if update_jira_status:
            transition_id = None

            # If status is "Closed", some transitions have to be done first
            if status and status.lower() == "closed":
                # Setting status "Done" by at first setting status "Resolved"
                # Get the available transitions for the issue
                print_info("Gathering possible transitions")
                transitions = jira_client.transitions(issue)

                # Find the transition ID for the desired status
                for transition in transitions:
            
                    if status and transition["name"].lower() == "resolve":
                        transition_id = transition["id"]
                        break
                                    
                if transition_id is None:
                    raise Exception(f"Error: Transition to status 'resolve' not found.")
                
                # Transitioning to "Done"
                # Get the available transitions for the issue
                print_info("Gathering possible transitions")
                transitions = jira_client.transitions(issue)

                # Find the transition ID for the desired status
                for transition in transitions:
            
                    if status and transition["name"].lower() == "done":
                        transition_id = transition["id"]
                        break
                                    
                if transition_id is None:
                    raise Exception(f"Error: Transition to status 'done' not found.")

            else:
                # Get the available transitions for the issue
                print_info("Gathering possible transitions")
                transitions = jira_client.transitions(issue)

                # Find the transition ID for the desired status
                for transition in transitions:
            
                    if status and transition["name"].lower() == status.lower():
                        transition_id = transition["id"]
                        break
                        
                if transition_id is None:
                    raise Exception(f"Error: Transition to status '{status}' not found.")

            # Update the status
            print_info("Transitioning status of Issue")
            jira_client.transition_issue(issue, transition_id)

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
