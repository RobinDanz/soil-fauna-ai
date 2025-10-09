from dataclasses import dataclass, asdict, field
from typing import List
import cv2
from shapely import Polygon, LinearRing
import numpy as np

@dataclass
class CocoImage:
    id: int
    width: int
    height: int
    file_name: str

    def to_dict(self):
        return asdict(self)
    
@dataclass
class CocoAnnotation:
    id: int
    image_id: int
    category_id: int
    area: float
    iscrowd: int
    bbox: List[int] = field(default_factory=list)
    segmentation: List[List[int]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

@dataclass
class CocoCategory:
    id: int
    name: str

    def to_dict(self):
        return asdict(self)

@dataclass
class CocoObject:
    images: List[CocoImage] = field(default_factory=list)
    categories: List[CocoCategory] = field(default_factory=list)
    annotations: List[CocoAnnotation] = field(default_factory=list)

    @property
    def images_count(self):
        return len(self.images)
    
    @property
    def categories_count(self):
        return len(self.categories)
    
    @property
    def annotations_count(self):
        return len(self.annotations)

    def to_dict(self):
        return asdict(self)


class CocoGenerator:
    DEFAULT_CATEGORY = 'Unclassified'

    def __init__(self):
        self.coco = CocoObject()

    def add_image(self, image, file_name):
        id = self.coco.images_count + 1
        height, width, _ = image.shape
        
        image_object = CocoImage(
            id=id,
            width=width,
            height=height,
            file_name=file_name
        )

        self.coco.images.append(image_object)

        return id
    
    def add_category(self, name=DEFAULT_CATEGORY):
        id = self.coco.categories_count + 1
        
        category_object = CocoCategory(
            id=id,
            name=name
        )

        self.coco.categories.append(category_object)

        return id
    
    def add_annotations(self, image_id, category_id, contour):
        points = contour.reshape(-1, 2).tolist()
        if len(points) < 3:
            return -1
        
        if points[0] != points[-1]:
            points.append(points[0])

        if not LinearRing(points).is_ring:
            return -1
        
        polygon = Polygon(points)
        
        id = self.coco.annotations_count + 1

        bbox = self.calculate_bbox(polygon)
        area = self.calculate_area(polygon)

        annotation_object = CocoAnnotation(
            id=id,
            image_id=image_id,
            category_id=category_id,
            segmentation=[np.array(points).reshape(-1).tolist()],
            bbox=bbox,
            iscrowd=0,
            area=area
        )

        self.coco.annotations.append(annotation_object)

        return id
    
    def calculate_bbox(self, polygon: Polygon):
        minx, miny, maxx, maxy = polygon.bounds

        width = maxx - minx
        height = maxy - miny

        return [minx, miny, width, height]

    def calculate_area(self, polygon: Polygon):
        return polygon.area
    
    def generate(self):
        return self.coco.to_dict()
        