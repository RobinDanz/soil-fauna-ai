import json
import csv
from datetime import datetime
from pathlib import Path
import shutil

now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

biigle_fieldnames = [
    'id',
    'name',
    'parent_id',
    'color',
    'label_tree_id',
    'source_id'
]

output = Path(__file__).parent.parent.joinpath('out', 'label_trees')
output.mkdir(parents=True, exist_ok=True)

output_labels = output.joinpath('labels.csv')
output_label_tree = output.joinpath('label_tree.json')

if __name__ == '__main__':
    label_tree_name = 'QBS'

    label_tree = {
        "id": 1,
        "name": label_tree_name,
        "description": None,
        "created_at": now,
        "updated_at": now,
        "uuid": "c93bfedd-8ab0-40e2-a404-28470a6e80c5",
        "version": None
    }

    lines = []

    with open('/Users/robin/DEV/soil-fauna-ai/data/label_trees/newQBSlabel4.csv', 'r') as input_file:
        reader = csv.DictReader(input_file, delimiter=';', fieldnames=biigle_fieldnames)
        header = next(reader)
        for row in reader:
            lines.append(row)

    with open(output_labels, 'w') as output_file:
        writer = csv.DictWriter(output_file, delimiter=',', fieldnames=biigle_fieldnames)
        writer.writeheader()
        for row in lines:
            row['label_tree_id'] = label_tree['id']
            row['source_id'] = None
            row['color'] = str.lower(row['color'])
            writer.writerow(row)

    with open(output_label_tree, 'w') as f:
        json.dump(label_tree, f)

    shutil.make_archive('label_tree', 'zip', root_dir=output)
        


