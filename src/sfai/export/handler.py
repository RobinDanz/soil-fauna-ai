import os
from pathlib import Path
from sfai.config import SegmentationConfig


class OutputHandler:
    """Utility class that manages the output

    Args:
        base_dir (Path, optional): Base output directory. Defaults to default.DEFAULT_OUTPUT_DIR.
        subname (str | None, optional): Subdir. Defaults to None.
    """
    def __init__(self, config: SegmentationConfig, subname: str | None = None):
        self.config = config
        self.base_dir = config.base_output_dir
        
        if subname:
            self.base_dir = self.base_dir / subname
        
    def generate_output_folders(self):
        """Generate output folders for annotations, crops and images.
        """
        self.annotation_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.save_intermediate_images:
            self.crop_dir.mkdir(parents=True, exist_ok=True)
            
        if self.config.save_final_images:
            self.image_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_crop_subfodler(self, image_name: str, subfolder: str) -> Path:
        """Generate a subfolder for each type of crop. The folder is generated into the 'crops' folder.

        Args:
            image_name (str): Name of the image
            subfolder (str): Name of the folder to create

        Returns:
            Path: Path to the subfolder
        """
        crop_subfolder = self.crop_dir / image_name / subfolder
        crop_subfolder.mkdir(parents=True, exist_ok=True)
        
        return crop_subfolder
    
    @property
    def annotation_dir(self) -> Path:
        return Path(os.path.join(self.base_dir, 'annotations'))
    
    @property
    def crop_dir(self) -> Path:
        return Path(os.path.join(self.base_dir, 'crops'))
    
    @property
    def image_dir(self) -> Path:
        return Path(os.path.join(self.base_dir, 'images'))
    
    @property
    def images_jsonl_path(self) -> Path:
        return Path(os.path.join(self.annotation_dir, 'images.jsonl'))
    
    @property
    def annotations_jsonl_path(self) -> Path:
        return Path(os.path.join(self.annotation_dir, 'annotations.jsonl'))
    
    @property
    def categories_jsonl_path(self) -> Path:
        return Path(os.path.join(self.annotation_dir, 'categories.jsonl'))
        