#!/bin/bash

echo "Select an option:"
echo "1. --update -> Update Notion issues and import missing Issues, based on imported Epics"
echo "2. --issues -> Import Notion Issues by providing a list of Issue ISPI's"
echo "3. --epics -> Import Notion Issues by providing a list of Epic ISPI's. Issues linked to Epics will be imported"
echo "4. --sprints -> Import Notion Issues by providing a list of sprints. Issues linked to at least one of those sprints will eb imported"
read -p "Enter the option number: " option

case $option in
    1)
        read -p "Enter sprint names. You also can enter none. (space-separated): " sprints
        python3 main.py --update --sprints $sprints
        ;;
    2)
        read -p "Enter the issue IDs (space-separated): " issues
        python3 main.py --issues $issues
        ;;
    3)
        read -p "Enter the epic IDs (space-separated): " epics
        read -p "Enter sprint names. You also can enter none. (space-separated): " sprints
        python3 main.py --epics $epics --sprints $sprints
        ;;
    3)
        read -p "Enter sprint names. (space-separated): " sprints
        python3 main.py --sprints $sprints
        ;;
    *)
        echo "Invalid option. Exiting..."
        exit 1
        ;;
esac
