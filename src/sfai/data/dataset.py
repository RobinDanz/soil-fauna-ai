from abc import ABC, abstractmethod
from pathlib import Path
import cv2
from dataclasses import dataclass
from typing import List
from PIL import Image

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
    Base abstract class for datasets.
    """
    @abstractmethod
    def __iter__(self):
        pass
    
    @property
    @abstractmethod
    def length(self):
        pass
    
class ImageDataset(Dataset):
    """
    Dataset implementation for images

    Args:
        path (Path): Path to a folder or a single image
        extensions (List[str], optional): Specific extensions to look for. Default is ['.jpg', '.jpeg', '.png']
    
    Attributes:
        path (Path): Base directory
        images_paths (List[Path]): List of images paths of the dataset
    """
    def __init__(self, path: Path, extensions=['.jpg', '.jpeg', '.png']):
        self.path = path
        self.images_paths = []

        if path.is_file() and path.suffix.lower() in extensions:
            self.images_paths.append(path)
        elif path.is_dir():
            for p in path.iterdir():
                if p.suffix.lower() in extensions:
                    self.images_paths.append(p)
        
    def __iter__(self):
        """
        Iterates over the dataset

        Yields:
            (Tuple[ImageInfo, np.ndarray])
        """
        for id, path in enumerate(self.images_paths, 1):
            img = cv2.imread(str(path))
            
            info = ImageInfo(
                id=id,
                name=path.stem,
                file_name=path.name,
                path=path,
                height=img.shape[0],
                width=img.shape[1]
            )
            
            yield info, img
    
    @property
    def length(self):
        return len(self.images_paths)
    
class TIFFImageDataset(ImageDataset):
    def __init__(self, path):
        super().__init__(path, extensions=['.tiff'])

    def __iter__(self):
        print(self.images_paths)

            
   
def generate_datasets(datasets: List[Path]) -> List[Dataset]:
    """
    Utility method to generate datasets from a list of path
    
    Args:
        datasets (List[Path]): List of path to images or folders
    
    Returns:
        (List[Dataset]): List of Dataset objects.
    """
    out = []
    
    for path in datasets:
            out.append(
                ImageDataset(path)
            )
            
    return out
            
            
                