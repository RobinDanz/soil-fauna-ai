import rasterio
from rasterio.windows import Window
from rasterio.plot import show

import matplotlib.pyplot as plt

tile_size = 5000

with rasterio.open("c:\\Users\\Robin\\Pictures\\data\\stitch\\A01-A_stitched.tiff") as src:
    width = src.width
    height = src.height

    print(width)
    print(height)

    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            window = Window(
                col_off=x,
                row_off=y,
                width=min(tile_size, width - x),
                height=min(tile_size, height - y)
            )

            tile = src.read(1, window=window)

            print(f"Traitement tuile x={x}, y={y}, shape={tile.shape}")
            
            # plt.imshow(tile, cmap='rgb')
            # show(tile)

