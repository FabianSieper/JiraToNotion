#!/bin/bash

echo "Select an option:"
echo "1. --update"
echo "2. --update-issues"
echo "3. --issues"
echo "4. --epics"
read -p "Enter the option number: " option

case $option in
    1)
        python3 main.py --update
        ;;
    2)
        read -p "Enter the issue IDs (space-separated): " issues
        python3 main.py --issues $issues
        ;;
    3)
        read -p "Enter the epic IDs (space-separated): " epics
        python3 main.py --epics $epics
        ;;
    *)
        echo "Invalid option. Exiting..."
        exit 1
        ;;
esac
