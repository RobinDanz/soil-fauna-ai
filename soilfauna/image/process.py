import cv2
import numpy as np
from sklearn.cluster import KMeans

def process_crop(crop):
    kernel = np.ones((3,3), np.uint8)
    eroded = cv2.morphologyEx(crop, cv2.MORPH_DILATE, kernel, iterations=8)
    return eroded

def apply_kmeans(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    shape = image.shape
    rgb_image = image.reshape(-1, 3)
    kmeans_init_centers = np.asarray([
        [79.49, 130.62, 189.84],
        [131.84, 107.86, 76.36],
        [178.59, 173.83, 159.51],
        [47.20, 28.64, 18.90],
        [114.45, 146.57, 187.97]
    ])

    kmeans = KMeans(n_clusters=5, init=kmeans_init_centers, random_state=42)
    cluster_labels = kmeans.fit_predict(rgb_image)
    
    ratio = 1
    total_pixels = len(cluster_labels)

    total_0 = np.count_nonzero(cluster_labels == 0)
    total_4 = np.count_nonzero(cluster_labels == 4)

    print(f'Total pixels: {total_pixels}')

    if total_0 + total_4 >= ratio * total_pixels:
        print(f'Class removed: {0}')
        mask = ~np.isin(cluster_labels, [0])
    else:
        print(f'Class removed: {0, 4}')
        mask = ~np.isin(cluster_labels, [0, 4])

    img_array = np.array(rgb_image)
    new_img = np.full_like(img_array, 255)
    new_img[mask] = img_array[mask]

    new_img = new_img.reshape(shape)

    return new_img

def convert_to_binary(image):
    mask = (image == [255, 255, 255]).all(axis=-1)
    result = np.zeros_like(image)
    result[mask] = [255, 255, 255]

    return result