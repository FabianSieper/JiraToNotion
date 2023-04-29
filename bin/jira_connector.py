from bin.helper_functions import print_info
from bin.notion_connector import *
from bin.config import *

def get_issues_for_epics(jira, epics):
    epic_conditions = ' OR '.join([f'"Epic Link" = {epic}' for epic in epics])
    jql_query = f'({epic_conditions})'

    all_issues = []
    start_at = 0
    max_results = 100

    while True:
        issues = jira.search_issues(jql_query, startAt=start_at, maxResults=max_results)
        if not issues:
            break

        all_issues.extend(issues)
        start_at += max_results

        print_info("Fetched jira issues for epics: " + str(len(all_issues)))

    return all_issues



def get_issue_list_from_epics(jira, epics):

    issue_list = get_issues_for_epics(jira, epics)

    # Convert each jira issue to a ISPI- String
    issue_list = [str(issue) for issue in issue_list]

    return issue_list


def get_jira_issues_for_jql_query(jira, jql_query):

    return jira.search_issues(jql_query, maxResults=AMOUNT_JIRA_RESULTS)


def get_jira_issues_for_ispis(jira, issue_ispis):

    jql_query = create_jira_jql_query(issue_ispis)

    # Get JIRA issues using the specified filter
    issues = get_jira_issues_for_jql_query(jira, jql_query)

    return issues