from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from sfai.operators import Operator
    from sfai.config import SegmentationConfig

import numpy as np
from dataclasses import dataclass
import matplotlib.pyplot as plt
import cv2
import random
import time

from sfai.pipeline import Pipeline, PipelineContext
from sfai.data import ImageTiler, Tile
from sfai.stitch import MaskStitcher
from sfai.mask import MaskProcessor
from sfai.data import ImageInfo
from sfai.export.data import CocoAnnotation
from sfai.export import OutputHandler
from sfai.logging import PipelineProgess

def random_rgb_bright(seed: Optional[int] = None, min_val=64, max_val=255):
    """Generate a random RGB color from a seed

    Args:
        seed (Optional[int], optional): Defaults to None.
        min_val (int, optional):  Defaults to 64.
        max_val (int, optional):  Defaults to 255.

    Returns:
        T (Tuple[int, int, int]): RGB color
    """
    rng = random.Random(seed)
    return (
        rng.randint(min_val, max_val),
        rng.randint(min_val, max_val),
        rng.randint(min_val, max_val),
    )


@dataclass
class TileResult:
    """Utility dataclass to hold a tile and the PipelineContext
    """
    tile: Tile
    ctx: PipelineContext

class ImagePipelineRunner:
    """
    Pipeline runner for a single image.
    
    Handles image operations.
    """
    def __init__(self, operators: List[Operator], config: SegmentationConfig):
        self.config = config
        self.operators = operators
        
    def run(self, image_info: ImageInfo, image: np.ndarray, output_handler: OutputHandler) -> tuple[List[CocoAnnotation], dict]:
        """Run the pipeline on an image
        """
        annotations: List[CocoAnnotation] = []
        
        stitcher = MaskStitcher()
        mask_processor = MaskProcessor()

        start_pipeline = time.time()

        tile_results = TilePipelinRunner(
            self.operators,
            self.config
        ).run(image_info, image, output_handler)
        
        end_pipeline = time.time()

        start_postprocess = time.time()

        label_image = stitcher.stitch(tiles=tile_results, image_shape=image.shape[:2])
        
        for annotation in mask_processor.build_annotations(label_image, image_id=image_info.id, category_id=1):
            annotations.append(annotation)
        
        end_postprocess = time.time()

        stats = {
            "pipeline": end_pipeline - start_pipeline,
            "postprocess": end_postprocess - start_postprocess,
            "total": (end_pipeline - start_pipeline) + (end_postprocess - start_postprocess)
        }
        
        if self.config.save_final_images:
            path = output_handler.image_dir / image_info.name
            
            plt.imsave(f'{path}_labels.png', label_image, cmap='nipy_spectral', format='png', dpi=400)
            
            img = image.copy()
            
            for ann in annotations:
                seg = ann.segmentation
                
                polygons = [
                    np.array(shape, dtype=np.int32).reshape(-1, 1, 2)
                    for shape in seg
                ]
                
                cv2.polylines(img, polygons, isClosed=True, color=(0, 255, 0), thickness=4)
            img_small = cv2.resize(img, None, fx=0.7, fy=0.7)
            plt.imsave(f'{path}_contours.jpg', cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB), format='jpg', pil_kwargs={"quality": 80})
                
        return annotations, stats
        
class TilePipelinRunner:
    """
    Pipeline runner for tiles.
    
    Splits an image into tiles and runs operations on each tile.
    """
    def __init__(self, operators: List[Operator], config: SegmentationConfig):
        self.operators = operators

        self.pipeline = Pipeline(operators=self.operators)
        self.tiler = ImageTiler(rows=config.tile_rows, cols=config.tile_columns)
        
    def run(self, image_info: ImageInfo, image: np.ndarray, output_handler: OutputHandler) -> List[TileResult]:
        tiles = self.tiler.split(image)
        results = []

        progress = PipelineProgess()
        progress.start(image_info.file_name, nb_tiles=len(tiles))
        
        for index, tile in enumerate(tiles):
            ctx = self.pipeline.run(tile.image, image_info, index, output_handler)

            results.append(TileResult(
                tile=tile,
                ctx=ctx
            ))
            
            progress.update()
        
        progress.close()
            
        return results