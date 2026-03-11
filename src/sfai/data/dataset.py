from abc import ABC, abstractmethod
from pathlib import Path
import cv2
from dataclasses import dataclass
from typing import List
from collections import defaultdict
from sfai.config import SegmentationConfig



@dataclass
class ImageInfo:
    """
    Dataclass holding image informations
    """
    id: int
    name: str
    file_name: str
    path: Path
    width: int
    height: int

class Dataset(ABC):
    """
    Base class for datasets.
    """
    def __init__(self, root: Path, paths: List[Path], config: SegmentationConfig):
        self.config = config
        self.root = root
        self.paths = paths
        
    def ignore_borders(self, image):
        border_size = self.config.ignore_border_size
        
        if self.config.ignore_border_top:
            image = image[border_size:, :, :]
        
        if self.config.ignore_border_bottom:
            image = image[:-border_size, :, :]
        
        if self.config.ignore_border_left:
            image = image[:, border_size:, :]
        
        if self.config.ignore_border_right:
            image = image[:, :-border_size, :]
        
        return image
    
    @abstractmethod
    def __iter__(self):
        pass
    
    @abstractmethod
    def __len__(self):
        pass
    
class ImageDataset(Dataset):

    EXTENSIONS = {'.jpg', '.jpeg', '.png'}
        
    def __iter__(self):
        """
        Iterates over the dataset

        Yields:
            (Tuple[ImageInfo, np.ndarray])
        """
        for id, path in enumerate(self.paths, 1):
            full_path = self.root / path
            img = cv2.imread(str(full_path))
            img = self.ignore_borders(img)          
            info = ImageInfo(
                id=id,
                name=full_path.stem,
                file_name=full_path.name,
                path=full_path,
                height=img.shape[0],
                width=img.shape[1]
            )
            
            yield info, img
    
    def __len__(self):
        return len(self.paths)
    
class TIFFImageDataset(ImageDataset):
    EXTENSIONS = {'.tiff', '.tif'}

    def __iter__(self):
        for id, path in enumerate(self.paths, 1):
            pass
        
class CompositeDataset(Dataset):
    def __init__(self, root, datasets, config: SegmentationConfig):
        self.datasets = datasets

        paths = []
        for d in datasets:
            paths.extend(d.paths)
        
        super().__init__(root, paths, config=config)
            
        
    def __iter__(self):
        for dataset in self.datasets:
            yield from dataset

    def __len__(self):
        return sum(len(d) for d in self.datasets)
           
class DatasetFactory:

    DATASET_CLASSES = [ImageDataset, TIFFImageDataset]

    @classmethod
    def create(cls, path: Path, config: SegmentationConfig):
        """
        """
        if path.is_file():
            root = path.parent
            files = [path]
        else:
            root = path
            files = [p for p in path.rglob("*") if p.is_file()]
            
        return cls._build_datasets(root, files, config)

    @classmethod
    def _build_datasets(cls, root, files: List[Path], config: SegmentationConfig) -> Dataset:
        groups = defaultdict(list)

        for file in files:
            ext = file.suffix.lower()

            for dataset_cls in cls.DATASET_CLASSES:
                if ext in dataset_cls.EXTENSIONS:
                    groups[dataset_cls].append(file.relative_to(root))
                    break

        datasets = [
            dataset_cls(root, paths, config)
            for dataset_cls, paths in groups.items()
        ]

        if len(datasets) == 1:
            return datasets[0]

        return CompositeDataset(root, datasets, config)

    
def generate_datasets(config: SegmentationConfig) -> List[Dataset]:
    """
    Utility method to generate datasets from a list of path
    
    Args:
        datasets (List[Path]): List of path to images or folders
    
    Returns:
        (List[Dataset]): List of Dataset objects.
    """
    out = []
    
    for path in config.datasets:
            out.append(DatasetFactory.create(path, config))
    
    return out