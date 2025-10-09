from pathlib import Path
import os
import cv2
import json
from typing import List
from soilfauna.image.process import apply_kmeans

class Dataset:
    """
    Dataset loader
    """
    def __init__(self, data_path, metadata_path=None, preload=True, metadata_prefix='metadata'):
        self.data_path = data_path
        self.metadata_path = metadata_path
        self.metadata_prefix = metadata_prefix

        self.data: List[ImageData] = []

        if preload:
            self.load()

    def load(self, with_metadata=True):
        data_path = Path(self.data_path)
        metadata_path = None

        if self.metadata_path:
            metadata_path = Path(self.metadata_path)

        files = list(data_path.rglob('*.jpg'))

        for image in files:
            name = image.stem
            metadata_json = None

            if metadata_path:
                metadata_json = next(metadata_path.rglob(f'{name}{self.metadata_prefix}.json'), None)
            
            self.append(
                ImageData(image_path=image, metadata_path=metadata_json)
            )
            
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __setitem__(self, index, value):
        self.data[index] = value

    def __delitem__(self, index):
        del self.data[index]

    def __iter__(self):
        return iter(self.data)
    
    def append(self, value):
        self.data.append(value)

class ImageData:
    """
    Object holding image and json metadata
    """
    def __init__(self, image_path: Path, metadata_path=None, crops_padding=10):
        self.image_path = image_path
        self.metadata_path = metadata_path
        self.padding = crops_padding

        self.image = None
        self.metadata = None

        self.loaded = False

    def load(self):
        if not self.loaded:
            self.raw_image = self.read_image(self.image_path)
            self.image = apply_kmeans(self.raw_image)
            if self.metadata_path:
                self.metadata = self.read_json(self.metadata_path)
            self.full_height, self.full_width = self.image.shape[:2]

            self.loaded = True

        return (self.image, self.metadata)

    def read_image(self, image_path):
        return cv2.imread(image_path)

    def read_json(self, metadata_path):
        with open(metadata_path, 'r') as file:
            data = json.loads(file.read())

            return data
        
    def count(self):
        if self.loaded and self.metadata:
            return len(self.metadata['annotations'])
        
        return None
    
    def get_crops(self, rows=5, cols=5):
        if not self.loaded and not self.metadata:
            return []
        
        crops = []

        height, width, _ = self.image.shape

        crop_y = height//rows
        crop_x = width//cols

        crops = []

        for y in range(0, height, crop_y):
            for x in range(0, width, crop_x):
                x1 = max(x-self.padding, 0)
                y1 = max(y-self.padding, 0)
                x2 = min(x + crop_x + self.padding, width)
                y2 = min(y + crop_y + self.padding, height)
                crops.append(
                    (
                        self.image[y1:y2, x1:x2],
                        ((x2//2), (y2//2)),
                        (x1, y1, x2, y2),
                        self.raw_image[y1:y2, x1:x2]
                    )
                )
        return crops
        
        # for annotation in self.metadata['annotations']:
        #     for bbox in annotation['bbox']:
        #         center_x = bbox['center_x']
        #         center_y = bbox['center_y']
        #         box_width = bbox['box_width']
        #         box_height = bbox['box_height']

        #         x1 = max(int(center_x - box_width/2 - self.padding), 0)
        #         x2 = min(int(center_x + box_width/2 + self.padding), self.full_width) 

        #         y1 = max(int(center_y - box_height/2 - self.padding), 0)
        #         y2 = min(int(center_y + box_height/2 + self.padding), self.full_height)

        #         box_center_x = int((x2-x1)/2)
        #         box_center_y = int((y2-y1)/2)

        #         crops.append(
        #             (
        #                 self.image[y1:y2, x1:x2],
        #                 (box_center_x, box_center_y),
        #                 (x1, y1, x2, y2)
        #             )
        #         )

        # return crops
    
    def slice(self, tile_height=500, tile_width=500):
        tiles = []

        height, width, _ = self.image.shape

        for i in range(0, height, tile_height):
            for j in range(0, width, tile_width):
                tile = self.image[i:i+tile_height, j:j+tile_width]
                tiles.append(tile)
        
        return tiles
    
    def __str__(self):
        return f'Image: {str(self.image_path)}, Metadata: {str(self.metadata_path)}'