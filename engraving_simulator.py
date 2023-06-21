import cv2 as cv
import numpy as np
from bisect import bisect
from calibration_profile import CalibrationData
from tqdm import tqdm

simulation_table_cache = {}

def simulate_engraving(input_image, calibration_data: CalibrationData):
    hls_image = cv.cvtColor(input_image, cv.COLOR_RGB2HLS)
    lightnesses = hls_image.reshape(-1, 3)[:, [1]]

    if calibration_data not in simulation_table_cache:
        simulation_table_cache[calibration_data] = prepare_simulation_table(calibration_data)
    simulation_table = simulation_table_cache[calibration_data]

    print("Simulating lightnesses...")
    transformed = np.array([[simulation_table[int(xi[0])]] for xi in tqdm(lightnesses)])

    # add zero columns and reshape to transform into a correct HSL image
    out_hls = np.c_[np.zeros(transformed.shape[0]), transformed, np.zeros(transformed.shape[0])]
    out_hls = out_hls.reshape(hls_image.shape)

    # convert the image into RGB color space
    transformed_rgb = cv.cvtColor(out_hls.astype(np.float32), cv.COLOR_HLS2RGB)
    return transformed_rgb


def prepare_simulation_table(calibration_data):
    available_input_lightnesses = calibration_data.svg_lightness_to_engraved_lightness.keys()
    sorted_avail_lightnesses = sorted(available_input_lightnesses)

    def interpolated_output_lightness(input_lightness):
        insert_index = bisect(sorted_avail_lightnesses, input_lightness)
        output_dict = calibration_data.svg_lightness_to_engraved_lightness
        if insert_index == 0:
            return output_dict[sorted_avail_lightnesses[insert_index]]
        elif insert_index == len(sorted_avail_lightnesses):
            return output_dict[sorted_avail_lightnesses[insert_index - 1]]
        else:
            upper_neighbor = sorted_avail_lightnesses[insert_index]
            lower_neighbor = sorted_avail_lightnesses[insert_index - 1]
            range = upper_neighbor - lower_neighbor
            return ((output_dict[upper_neighbor] * (1 - (upper_neighbor - input_lightness) / range)) \
                    + (output_dict[lower_neighbor] * ((upper_neighbor - input_lightness) / range)))

    simulation_table = {}
    for l in range(256):
        simulation_table[l] = int(interpolated_output_lightness(l))
    return simulation_table
