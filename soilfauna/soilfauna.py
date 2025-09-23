from segment import segment
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.as_posix()

model = ROOT_DIR + '/models/sam2_b.pt'
crop_output_dir = ROOT_DIR + '/out/crops'
annotations_output_dir = ROOT_DIR + '/out/annotations'
image_output_dir = ROOT_DIR + '/out/full'
dataset = '/Users/robin/Pictures/soil-fauna-ai/test_polygon'

if __name__ == '__main__':
    segment(model, dataset, crop_output_dir, annotations_output_dir, image_output_dir)