import argparse
import json
from pathlib import Path
import os
import pandas as pd
from datetime import datetime

parser = argparse.ArgumentParser()

parser.add_argument("-c", "--coco",
                    help="""Directory name""")

parser.add_argument("-o", "--out_dir",
                    help="""Output directory""")

parser.add_argument("-p", "--project_name",
                    help="""Project name""")

parser.add_argument("-v", "--volume_name",
                    help="""Volume name""")


def coco2df(coco):
    '''
    Fit a coco instance into a flat pandas DataFrame.
    '''
    classes_df = pd.DataFrame(coco['categories'])
    classes_df['name'] = classes_df['name'].str.strip()
    classes_df = classes_df.rename(columns={"id": "category_id"})
    images_df = pd.DataFrame(coco['images'])
    images_df.rename(columns={"id": "image_id"}, inplace=True)
    coco_df = pd.DataFrame(coco['annotations'])\
                    .merge(classes_df, on="category_id", how='left')\
                    .merge(images_df, on="image_id", how='left')

    return coco_df




if __name__ == '__main__':
    args = parser.parse_args()

    coco_file = args.coco
    output_dir = args.out_dir
    project_name = args.project_name
    volume_name = args.volume_name

    with open(coco_file, 'r') as f:
        coco = json.load(f)

    output_path = os.path.join(output_dir, project_name, volume_name)
    Path(output_path).mkdir(parents=True, exist_ok=True)

    df = coco2df(coco)

    df['annotation_id'] = df.index + 1

    label_tree = {}

    label_tree_path = './biigle/label_trees.json'

    with open(label_tree_path, 'r') as f:
        label_tree = json.load(f)

    labels = label_tree[0].get('labels')

    labels_map = {label['name']: label['id'] for label in labels}

    df['label_id'] = df['name'].map(labels_map)

    df.to_clipboard()

    users_path = './biigle/users.json'

    with open(users_path, 'r') as f:
        users = json.load(f)

    df['user_id'] = users[0]['id']

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    df['created_at'] = now
    df['updated_at'] = now

    df.to_clipboard()


