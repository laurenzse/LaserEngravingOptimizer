# Laser Engraving Optimizer

Laser engraving often suffers from limitations imposed by hardware, materials, and laser control software, resulting in problems such as over-burned or over-bright engravings, as well as a limited dynamic range of engravings. The traditional manual process to solve this problem involves testing settings both in photo editing software and then on the laser cutter, which is tedious and material consuming.

The approach in this repository consists of a single manual step to identify the laser cutter settings that produce the clearest black. Using these settings, you engrave a software-generated calibration gauge on your desired material and scan it using a flatbed scanner. The software compares the values obtained from the scan with the original values processed and learns how the input lightness corresponds to its engraved counterpart. Using this calibration data, you can then optimize any photo for engraving in this constellation.

For more background information, please view this [post](https://laurenzseidel.com/projects/laser-engravings) on my personal web page.

## What you need

- a laser cutter/engraving
- engraving material for the initial calibration gauge and your photo
- for better results: a flatbed scanner

## Setup of the software

Install the requirements.

```
pip3 install -r requirements.txt
```


## Creating a calibration gauge

First, create the calibration gauge. Initially, the parameters used below should work well. As you gain more experience, you may want to try smaller gauges.

```
python create_calibration_image.py -h

>> Create a calibration gauge for engraving.
>> 
>> positional arguments:
>>   block_size  Height and width of one square calibration block.
>>   row_num     Number of rows of calibration blocks.
>>   column_num  Number of columns of calibration blocks.

python create_calibration_image.py 400 6 6

>> Output: calibration_gauge.png
```

![](./sample_images/calibration_image.png?raw=true)

Before engraving this calibration gauge, find the settings on your laser cutter/engraver that produce the clearest black for a full black PNG. The clearest black should be as dark as possible without producing too many burn marks.

Once you've found your settings, proceed with engraving the gauge on the material you'll be using for your photo.

## Optimize your photo for engraving

After engraving the gauge, scan it with a flatbed scanner. If you don't have access to one, a well-lit photo of the gauge from above should work. Crop the scan/photo to show only the gauge. Resize the resulting image to match the pixel dimensions of the original calibration gauge image.

Finally, run the script below.

```
python optimize_color_photo.py -h

>> Optimize a color photo for engraving.
>> 
>> positional arguments:
>>   block_size          Height and width of one square calibration block.
>>   row_num             Number of rows of calibration blocks.
>>   column_num          Number of columns of calibration blocks.
>>   scanned_gauge_path  File path of the scanned calibration gauge, the image
>>                       dimensions need to match the dimension of the generated
>>                       gauge image.
>>   photo_path          File path of the photo to optimize.

python optimize_color_photo.py 400 6 6 'scanned_gauge.png' 'your_photo.png'

>> Output: 
>> greyscale.png
>> greyscale_for_engraving.png
>> engraving_simulation_result.png
```

| original                                    | converted into greyscale                    | optimized for engraving                               | simulation result                           |
|---------------------------------------------|---------------------------------------------|-------------------------------------------------------|---------------------------------------------|
| ![](./sample_images/original.jpeg?raw=true) | ![](./sample_images/greyscale.jpg?raw=true) | ![](./sample_images/engraving_optimized.png?raw=true) | ![](./sample_images/simulated.png?raw=true) |

After engraving your photo, you may see something like this:

![](./sample_images/result.jpg?raw=true)

## Simulate result before engraving

You may want to play around with different photos or edits and test the resulting engraving. The script below produces a simulation of what a given image file would look like engraved, with no further edits.

```
python simulate_engraving.py -h

>> Optimize a color photo for engraving.
>> 
>> positional arguments:
>>   block_size          Height and width of one square calibration block.
>>   row_num             Number of rows of calibration blocks.
>>   column_num          Number of columns of calibration blocks.
>>   scanned_gauge_path  File path of the scanned calibration gauge, the image
>>                       dimensions need to match the dimension of the generated
>>                       gauge image.
>>   photo_path          File path of the photo to simulate engraving for.

python simulate_engraving.py 400 6 6 'scanned_gauge.png' 'your_photo.png'

>> Output: 
>> simulated.png
```