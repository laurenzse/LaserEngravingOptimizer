from typing import Generator
import math
import numpy as np
import cv2 as cv


class Image(np.ndarray): pass


class CalibrationArea:

    def __init__(self, top_left_corner, bottom_right_corner, svg_hls_color):
        self.top_left_corner = top_left_corner
        self.bottom_right_corner = bottom_right_corner
        self.svg_hls_color = svg_hls_color


class AbstractCalibrationImageSpecification:

    def get_width(self) -> int:
        pass

    def get_height(self) -> int:
        pass

    def get_whitespace_areas(self) -> Generator[CalibrationArea, None, None]:
        pass

    def get_colored_areas(self) -> Generator[CalibrationArea, None, None]:
        pass


class ARUCOCalibrationSpecification(AbstractCalibrationImageSpecification):

    def __init__(self, block_size: int, marker_size: int, number_of_rows: int, number_of_columns: int):
        self.block_size = block_size
        self.marker_size = marker_size
        self.number_of_rows = number_of_rows
        self.number_of_columns = number_of_columns

        self.calibration_image_width = math.ceil(
            self.block_size + number_of_columns * self.block_size + 3 * (self.block_size / 2))
        self.calibration_image_height = math.ceil(number_of_rows * self.block_size + 2 * (self.block_size / 2))

    def get_width(self) -> int:
        return self.calibration_image_width

    def get_height(self) -> int:
        return self.calibration_image_height

    def get_whitespace_areas(self) -> Generator[CalibrationArea, None, None]:
        x = (self.block_size / 2)
        x_end = (self.block_size / 2) + self.marker_size
        y = self.marker_size + 2 * (self.block_size / 2)
        y_end = self.calibration_image_height - (self.block_size / 2)

        white_hls = np.uint8([[[0, 255, 0]]])

        yield CalibrationArea((x, y), (x_end, y_end), white_hls)

    def get_colored_areas(self) -> Generator[CalibrationArea, None, None]:
        spacing = self.block_size * 0.15
        number_of_blocks = self.number_of_rows * self.number_of_columns
        block_count = 0
        for row_number in range(self.number_of_rows):
            for column_number in range(self.number_of_columns):
                x = math.ceil(
                    self.marker_size + column_number * self.block_size + 2 * (self.block_size / 2) + spacing)
                y = math.ceil(row_number * self.block_size + (self.block_size / 2) + spacing)

                x_end = math.ceil(x + self.block_size - spacing)
                y_end = math.ceil(y + self.block_size - spacing)

                # we suspect that the engraving darkness follows a root function, therefore we try to get the most
                # helpful data using an exponential function
                lightness = 255 - math.pow((1 + block_count) / number_of_blocks, 1.5) * 255
                hls_color = np.uint8([[[0, lightness, 0]]])

                block_count += 1
                yield CalibrationArea((x, y), (x_end, y_end), hls_color)


