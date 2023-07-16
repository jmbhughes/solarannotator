from solarannotator.io import ImageSet, ThematicMap
from datetime import datetime, timedelta
import numpy as np


def create_mask(radius, image_size):
    """
    Inputs:
        - Radius: Radius (pixels) within which a certain theme should be assigned
        - Image size: tuple of (x, y) size (pixels) that represents size of image
    """
    # Define image center
    center_x = (image_size[0] / 2) - 0.5
    center_y = (image_size[1] / 2) - 0.5

    # Create mesh grid of image coordinates
    xm, ym = np.meshgrid(np.linspace(0, image_size[0] - 1, num=image_size[0]),
                         np.linspace(0, image_size[1] - 1, num=image_size[1]))

    # Center each mesh grid (zero at the center)
    xm_c = xm - center_x
    ym_c = ym - center_y

    # Create array of radii
    rad = np.sqrt(xm_c ** 2 + ym_c ** 2)

    # Create empty mask of same size as the image
    mask = np.zeros((image_size[0], image_size[1]))

    # Apply the mask as true for anything within a radius
    mask[(rad < radius)] = 1

    # Return the mask
    return mask.astype('bool')


def create_thmap_template(image_set, limb_thickness=10):
    """
    Input: Image set object as input, and limb thickness in pixels
    Output: thematic map object
    Process:
        - Get the solar radius with predefined function
        - Create empty thematic map
        - Define concentric layers separated by solar radius + limb thickness, and create thmap
        - Return the thematic map object

    Note copied from Alison Jarvis
    """

    # Get the solar radius with class function
    solar_radius = image_set.get_solar_radius()

    # Define end of disk and end of limb radii
    disk_radius = solar_radius - (limb_thickness / 2)
    limb_radius = solar_radius + (limb_thickness / 2)

    # Create concentric layers for disk, limb, and outer space
    # First template layer, outer space (value 1) with same size as composites
    imagesize = np.shape(image_set['171'].data)
    thmap_data = np.ones(imagesize)
    # Mask out the limb (value 8)
    limb_mask = create_mask(limb_radius, imagesize)
    thmap_data[limb_mask] = 8
    # Mask out the disk with quiet sun (value 7)
    qs_mask = create_mask(disk_radius, imagesize)
    thmap_data[qs_mask] = 7

    # Create a thematic map object with this data and return it
    theme_mapping = {1: 'outer_space', 3: 'bright_region', 4: 'filament', 5: 'prominence', 6: 'coronal_hole',
                     7: 'quiet_sun', 8: 'limb', 9: 'flare'}
    thmap_template = ThematicMap(thmap_data, {'DATE-OBS': image_set['171'].header['DATE-OBS']}, theme_mapping)

    # Return the thematic map object
    return thmap_template
