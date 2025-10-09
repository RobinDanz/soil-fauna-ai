import json
import cv2
import matplotlib.pyplot as plt
import numpy as np
from ultralytics import SAM

from soilfauna.dataset import Dataset
from soilfauna.export import CocoGenerator
from soilfauna.image.process import convert_to_binary


def get_coco_generator(generators, key):
    if key in generators:
        return generators[key]
    else:
        generator = CocoGenerator()
        category_id = generator.add_category()
        generators[key] = (generator, category_id)
        return generators[key]

def segment(model, dataset_path, metadata_path, crop_output, annotations_output, processed_output):
    dataset = Dataset(dataset_path, metadata_path, metadata_prefix='_no_bkgd')
    sam = SAM(model)

    coco_generators = {}

    for data in dataset:
        data.load()
        image = data.image

        coco_annotation, default_category_id = get_coco_generator(coco_generators, data.image_path.parent.stem)
        image_id = coco_annotation.add_image(image, data.image_path.name)

        print(f'Image: {data.image_path.stem}')
        image_masks = np.zeros((data.full_height, data.full_width), dtype=np.uint8)
        i = 1
        
        crops = data.get_crops()
        print(str(data))

        for crop, bbox_centers, coords, raw in crops:
            print(f'Crop analysis: {i}/{len(crops)}')
            binary = convert_to_binary(crop)
            inv = cv2.bitwise_not(binary)
            gray = cv2.cvtColor(inv, cv2.COLOR_BGR2GRAY)

            dist = cv2.distanceTransform(gray, cv2.DIST_L2, 5)
            _, dist_thresh = cv2.threshold(dist, 0.2*dist.max(), 1, cv2.THRESH_BINARY)
            
            contours, _ = cv2.findContours(dist_thresh.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            centers = []

            for cnt in contours:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx = int(M["m10"]/M["m00"])
                    cy = int(M["m01"]/M["m00"])
                    cv2.circle(crop, (cx, cy), 0, (255, 0, 0), 3)
                    centers.append([cx, cy])

            if centers:
                results = sam.predict(raw, points=centers)
                for result in results:
                    for mask in result.masks.data:
                        region_mask = mask.cpu().numpy().astype(np.uint8)
                        image_masks[coords[1]:coords[3], coords[0]:coords[2]] = np.maximum(image_masks[coords[1]:coords[3], coords[0]:coords[2]], region_mask)
            
            fig, (ax1, ax2) = plt.subplots(1, 2)
            ax1.imshow(crop)
            ax2.imshow(dist_thresh, cmap='gray')

            plt.savefig(f'{crop_output}/c{i}_{data.image_path.stem}.png', dpi=500)
            plt.close()
            i += 1

            print('==============================\n')

        mask_uint8 = image_masks.astype(np.uint8) * 255
        mask_contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

        for mask_contour in mask_contours:
            coco_annotation.add_annotations(
                image_id=image_id,
                category_id=default_category_id,
                contour=mask_contour
            )

        cv2.drawContours(data.image, mask_contours, -1, (0,255,0), 3)

        fig, (ax1, ax2) = plt.subplots(1, 2)
        ax1.imshow(data.image)
        ax2.imshow(image_masks, cmap='binary')
        plt.savefig(f'{processed_output}/fig_{data.image_path.stem}.png', dpi=400)
        plt.close()

    for name, (generator, _) in coco_generators.items():
        with open(f'{annotations_output}/{name}-annotations.json', 'w', encoding='utf-8') as file:
            json.dump(generator.generate(), file, ensure_ascii=False, indent=4)