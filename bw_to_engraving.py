from calibration_profile import CalibrationData
from scipy.signal import savgol_filter
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from tqdm import tqdm
import numpy as np
import cv2
import math

DEGREE_OF_FUNCTION = 3


def prepare_for_engraving(image, calibration_data: CalibrationData):
    model, polynomial_features = construct_model_from_calibration(calibration_data)
    transformed_rgb = transform_image(image, model, polynomial_features)

    return transformed_rgb


def construct_model_from_calibration(calibration_data):
    engraved_lightness_levels, file_lightness_levels = prepare_dataset(calibration_data)
    # experimental and assumptions might not hold
    engraved_lightness_levels, file_lightness_levels = truncate_lightness_levels(
        engraved_lightness_levels, file_lightness_levels)

    # engraved_lightness_levels, file_lightness_levels = nudge_to_lighter(
    #     engraved_lightness_levels, file_lightness_levels)

    model, polynomial_features = build_model(engraved_lightness_levels, file_lightness_levels)

    return model, polynomial_features


def transform_image(image, model, polynomial_features):
    # print(image.shape)
    # hls_image = cv2.cvtColor(image, cv2.GRAY)
    # hls_image = cv2.cvtColor(image, cv2.COLOR_RGB2HLS)
    # lightnesses = (hls_image.reshape(-1, 3)[:, [1]] / 255)
    lightnesses = (image.reshape(-1, 1) / 255)

    # experimental and can be optimized
    # lightnesses = stretch_levels(lightnesses)

    lightnesses_poly = polynomial_features.fit_transform(lightnesses)

    # use the model to predict the adapted lightnesses for the lasercutter
    out_lightness = model.predict(lightnesses_poly)

    # clip values as the regression model could return invalid numbers
    np.clip(out_lightness, 0, 1, out=out_lightness)

    # add zero columns and reshape to transform into a correct HSL image
    out_hls = np.c_[np.zeros(out_lightness.shape[0]), out_lightness, np.zeros(out_lightness.shape[0])] * 255
    out_hls = out_hls.reshape((image.shape[0], image.shape[1], 3))

    # convert the image into RGB color space
    transformed_rgb = cv2.cvtColor(out_hls.astype(np.float32), cv2.COLOR_HLS2RGB)
    return transformed_rgb


def stretch_levels(lightnesses):
    max_darkness_photo = np.min(lightnesses)
    max_lightness_photo = np.max(lightnesses)

    print("Adapting lightnesses of input photo...")
    lightnesses_stretched = np.array(
        [relative_lightness(value, max_lightness_photo, max_darkness_photo) for value in tqdm(lightnesses)]).reshape(-1, 1)

    return lightnesses_stretched


def build_model(engraved_lightness_levels, file_lightness_levels):
    polynomial_features = PolynomialFeatures(degree=DEGREE_OF_FUNCTION)
    x_poly = polynomial_features.fit_transform(engraved_lightness_levels)

    model = LinearRegression()
    model.fit(x_poly, file_lightness_levels)

    return model, polynomial_features


def truncate_lightness_levels(engraved_lightness_levels, file_lightness_levels):
    # smoothed = savgol_filter(np.ravel(engraved_lightness_levels), 13, 2)
    smoothed = savgol_filter(np.ravel(engraved_lightness_levels), 5, 2) # window size 51, polynomial order 3

    min_lightness_index = np.where(smoothed == np.amin(smoothed))[0][0]
    max_lightness_index = np.where(smoothed == np.amax(smoothed))[0][0]

    smaller_index = min(min_lightness_index, max_lightness_index)
    bigger_index = max(min_lightness_index, max_lightness_index)

    engraved_lightness_levels_trunacted = engraved_lightness_levels[smaller_index:bigger_index, :]
    file_lightness_levels_truncated = file_lightness_levels[smaller_index:bigger_index, :]

    return engraved_lightness_levels_trunacted, file_lightness_levels_truncated


def nudge_to_lighter(engraved_lightness_levels, file_lightness_levels):
    nudged_file_lightness = np.array([math.pow(orig_file_level, 0.9) for orig_file_level in file_lightness_levels])

    return engraved_lightness_levels, nudged_file_lightness


def prepare_dataset(calibration_data):
    # get lightness of material
    median_engraved_whiteness = calibration_data.median_whiteness

    # prepare dataset
    engraved_lightnesses = np.array([])
    file_lightnesses = np.array([])

    # add value for no engraving at all
    file_lightnesses = np.append(file_lightnesses, [255])
    engraved_lightnesses = np.append(engraved_lightnesses, [median_engraved_whiteness])
    for file_lightness, engraved_lightness in calibration_data.svg_lightness_to_engraved_lightness.items():
        white_difference = median_engraved_whiteness - engraved_lightness

        # TODO better determine threshold
        if white_difference > 10:
            file_lightnesses = np.append(file_lightnesses, [file_lightness])
            engraved_lightnesses = np.append(engraved_lightnesses, [engraved_lightness])

    # extract also min lightness/darkness to determine relative lightness values
    max_engraved_darkness = np.min(engraved_lightnesses)

    engraved_lightness_levels = np.array(
        [relative_real_mix(value, median_engraved_whiteness, max_engraved_darkness) for value in
         engraved_lightnesses]).reshape(-1, 1)
    file_lightness_levels = np.array([relative_lightness(value, 255, 0) for value in file_lightnesses]).reshape(-1, 1)

    return engraved_lightness_levels, file_lightness_levels


def relative_real_mix(measurement, light, dark):
    relative = relative_lightness(measurement, light, dark)
    real = relative_lightness(measurement, 255, 0)
    return (relative * 0.6) + (real * 0.4)


def relative_lightness(measurement, light, dark):
    light_dark_range = light - dark
    return (measurement - dark) / light_dark_range