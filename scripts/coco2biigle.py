import argparse
import json
from pathlib import Path
import os
import pandas as pd
from soilfauna.biigle import BiigleAPI
from dotenv import load_dotenv
import zipfile
from datetime import datetime
import shutil
import glob

load_dotenv()


DEFAULT_OUTPUT = os.path.join(Path(__file__).parent.parent, 'out', 'biigle')
BIIGLE_BASE_FILES = os.path.join(Path(__file__).parent.parent, 'soilfauna', 'biigle', 'data')

parser = argparse.ArgumentParser()

parser.add_argument("-c", "--coco",
                    help="""Directory name""")

parser.add_argument("-o", "--out_dir",
                    default=DEFAULT_OUTPUT,
                    help="""Output directory""")

parser.add_argument("-p", "--project_name",
                    default='project01',
                    help="""Project name""")

parser.add_argument("-v", "--volume_name",
                    default='volume01',
                    help="""Volume name""")

parser.add_argument('-t', '--label_tree_name')


def merge_list(x):
        res = list()
        for i in x:
            res.extend(i)
        return res

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
    label_tree_name = args.label_tree_name

    with open(coco_file, 'r') as f:
        coco = json.load(f)

    output_path = os.path.join(output_dir, project_name, volume_name)
    temp_path = os.path.join(output_dir, 'temp')
    Path(output_path).mkdir(parents=True, exist_ok=True)
    Path(temp_path).mkdir(parents=True, exist_ok=True)

    df = coco2df(coco)

    df['annotation_id'] = df.index + 1

    api = BiigleAPI()
    label_tree_file = api.download_label_tree(temp_path)
    
    with zipfile.ZipFile('/Users/robin/DEV/soil-fauna-ai/out/biigle/temp/label-tree.zip', 'r') as zip:
        zip.extractall(temp_path)

    label_tree_path = os.path.join(temp_path, 'label_trees.json')
    user_path = os.path.join(temp_path, 'users.json')

    with open(label_tree_path, 'r') as f:
        label_tree = json.load(f)

    labels = label_tree[0].get('labels')

    labels_map = {label['name']: label['id'] for label in labels}

    df['label_id'] = df['name'].map(labels_map)

    with open(user_path, 'r') as f:
        users = json.load(f)

    df['user_id'] = users[0]['id']
    df['confidence'] = 1

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    df['created_at'] = now
    df['updated_at'] = now

    image_annotation_labels_cols = [
        'annotation_id',
        'label_id', 
        'user_id',
        'confidence',
        'created_at',
        'updated_at'
    ]

    # Dump image_annotation_labels.csv
    df[image_annotation_labels_cols].to_csv(
        os.path.join(output_path, "image_annotation_labels.csv"),
        sep=",",
        index=False,
        quotechar='"',
        quoting=2
    )

    # Dump image_annotations.csv
    df['id'] = df['annotation_id']
    df['shape_id'] = 3

    df['points'] = df['segmentation'].apply(merge_list)

    select_col = [
        'id',
        'image_id', 
        'shape_id',
        'created_at',
        'updated_at',
        'points'
    ]

    df[select_col].to_csv(
        os.path.join(output_path, "image_annotations.csv"),
        sep=",",
        index=False,
        quotechar='"',
        quoting=2
    )

    # Preparing image.csv
    df['id'] = df['image_id']
    df['filename'] = df['file_name']  # Needs to be updated with biigle image id
    df['volume_id'] = 1  # Need to be fixed ?

    select_col = [
        'id',
        'filename',
        'volume_id'
    ]

    df[select_col].drop_duplicates(keep='first').to_csv(
        os.path.join(output_path, "images.csv"),
        sep=",",
        index=False
    )

    volume = [{
        "id": 1,
        "name": volume_name,
        "url": f"local://{os.path.basename(volume_name)}",
        "attrs": None,
        "media_type_name": "image"
    }]

    with open(os.path.join(output_path, 'volumes.json'), "w") as js:
        json.dump(volume, js)

    for z in glob.glob(os.path.join(BIIGLE_BASE_FILES, '*')):
        print(z)
        shutil.copy(z, os.path.join(output_path, os.path.basename(z)))

    for z in glob.glob(os.path.join(temp_path, '*.json')):
        print(z)
        shutil.copy(z, os.path.join(output_path, os.path.basename(z)))

    to_compress = [f for f in glob.glob(os.path.join(output_path, '*'))]

    with zipfile.ZipFile(f"{os.path.join(output_path)}.zip", "w") as archive:
        for file in to_compress:
            archive.write(file, os.path.basename(file))



