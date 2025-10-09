import os
import re
from dotenv import load_dotenv

from googleapiclient.discovery import build
from google.oauth2 import service_account

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

FILENAME_REGEX = r'(?P<batch>[\da-zA-Z-_]*)_(?P<position>r\d{1,2}c\d{1,2}).(?P<ext>jpg|png)'

ALL_IMAGES_FOLDER = os.getenv('ALL_IMAGES_FOLDER')
SELECTED_IMAGES_FOLDER = os.getenv('SELECTED_IMAGES_FOLDER')

class ImageFile:
    def __init__(self, index=0, filename=None, batch=None, stored=False, selected=False, tracked=False):
        self.index = index
        self.filename = filename
        self.batch = batch
        self.stored = stored
        self.selected = selected
        self.tracked = tracked
        
    def to_list(self):
        return [
            '=ROW()',
            self.filename,
            self.batch,
            self.stored,
            self.selected
        ]
            
        
    def __eq__(self, other):
        if not isinstance(other, ImageFile):
            return NotImplemented

        return self.filename == other.filename
    
    def __hash__(self):
        return hash(self.filename)

    def __repr__(self):
        return (f"ImageFile(index={self.index!r}, filename={self.filename!r}, "
                f"batch={self.batch!r}, stored={self.stored!r}, "
                f"selected={self.selected!r}, tracked={self.tracked!r})")

def build_service():
    """
    Build and return Google API service
    """
    creds = service_account.Credentials.from_service_account_file('service_account.json', scopes=SCOPES)

    service = build("sheets", "v4", credentials=creds)

    return service
            
def list_files(path):
    """
    List files matching FILENAME_REGEX in path and subdirs
    """
    result = []
    for _, _, files in os.walk(path):
        result.extend(
            files
        )
    return result
    
def build_local_list(all_images_path, selected_images_path):
    all_images = set(list_files(all_images_path))
    selected_images = set(list_files(selected_images_path))
    
    in_both = all_images & selected_images
    only_stored = all_images - selected_images
    only_selected = selected_images - all_images
    
    all = []
    
    for img in in_both:
        match = re.match(FILENAME_REGEX, img)
        if match:
            all.append(
                ImageFile(
                    index=0,
                    filename=img,
                    batch=match.group('batch'),
                    stored=True,
                    selected=True,
                    tracked=False
                )
            )
        
    for img in only_stored:
        match = re.match(FILENAME_REGEX, img)
        if match:
            all.append(
                ImageFile(
                    index=0,
                    filename=img,
                    batch=match.group('batch'),
                    stored=True,
                    selected=False,
                    tracked=False
                )
            )
        
    for img in only_selected:
        match = re.match(FILENAME_REGEX, img)
        if match:
            all.append(
                ImageFile(
                    index=0,
                    filename=img,
                    batch=match.group('batch'),
                    stored=False,
                    selected=True,
                    tracked=False
                )
            )
    
    return all

def parse_bool(value):
    truth = ['TRUE']
    
    if value in truth:
        return True
    return False

def build_remote_list(service):
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range='tracking!A2:E')
        .execute()
    )
    rows = result.get("values", [])
    files = []
    for row in rows:
        files.append(
            ImageFile(
                index=int(row[0]),
                filename=row[1],
                batch=row[2],
                stored=parse_bool(row[3]),
                selected=parse_bool(row[4]),
                tracked=True
            )
        )

    return files

def compare(tracked, local):
    to_update = []
    to_insert = []
    for f in local:
        if f in tracked:
            f.index = tracked[tracked.index(f)].index
            f.tracked = True
            to_update.append(f)
        else:
            to_insert.append(f)
    
    return to_insert, to_update

def insert_files(service, values):
    values = [
        f.to_list() for f in values
    ]
    
    body = {
        'values': values
    }
    
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=SPREADSHEET_ID,
            range='tracking!A2:E',
            valueInputOption="USER_ENTERED",
            body=body
        )
        .execute()
    )

def update_files(service, values):
    data = []
    
    for f in values:
        data.append(
            {
                'range': f'tracking!A{f.index}:E{f.index}',
                'values': [f.to_list()]
            }
        )
    body = {
        'valueInputOption': 'USER_ENTERED',
        'data': data
    }
    
    result = (
        service.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body)
        .execute()
    )
 
if __name__ == '__main__':
    service = build_service()
    
    images = build_local_list(all_images_path=ALL_IMAGES_FOLDER, selected_images_path=SELECTED_IMAGES_FOLDER)
    remote = build_remote_list(service)
    
    to_insert, to_update = compare(remote, images)
    
    insert_files(service=service, values=to_insert)
    update_files(service=service, values=to_update)