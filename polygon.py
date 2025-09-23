import json
import shapely

if __name__ == '__main__':
    data = {}

    with open('./out/annotations/test_polygon-annotations.json', 'r') as f:
        data = json.load(f)

    annotations = data['annotations']

    for annotation in annotations:
        segmentations = annotation['segmentation']

        for coords in segmentations:
            points = list(zip(coords[0::2], coords[1::2]))
            if len(points) > 4:
                poly = shapely.Polygon(points)
                print(poly.is_valid)

            

            

    
