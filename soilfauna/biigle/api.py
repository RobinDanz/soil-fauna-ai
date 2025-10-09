from requests import Session
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

load_dotenv()

API_BASE_URL = os.getenv('BIIGLE_API_BASE_URL')

class BiigleAPI:
    """
    Biigle API requester
    """
    def __init__(self, server_url=API_BASE_URL):
        self.server_url = server_url
        self.session = self.build_session()
    
    def build_session(self):
        s = Session()
        s.headers = {'Accept': 'application/json'}
        print(os.getenv('BIIGLE_API_USER'))
        print(os.getenv('BIIGLE_API_KEY'))
        s.auth = HTTPBasicAuth(os.getenv('BIIGLE_API_USER'), os.getenv('BIIGLE_API_KEY'))

        return s

    def get_label_trees(self):
        url = self.server_url + 'label-trees'
        resp = self.session.get(url)
        return resp.json()

    def find_label_trees(self, name):
        """
        Finds a label tree id based on its name. Returns -1 if not found.
        """
        label_trees = self.get_label_trees()

        for label_tree in label_trees:
            print(label_trees)
            if label_tree.get('name') == name:
                return label_tree.get('id')
        
        return -1
    
    def download_label_tree(self, output_path='.'):
        url = self.server_url + 'export/label-trees'
        output_file = os.path.join(output_path, 'label-tree.zip')
        print(output_file)
        resp = self.session.get(url)
        
        open(output_file, 'wb').write(resp.content)

        return output_file


    

    