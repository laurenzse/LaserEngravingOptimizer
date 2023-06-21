from decolorize import decolorize
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv


def convert_photo_to_engraving_friendly_bw(image, calibration_data):
    decolorized = decolorize(image) # decolorize
    grey_channel = decolorized[:,:,0]

    # normalize values
    normalized = (grey_channel - np.min(grey_channel)) / (np.max(grey_channel) - np.min(grey_channel))
    grey_image = plt.cm.gray(normalized, bytes=True)[:, :, [0]].reshape(normalized.shape[:2])

    # equalize histogram
    # img = cv.cvtColor(img, cv.COLOR_BGR2GRAY);
    # equalized = cv.equalizeHist(grey_image)
    equalized = grey_image

    # return grey_image

    # return apply_unsharp_mask(grey_image)

    return apply_clahe(calibration_data, equalized)


def apply_unsharp_mask(grey_image):
    gaussian_3 = cv.GaussianBlur(grey_image, (0, 0), 10.0)
    unsharp_image = cv.addWeighted(grey_image, 2.0, gaussian_3, -1.0, 0)
    return unsharp_image


def apply_clahe(calibration_data, equalized):
    # apply CLAHE
    # clip_limit = get_clahe_clip_limit(calibration_data)
    clip_limit = 4
    clahe = cv.createCLAHE(clipLimit=clip_limit, tileGridSize=(16, 16))
    clahed_image = clahe.apply(equalized)
    return clahed_image


def get_clahe_clip_limit(calibration_data):
    dark_light_range = 1.0 - calibration_data.get_dark_light_range()

    if dark_light_range <= 0.05:
        clip_limit = 0.05
    else:
        clip_limit = 35.0 * dark_light_range

    print("This calibration has a light/dark range of {}, will apply a CLAHE clip limit of {}".format(calibration_data.get_dark_light_range(), clip_limit))

    return clip_limit
