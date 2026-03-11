from sfai.config import SegmentationConfig
from sfai.segmentation import segment


def add_segment_parser(subparsers):
    """
    Add segment command parser to subparser
    """
    parser = subparsers.add_parser(
        "segment",
        help="Automatic segmentation tool"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=str,
        required=True,
        help="Config file"
    )
    
    parser.set_defaults(func=run_segmentation)
    
def run_segmentation(args):
    """
    CLI entrypoint for segmentation tool
    """
    cfg = SegmentationConfig.from_file(args.config)
    cfg.create_run_folder()
    segment(cfg)
