import argparse
from calibration_profile import GridCalibrationSpecification, CalibrationData
from engraving_simulator import simulate_engraving
from bw_to_engraving import prepare_for_engraving
from engraving_friendly_bw import convert_photo_to_engraving_friendly_bw
import cv2 as cv

parser = argparse.ArgumentParser(description='Optimize a color photo for engraving.')
parser.add_argument('block_size', type=int,
                    help='Height and width of one square calibration block.')
parser.add_argument('row_num', type=int,
                    help='Number of rows of calibration blocks.')
parser.add_argument('column_num', type=int,
                    help='Number of columns of calibration blocks.')
parser.add_argument('scanned_gauge_path', type=str,
                    help='File path of the scanned calibration gauge, '
                         'the image dimensions need to match the dimension of the generated gauge image.')
parser.add_argument('photo_path', type=str,
                    help='File path of the photo to optimize.')


args = parser.parse_args()

print("## Load laser profile")
calibration_image = cv.imread(args.scanned_gauge_path)
grid_spec = GridCalibrationSpecification(args.block_size, args.row_num, args.column_num)
calibration_data = CalibrationData(grid_spec, calibration_image)

print("## Convert color photo to engraving friendly bw photo")
input_image = cv.imread(args.photo_path, cv.IMREAD_COLOR)
engraving_friendly = convert_photo_to_engraving_friendly_bw(input_image, calibration_data)
cv.imwrite('greyscale.png', engraving_friendly)

print("## Adapt photo to profile of laser")
for_engraving = prepare_for_engraving(engraving_friendly, calibration_data)
cv.imwrite('greyscale_for_engraving.png', for_engraving)

print("## Simulate engraving")
simulated = simulate_engraving(for_engraving, calibration_data)
cv.imwrite('engraving_simulation_result.png', simulated)
