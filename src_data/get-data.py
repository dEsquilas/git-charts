import argparse
import json
import os
import re
import subprocess
import sys

from dateutil.parser import parse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-f', '--folder', type=str, required=True, help='The folder to process')
    parser.add_argument('-d', '--date', type=str, required=True, help='The date to process')
    parser.add_argument('-o', '--output', type=str, required=True, help='The output file')

    args = parser.parse_args()
    return args.folder, args.date, args.output

def get_data(dir, date):
    # get the value of the data
    data = subprocess.run(["git", "-C", dir, "log", "--since=" + date, "--numstat", "--format=%H %an %ad", "--date=short"], capture_output=True, text=True)
    return data.stdout

folder, date, output = parse_arguments()

try:
    parse(date)
except ValueError:
    print("Date is not valid")
    exit(1)

if not os.path.isdir(folder):
    print("Folder does not exist")
    exit(1)

data = get_data(folder, date).splitlines()
log = {}
newData = {}

commit_pattern = re.compile(r'^([0-9a-f]{40})\s+(.+?)\s+(\d{4}-\d{2}-\d{2})$')
file_change_pattern = re.compile(r'^(\d+|-)\s+(\d+|-)\s+(.+)$')
old_date = ""

for line in data:
    commit_match = commit_pattern.match(line)
    if commit_match:
        data_splitted = line.split()
        current_date = data_splitted[-1]
        commit_hash = data_splitted[0]
        data_splitted.remove(current_date)
        data_splitted.remove(commit_hash)
        current_author = " ".join(data_splitted)

        if old_date != current_date and old_date != "":
            log[current_date] = newData
            newData = {}

        old_date = current_date

        if current_author not in newData:
            newData[current_author] = {}
        if current_date not in newData[current_author]:
            newData[current_author][current_date] = {"added": 0, "removed": 0}
    else:
        file_change_match = file_change_pattern.match(line)
        if file_change_match:
            added = file_change_match.group(1)
            removed = file_change_match.group(2)
            if added == "-":
                added = 0
            else:
                added = int(added)
            if removed == "-":
                removed = 0
            else:
                removed = int(removed)
            newData[current_author][current_date]["added"] += added
            newData[current_author][current_date]["removed"] += removed

log[current_date] = newData

with open(output, "w") as f:
    json.dump(log, f)

print("Data saved to output.json")