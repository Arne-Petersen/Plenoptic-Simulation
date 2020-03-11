# ------------------------------------------------------------------------
#    Class for reading/writing files
# ------------------------------------------------------------------------

import bpy
import csv

from os import listdir
from os.path import isfile, join

from . import calc

# ------------------------------------------------------------------------
#    Helper functions
# ------------------------------------------------------------------------

# turns a number string into a float
def str_to_float(string: str) -> float:
    string = string.strip()
    if not len(string):
        return 0.0
    return float(string)


# ------------------------------------------------------------------------
#    Camera GUI Parameters IO
# ------------------------------------------------------------------------

# writes camera parameters to csv file at specified location
def write_cam_params(filepath: str):
    cg = bpy.data.scenes[0].camera_generator

    # create/open file and save parameters to it
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='&', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['prop_objective_list', cg.prop_objective_list])
        writer.writerow(['prop_objective_scale', cg.prop_objective_scale])
        writer.writerow(['prop_vertex_count_radial', cg.prop_vertex_count_radial])
        writer.writerow(['prop_vertex_count_height', cg.prop_vertex_count_height])
        writer.writerow(['prop_aperture_blades', cg.prop_aperture_blades])
        writer.writerow(['prop_aperture_size', cg.prop_aperture_size])
        writer.writerow(['prop_aperture_angle', cg.prop_aperture_angle])
        writer.writerow(['prop_sensor_width', cg.prop_sensor_width])
        writer.writerow(['prop_sensor_height', cg.prop_sensor_height])
        writer.writerow(['prop_wavelength', cg.prop_wavelength])
        writer.writerow(['prop_focal_distance', cg.prop_focal_distance])
        writer.writerow(['prop_sensor_mainlens_distance', cg.prop_sensor_mainlens_distance])
        writer.writerow(['prop_mla_enabled', cg.prop_mla_enabled])
        writer.writerow(['prop_mla_type', cg.prop_mla_type])
        writer.writerow(['prop_microlens_diam', cg.prop_microlens_diam])
        writer.writerow(['prop_mla_sensor_dist', cg.prop_mla_sensor_dist])
        writer.writerow(['prop_three_ml_types', cg.prop_three_ml_types])
        writer.writerow(['prop_ml_type_1_f', cg.prop_ml_type_1_f])
        writer.writerow(['prop_ml_type_2_f', cg.prop_ml_type_2_f])
        writer.writerow(['prop_ml_type_3_f', cg.prop_ml_type_3_f])


# reads camera parameters from csv file at specified location
def read_cam_params(filepath: str):
    cg = bpy.data.scenes[0].camera_generator

    # open file and load parameters
    read_data = []
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='&')
        for row in reader:
            read_data.append(row)

    for read_property in read_data:
        # check property type and set accordingly casted values
        property_type = type(getattr(cg, read_property[0]))
        if property_type == float:
            setattr(cg, read_property[0], float(read_property[1]))
        elif property_type == int:
            setattr(cg, read_property[0], int(read_property[1]))
        elif property_type == bool:
            setattr(cg, read_property[0], bool(read_property[1]))
        else:
            setattr(cg, read_property[0], read_property[1])


# ------------------------------------------------------------------------
#    Lenses IO
# ------------------------------------------------------------------------

# reads lens parameters from csv file
def read_lens_file(filepath: str):
    objective = []
    reader = csv.reader(open(filepath, 'r'), delimiter=';')
    glass_data_known = True
    for row_idx, row in enumerate(reader):
        # ignore the first line since it contains a parameter description
        if row_idx < 1:
            continue
        ior = str_to_float(row[3])
        if ior == 0.0:
            ior = 1.0

        # get objective scale
        scale = bpy.data.scenes[0].camera_generator.prop_objective_scale

        # add leading zero for surface names
        name_part = "_"
        if len(objective) < 10:
            name_part = "_0"
        objective.append({
            'radius': scale * str_to_float(row[0]) / 1000,
            'thickness': scale * str_to_float(row[1]) / 1000,
            'material': row[2].strip(),
            'ior': ior,
            'ior_wavelength': ior,
            'ior_ratio': ior,
            'semi_aperture': scale * str_to_float(row[5]) / 1000,
            'position': 0.0,
            'name': "Surface"+name_part+str(len(objective)+1)+"_"+row[2].strip()
        })

        lens = objective[len(objective)-1]
        if lens['material'] != 'air' and lens['material'] != 'Air':
            if calc.ior(lens['material'], 0.5) == None:
                glass_data_known = False

    return objective, glass_data_known

# 
def load_lens_file(lens_directory):
    cg = bpy.data.scenes[0].camera_generator
    objective_id = int(cg.prop_objective_list[10:])
    # create a list of available lens files
    lensfiles = [f for f in listdir(lens_directory) if isfile(join(lens_directory, f))]
    lensfiles.sort()
    file = ''
    for counter, lensfile in enumerate(lensfiles):
        # check if file ends with .csv
        file_ending = lensfile[-3:]
        if file_ending == 'csv' and counter == objective_id:
            file = lensfile
            break
    # read lens parameters
    return read_lens_file(join(lens_directory,file))

# read dispersion parameters for Sellmeier and Cauchy equation from given files
def read_dispersion_data(dispersion_file: str):
    # Sellmeier type data:
    dispersion_data = {}
    with open(dispersion_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='&')
        for row in reader:
            dispersion_data[row[0]] = (float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]),float(row[7]))

    return dispersion_data

# ------------------------------------------------------------------------
#    Additional Blender resources IO
# ------------------------------------------------------------------------

# laods raw camera model and materials from given resource file
def load_basic_camera(path: str):
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection

    for filename in ['Camera Collection', 'Glass Material', 'MLA Hex Material', 'Calibration Pattern Material']:
        bpy.ops.wm.append(filename=filename, directory=f'{path}resources.blend/{filename.split()[-1]}')

    for materials in ['Glass Material', 'MLA Hex Material', 'MLA Rect Material', 'Calibration Pattern Material']:
        bpy.data.materials[materials].use_fake_user = True

    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Camera Collection']