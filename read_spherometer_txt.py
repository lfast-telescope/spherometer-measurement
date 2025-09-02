import numpy as np
import csv
import os

def convert_txt_to_csv(txt_path,csv_path=None,num_measurement_rings = 4):
    val_holder = [[] for i in range(num_measurement_rings)]

    file = open(txt_path,'r',encoding='utf-8')

    while True:
        line = file.readline()
        if not line:
            break
        split_line = line.split('-')
        for i in range(len(split_line)):
            split_line[i] = split_line[i].replace('”','"')
        bool_line = ['"' in segment for segment in split_line]
        reduced_line = np.array(split_line)[np.array(bool_line)]

        vals = [entry.split('"')[0] for entry in reduced_line]
        print(vals)
        for num,val in enumerate(vals):
            val_holder[num].append(val)
    file.close()

    if csv_path:
        with open(csv_path,'w',newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(val_holder)
    else:
        return val_holder

path = 'C:/Users/warrenbfoster/OneDrive - University of Arizona/Documents/LFAST/mirrors/M6/'

for file in os.listdir(path):
    if file.endswith('.txt'):
        file_name = file.split('.')[0]
        val_holder = convert_txt_to_csv(path + file, path + file_name + '.csv')