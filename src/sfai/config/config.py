from dataclasses import dataclass, fields, field, MISSING
from pathlib import Path
import os
import yaml
from sfai.config import default
from typing import ClassVar, Mapping, List, Tuple, get_args, get_origin
from types import UnionType

@dataclass(init=False)
class BaseConfig:
    """
    Base class holding a configuration
    """
    CONFIG_NAMESPACE: ClassVar[str | None] = None
    
    log_level: int = 1
    root_dir: Path = default.PROJECT_ROOT_DIR
    
    @classmethod
    def from_file(cls, path: str | Path):
        """
        Load a configuration from a yaml file
        """
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
            
        base_config = cls._extract_base_config(raw)
        sub_config = cls._extract_sub_config(raw)
        
        obj = cls.from_dict(sub_config)
        obj._apply_base_config(base_config)
        
        return obj
            
    @classmethod
    def from_dict(cls, data: Mapping):
        """
        Generate a configuration from a dict
        """
        fields_defs = {f.name: f for f in fields(cls)}
        obj = cls.__new__(cls)
        for name, field in fields_defs.items():
            if name in data and data[name]:
                value = cls._coerce(field.type, data[name])
            else:
                if field.default_factory is not MISSING:
                    value = field.default_factory()
                elif field.default is not MISSING:
                    value = field.default
                else:
                    raise TypeError(f"Required field missing from config: {name}")
            setattr(obj, name, value)

        obj.validate()
        return obj
        
    @classmethod
    def _extract_base_config(cls, raw: Mapping) -> dict:
        """
        Get high level configuration
        """
        return {
            k: v for k, v in raw.items() if not isinstance(v, dict)
        }
        
    @classmethod
    def _extract_sub_config(cls, raw: Mapping) -> dict:
        """
        Get specific configuration for task
        """
        if cls.CONFIG_NAMESPACE:
            return raw.get(cls.CONFIG_NAMESPACE, {})
        return {}
    
    def _apply_base_config(self, base_config: dict):
        """
        
        """
        base_fields = {f.name for f in fields(BaseConfig)}
        
        for name in base_fields:
            if name in base_config:
                value = self._coerce(
                    BaseConfig.__annotations__[name],
                    base_config[name],
                )
                
                setattr(self, name, value)
    
    @staticmethod 
    def _coerce(tp, value):
        """
        Converts required values into Path
        """
        if tp is Path and isinstance(value, str):
            return Path(value)
        if isinstance(tp, UnionType) and Path in get_args(tp):
            return Path(value)
        if get_origin(tp) is list and Path in get_args(tp):
            return [
                Path(val) for val in value if isinstance(val, str)
            ]
        return value
    
    def validate(self):
        """
        Config validation.
        
        Override in subclasses
        """
        pass
    
    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        parts = []

        for f in fields(self.__class__):
            value = getattr(self, f.name, None)
            parts.append(f"{f.name}={value!r}")

        return f"{cls_name}({', '.join(parts)})"
    

@dataclass(init=False)
class SegmentationConfig(BaseConfig):
    """
    Class holding a segmentation run configuration
    """
    CONFIG_NAMESPACE = 'segment'
    
    id: int | None = None
    save_intermediate_images: bool = False
    save_final_images: bool = False
    name: str = default.DEFAULT_RUN_NAME
    output_dir: Path = default.DEFAULT_OUTPUT_DIR
    model: Path = default.DEFAULT_MODEL
    tile_rows: int = default.DEFAULT_TILE_ROWS
    tile_columns: int = default.DEFAULT_TILE_COLUMNS
    hsv_lower_bound: Tuple[int, int, int] = field(default_factory=lambda: default.DEFAULT_HSV_LOWER_BOUND)
    hsv_upper_bound: Tuple[int, int, int] = field(default_factory=lambda: default.DEFAULT_HSV_UPPER_BOUND)
    ignore_borders: str = ''
    ignore_border_top: bool = False
    ignore_border_bottom: bool = False
    ignore_border_left: bool = False
    ignore_border_right: bool = False
    ignore_border_size: int = 200
    
    datasets: List[Path] = field(default_factory=lambda: [])
    
    def validate(self):
        """
        Validate a configuration. Generates the run ID
        """
        if self.datasets is None:
            raise ValueError("Dataset is required")
        
        if self.id is None:
            self.id = self._generate_id()
            
        if self.ignore_borders:
            self._set_ignored_borders()
            
    def _set_ignored_borders(self) -> Tuple[bool, bool, bool, bool]:
        """
        Parses the 'ignore_borders' config str. Returns a boolean for each ignored borders.
        """
        
        borders_code = set(self.ignore_borders)
        
        out = {
            'ignore_border_top': 't',
            'ignore_border_bottom': 'b',
            'ignore_border_left': 'l',
            'ignore_border_right': 'r'
        }
        
        for key, value in out.items():
            if value in borders_code:
                setattr(self, key, True)
        
        
    def _generate_id(self) -> int:
        """
        Generate run ID
        """
        run_dir = self.output_dir / self.name
        run_dir.mkdir(parents=True, exist_ok=True)
        
        next_id = len(next(os.walk(run_dir))[1])
        
        return next_id + 1
    
    def create_run_folder(self):
        """
        Create run folder
        """
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
    @property
    def base_output_dir(self) -> Path:
        return Path(os.path.join(self.output_dir, self.name, str(self.id)))

@dataclass
class IgnoreSliceConfig:
    pass
    
    