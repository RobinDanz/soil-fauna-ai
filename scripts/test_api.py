from soilfauna.biigle.api import BiigleAPI

if __name__ == '__main__':
    api = BiigleAPI()

    api.download_label_tree('test')