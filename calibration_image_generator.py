# create calibration image
import cv2 as cv
import numpy as np
from calibration_profile import AbstractCalibrationImageSpecification


def create_calibration_image(specification: AbstractCalibrationImageSpecification):
    # Create a white image
    calibration_image = 255 * np.ones((specification.get_height(), specification.get_width(), 3), np.uint8)

    # draw calibration blocks
    for calibration_area in specification.get_colored_areas():
        x, x_end = calibration_area.top_left_corner[0], calibration_area.bottom_right_corner[0]
        y, y_end = calibration_area.top_left_corner[1], calibration_area.bottom_right_corner[1]

        rgb_color = tuple(map(int, cv.cvtColor(calibration_area.svg_hls_color, cv.COLOR_HLS2RGB)[0][0]))

        cv.rectangle(calibration_image, (x, y),
                     (x_end, y_end), rgb_color, -1)

    return calibration_image