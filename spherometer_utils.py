import numpy as np
import csv
from scipy import ndimage

#%% Spherometer measurement algorithms


def process_spherometer_grid(csv_file,size_of_square=3,number_of_squares=10,pixels_per_square=10,spherometer_diameter=11.5,object_diameter=28,ideal_sag=0.076,mirror_center_x = 5, mirror_center_y = 5):
    
    #csv_file should be a 1D file representing values measured on a NxN grid
    
    #size_of_square, spherometer_diameter,object_diameter,ideal_sag are whatever units you like
    #Everything after that lives in tile space
    
    spher_radius = spherometer_diameter / 2 / size_of_square #units: tiles
    mirror_radius = object_diameter / 2 / size_of_square #units: tiles
        
    sigma = 3 #size in pixels for Gaussian blurring
    
    with open(csv_file, mode ='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = list(reader)            
    
    #Set up coordinates for tile space
    x = np.linspace(0,number_of_squares,number_of_squares*pixels_per_square)
    y = np.linspace(0,number_of_squares,number_of_squares*pixels_per_square)
    
    X,Y = np.meshgrid(x,y)
    
    #Initialize empty list that overlaying measurements will be attached to
    fill_data = [[] for i in range(X.size)]
    avg_data = list([0]*len(fill_data))
    list_data = []

    for num, sag in enumerate(data[0]):
        if sag != '0':  #Exclude the junk '0's that were added to the .csv. 
            x_pos = num % number_of_squares
            y_pos = np.floor(num / number_of_squares)

            distance_from_center = np.sqrt(np.power(X - x_pos, 2) + np.power(Y - y_pos, 2))
            spher_extent = distance_from_center < spher_radius

            #
            sample_height = sag
            list_data.append(float(sag))
            coord = np.where(spher_extent)

            for num, loc in enumerate(coord[0]):
                index = loc * X.shape[0] + coord[1][num]
                fill_data[index].append(float(sample_height))

    for num, val in enumerate(fill_data):
        if len(val) == 0:
            avg_data[num] = np.nan
        else:
            avg_data[num] = np.mean(val)

    reshaped_data = np.reshape(avg_data, X.shape)
    distance_from_center = np.sqrt(np.power(X - mirror_center_x, 2) + np.power(Y - mirror_center_y, 2))
    mirror_extent = distance_from_center < mirror_radius
    cropped_data = reshaped_data.copy()

    smoothed_data = ndimage.gaussian_filter(cropped_data, sigma, radius=3)
    smoothed_data[~mirror_extent] = np.nan

    cropped_data[~mirror_extent] = np.nan

    return cropped_data, smoothed_data, mirror_extent


def process_spherometer_concentric(csv_file, measurement_radius=[11.875, 8.5, 5.25, 2], spherometer_diameter=11.5,
                                   object_diameter=32, number_of_pixels=256, crop_clear_aperture=False,sag_unit='in'):
    spher_radius = spherometer_diameter / 2
    mirror_radius = object_diameter / 2
    overfill = 0
    gauss_filter_radius = 7
    sigma = 7  # size in pixels for Gaussian blurring
    ca_OD = 30
    ca_ID = 3

    with open(csv_file, mode='r', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        data = list(reader)

        # Set up coordinates for tile space
    x = np.linspace(-mirror_radius * (1 + overfill / 2), mirror_radius * (1 + overfill / 2),
                    int(number_of_pixels * (1 + overfill)))
    y = np.linspace(-mirror_radius * (1 + overfill / 2), mirror_radius * (1 + overfill / 2),
                    int(number_of_pixels * (1 + overfill)))

    X, Y = np.meshgrid(x, y)

    # Initialize empty list that overlaying measurements will be attached to
    fill_data = [[] for i in range(X.size)]
    avg_data = list([0] * len(fill_data))
    list_data = []

    for meas_index, measurement_set in enumerate(data):
        radius = measurement_radius[meas_index]
        meas_bool = [(x != "" and x != "0") for x in measurement_set]
        meas_data = [i for indx, i in enumerate(measurement_set) if meas_bool[indx]]

        theta = np.linspace(0, 2 * np.pi, len(meas_data), endpoint=False)

        for num, sag in enumerate(meas_data):
            try:
                x_pos = radius * np.cos(theta[num])
                y_pos = radius * np.sin(theta[num])

                distance_from_center = np.sqrt(np.power(X - x_pos, 2) + np.power(Y - y_pos, 2))
                spher_extent = distance_from_center < spher_radius
                #
                if sag_unit == 'in':
                    list_data.append(float(sag))
                elif sag_unit == 'mm':
                    list_data.append(float(sag))
                else:
                    return None, print('Sag unit ' + sag_unit + ' not recognized!')

                coord = np.where(spher_extent)

                for num, loc in enumerate(coord[0]):
                    index = loc * X.shape[0] + coord[1][num]
                    fill_data[index].append(float(sag))
            except ValueError:
                continue

    for num, val in enumerate(fill_data):
        if len(val) == 0:
            avg_data[num] = np.nan
        else:
            avg_data[num] = np.mean(val)

    reshaped_data = np.reshape(avg_data, X.shape)
    distance_from_center = np.sqrt(np.power(X, 2) + np.power(Y, 2))
    mirror_extent = distance_from_center < mirror_radius
    cropped_data = reshaped_data.copy()

    if not sag_unit == 'in':
        cropped_data = cropped_data / 25.4

    smoothed_data = ndimage.gaussian_filter(cropped_data, sigma, radius=gauss_filter_radius)

    if crop_clear_aperture:
        mirror_OD = distance_from_center < ca_OD/2
        mirror_ID = distance_from_center > ca_ID/2
        mirror_ID = distance_from_center > ca_ID/2
        mirror_extent = mirror_OD * mirror_ID
    else:
        mirror_extent = distance_from_center < mirror_radius

    smoothed_data[~mirror_extent] = np.nan
    cropped_data[~mirror_extent] = np.nan

    return cropped_data, smoothed_data, mirror_extent
