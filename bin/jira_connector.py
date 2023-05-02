from bin.helper_functions import *
from bin.notion_connector import *
from bin.config import *

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
