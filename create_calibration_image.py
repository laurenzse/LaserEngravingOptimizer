from calibration_profile import GridCalibrationSpecification
from calibration_image_generator import create_calibration_image
import cv2 as cv
import argparse

parser = argparse.ArgumentParser(description='Create a calibration gauge for engraving.')
parser.add_argument('block_size', type=int,
                    help='Height and width of one square calibration block.')
parser.add_argument('row_num', type=int,
                    help='Number of rows of calibration blocks.')
parser.add_argument('column_num', type=int,
                    help='Number of columns of calibration blocks.')

args = parser.parse_args()

print("## Create calibration image")
grid_spec = GridCalibrationSpecification(args.block_size, args.row_num, args.column_num)
calibration_image = create_calibration_image(grid_spec)
cv.imwrite('calibration_gauge.png', calibration_image)