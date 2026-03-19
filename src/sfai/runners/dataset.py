from __future__ import annotations
from typing import TYPE_CHECKING, List

from sfai.data import Dataset
from sfai.export import JsonlBufferedWriter, CocoWriter
from sfai.export.data import CocoImage, DEFAULT_CATEGORY
from sfai.logging import LOGGER
from sfai.runners.image import ImagePipelineRunner

if TYPE_CHECKING:
    from sfai.export import OutputHandler
    from sfai.config import SegmentationConfig
    from sfai.operators import Operator 
    from sfai.export.data import CocoCategory

class DatasetRunner:
    """Runner for a whole dataset

    Args:
        dataset (Dataset):
        operators (List[Operator]):
        output_handler (OutputHandler):
        config (SegmentationConfig):
    """
    def __init__(self, dataset: Dataset, operators: List[Operator], output_handler: OutputHandler, config: SegmentationConfig):
        self.operators = operators
        self.config = config
        self.dataset = dataset
        self.output_handler = output_handler

        self.image_runner = ImagePipelineRunner(
            operators=operators,
            config=self.config
        )

    def run(self):
        """Runs the pipeline on a dataset.
        """
        stats = {}
        categories: List[CocoCategory] = [DEFAULT_CATEGORY]

        annotation_file_name = self.dataset.root.stem + '.json'
        
        annotation_out = self.output_handler.annotation_dir / annotation_file_name

        coco_writer = CocoWriter(
            self.output_handler.images_jsonl_path,
            self.output_handler.annotations_jsonl_path,
            categories,
            annotation_out
        )
        
        images_writer = JsonlBufferedWriter(self.output_handler.images_jsonl_path)
        annotations_writer = JsonlBufferedWriter(self.output_handler.annotations_jsonl_path)
        
        for i, (image_info, image) in enumerate(self.dataset, 1):
            LOGGER.info(f"Image: {i}/{len(self.dataset)}")
            coco_img = CocoImage(
                id=image_info.id,
                width=image_info.source_width,
                height=image_info.source_height,
                file_name=image_info.file_name
            )
            
            images_writer.write(coco_img)
            
            annotations, timing = self.image_runner.run(image_info, image, self.output_handler)
            annotations_writer.write_list(annotations)
            stats[image_info.file_name] = timing
            
        images_writer.close()
        annotations_writer.close()
        
        coco_writer.write()