class GridCalibrationSpecification(AbstractCalibrationImageSpecification):

    def __init__(self, block_size: int, number_of_rows: int, number_of_columns: int, non_linearity_value:float = 1.8):
        self.block_size = block_size
        self.number_of_rows = number_of_rows
        self.number_of_columns = number_of_columns
        self.non_linearity_value = non_linearity_value

        self.calibration_image_width = math.ceil(number_of_columns * self.block_size)
        self.calibration_image_height = math.ceil(number_of_rows * self.block_size)

    def get_width(self) -> int:
        return self.calibration_image_width

    def get_height(self) -> int:
        return self.calibration_image_height

    def get_whitespace_areas(self) -> Generator[CalibrationArea, None, None]:
        x = (self.block_size / 2)
        x_end = (self.block_size / 2) + self.block_size
        y = (self.block_size / 2)
        y_end = (self.block_size / 2) + self.block_size

        white_hls = np.uint8([[[0, 255, 0]]])

        yield CalibrationArea((x, y), (x_end, y_end), white_hls)

    def get_colored_areas(self) -> Generator[CalibrationArea, None, None]:
        spacing = self.block_size * 0.1
        # vertical safety to give room to smoke
        vertical_safety = (self.block_size - spacing) * 0.3
        # vertical_safety = 0
        number_of_blocks = (self.number_of_rows * self.number_of_columns) - 1
        block_count = -1
        for row_number in range(self.number_of_rows):
            for column_number in range(self.number_of_columns):
                # first block is whitespace
                if block_count == -1:
                    block_count += 1
                    continue

                lightness_factor = math.pow((1 + block_count) / number_of_blocks, self.non_linearity_value)
                local_vertical_safety = vertical_safety * lightness_factor

                x = math.ceil((column_number * self.block_size) + spacing)
                y = math.ceil((row_number * self.block_size) + spacing + local_vertical_safety)

                x_end = math.ceil((column_number + 1) * self.block_size - spacing)
                y_end = math.ceil((row_number + 1) * self.block_size - spacing)

                # we suspect that the engraving darkness follows a root function, therefore we try to get the most
                # helpful data using an exponential function
                lightness = 255 - lightness_factor * 255
                hls_color = np.uint8([[[0, lightness, 0]]])

                block_count += 1
                yield CalibrationArea((x, y), (x_end, y_end), hls_color)


class CalibrationData:

    def __init__(self, calibration_specification: AbstractCalibrationImageSpecification, calibration_image: Image):
        self.median_whiteness = self.get_median_whiteness(calibration_specification, calibration_image)
        self.svg_lightness_to_engraved_lightness = self.get_input_output_mapping(calibration_specification, calibration_image)

    @staticmethod
    def get_median_whiteness(calibration_specification: AbstractCalibrationImageSpecification, calibration_image: Image):
        white_values = np.array([])
        # get median whiteness
        for calibration_area in calibration_specification.get_whitespace_areas():
            area_hls = CalibrationData.extract_color_from_area(calibration_area, calibration_image)
            values = np.reshape(area_hls[:, :, 1], (-1), 'C')

            white_values = np.append(white_values, values)

        return np.median(white_values)

    @staticmethod
    def get_input_output_mapping(calibration_specification: AbstractCalibrationImageSpecification, calibration_image: Image):
        svg_lightness_to_engraved_lightness = {}

        for calibration_area in calibration_specification.get_colored_areas():
            area_hls = CalibrationData.extract_color_from_area(calibration_area, calibration_image)
            values = np.reshape(area_hls[:, :, 1], (-1), 'C')
            measured_lightnesses = CalibrationData.filter_quantile(values, 0.4, 0.6)

            median_lightness = np.median(measured_lightnesses)
            svg_lightness_to_engraved_lightness[calibration_area.svg_hls_color[0, 0, 1]] = median_lightness

        return svg_lightness_to_engraved_lightness

    @staticmethod
    def filter_quantile(data, lower_limit, upper_limit):
        lower_quantile = np.quantile(data, lower_limit)
        upper_quantile = np.quantile(data, upper_limit)
        lower_filtered = data[lower_quantile <= data]
        upper_filtered = lower_filtered[lower_filtered <= upper_quantile]
        return upper_filtered

    @staticmethod
    def extract_color_from_area(calibration_area: CalibrationArea, calibration_image: Image):
        x, x_end = calibration_area.top_left_corner[0], calibration_area.bottom_right_corner[0]
        y, y_end = calibration_area.top_left_corner[1], calibration_area.bottom_right_corner[1]
        block = calibration_image[int(y):int(y_end), int(x):int(x_end)]
        block_hls = cv.cvtColor(block, cv.COLOR_RGB2HLS)
        return block_hls

    def get_dark_light_range(self):
        max_darkness = min(self.svg_lightness_to_engraved_lightness.values())
        return (self.median_whiteness - max_darkness) / 255;
