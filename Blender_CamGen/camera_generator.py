from os import listdir
from os.path import isfile, join

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper
import csv
import math

from . import data
from . import create
from . import update
from . test_camera_generator import test_main

from typing import Any, List, Dict, Tuple

# ------------------------------------------------------------------------
#    Helper functions
# ------------------------------------------------------------------------

# turns a number string into a float
def str_to_float(string: str) -> float:
    string = string.strip()
    if not len(string):
        return 0.0
    return float(string)

# deletes an object and all children
def delete_recursive(parent_object):
    children = parent_object.children
    for child in children:
        delete_recursive(child)
    bpy.data.objects.remove(parent_object)

# reads lens parameters from csv file
def parse_lensfile(lensfile):
    objective = []
    # get add-on folder path
    addon_directory = bpy.utils.user_resource(
        'SCRIPTS', "addons")+'/Blender_CamGen/'
    reader = csv.reader(open(addon_directory+'Lenses/' +
                             lensfile, 'r'), delimiter=';')
    data.glass_data_known = True
    for row_i, row in enumerate(reader):
        if row_i < 1:
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
            if data.calculate_ior(lens['material'], 0.5) == None:
                data.glass_data_known = False

    return objective


def get_lens_file(addon_directory):
    objective_id = int(
        bpy.data.scenes[0].camera_generator.prop_objective_list[10:])
    lensfiles = [f for f in listdir(
        addon_directory+'Lenses') if isfile(join(addon_directory+'Lenses', f))]
    lensfiles.sort()
    counter = 0
    file = ""
    for lensfile in lensfiles:
        # check if file end with .csv
        file_ending = lensfile[-3:]
        if file_ending == "csv" and counter == objective_id:
            file = lensfile
            break
        else:
            counter = counter+1
    if file == "":
        return {'FINISHED'}
    return parse_lensfile(file)


def delete_old_camera():
    # delete camera object and its children
    for object in bpy.data.objects:
        if object.name == 'Camera':
            delete_recursive(object)
            break
    # delete the camera collection
    for collection in bpy.data.collections:
        if collection.name == 'Camera Collection':
            bpy.data.collections.remove(
                bpy.data.collections['Camera Collection'])
            break
    # delete orphan meshes
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    # delete orthographic camera
    for camera in bpy.data.cameras:
        if camera.name == 'Orthographic Camera':
            bpy.data.cameras.remove(camera)
    # delete orphan materials
    for material in bpy.data.materials:
        if material.users == 0 or material.use_fake_user:
            bpy.data.materials.remove(material)
    # delete orphan node groups
    for group in bpy.data.node_groups:
        if group.users == 0:
            bpy.data.node_groups.remove(group)


def set_aperture_parameters(scene):
    # set opening rotation
    bpy.data.objects['Opening'].rotation_euler[0] = scene.camera_generator.prop_aperture_angle/180.0*math.pi

    if data.aperture_index != -1:
        # rescale opening according to currently set scaling
        opening_size = 2.0 * \
            data.objective[data.aperture_index]['semi_aperture']
        bpy.data.objects['Opening'].scale[1] = opening_size
        bpy.data.objects['Opening'].scale[2] = opening_size
        scene.camera_generator.prop_aperture_size = opening_size * 1000.0
        # rescale aperture plane to neighboring lens sizes
        aperture_plane_scale = 1.0
        if data.aperture_index == 0 and len(data.objective) > 1:
            aperture_plane_scale = 2.0 * \
                data.objective[data.aperture_index+1]['semi_aperture']
        elif data.aperture_index > 0 and data.aperture_index < len(data.objective)-1:
            aperture_plane_scale = 2.0 * \
                max(data.objective[data.aperture_index-1]['semi_aperture'],
                    data.objective[data.aperture_index+1]['semi_aperture'])
        elif data.aperture_index > 0 and data.aperture_index == len(data.objective)-1:
            aperture_plane_scale = 2.0 * \
                data.objective[data.aperture_index-1]['semi_aperture']

        bpy.data.objects['Aperture Plane'].scale[1] = aperture_plane_scale
        bpy.data.objects['Aperture Plane'].scale[2] = aperture_plane_scale
    else:
        size = 2.01 * data.objective[0]['semi_aperture']
        # rescale opening according to currently set scaling
        gui_size = scene.camera_generator.prop_aperture_size / 1000.0
        if size < gui_size:
            scene.camera_generator.prop_aperture_size = 0.99 * size * 1000.0
        bpy.data.objects['Opening'].scale[1] = scene.camera_generator.prop_aperture_size/1000.0
        bpy.data.objects['Opening'].scale[2] = scene.camera_generator.prop_aperture_size/1000.0
        data.semi_aperture = scene.camera_generator.prop_aperture_size/1000.0
        # rescale aperture plane to largest lens size
        bpy.data.objects['Aperture Plane'].scale[1] = size
        bpy.data.objects['Aperture Plane'].scale[2] = size


def set_MLA_parameters(data, scene, self, context):
    last_lens = data.objective[len(data.objective)-1]
    bpy.data.objects['Sensor'].location[0] = last_lens['position'] + \
        math.fabs(last_lens['radius'])+last_lens['thickness']
    scene.camera_generator.prop_sensor_mainlens_distance = bpy.data.objects[
        'Sensor'].location[0] * 1000.0

    min_ml_focal_length = 0.001 * min(scene.camera_generator.prop_ml_type_1_f,
                                      scene.camera_generator.prop_ml_type_2_f, scene.camera_generator.prop_ml_type_3_f)
    bpy.data.objects['MLA'].location[0] = last_lens['position']+math.fabs(
        last_lens['radius'])+last_lens['thickness'] - (0.9 * min_ml_focal_length)
    scene.camera_generator.prop_mla_sensor_dist = 0.9 * min_ml_focal_length * 1000.0

    update.mla_type(self, context)
    update.sensor(self, context)
    update.microlens_diam(self, context)
    update.ml_type_1_f(self, context)
    update.ml_type_2_f(self, context)
    update.ml_type_3_f(self, context)

# imports raw camera model and materials from given resource file
def import_basic_camera(path: str):
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection

    for filename in ['Camera Collection', 'Glass Material', 'MLA Hex Material', 'Calibration Pattern Material']:
        bpy.ops.wm.append(
            filename=filename, directory=f'{path}resources.blend/{filename.split()[-1]}')

    for materials in ['Glass Material', 'MLA Hex Material', 'MLA Rect Material', 'Calibration Pattern Material']:
        bpy.data.materials[materials].use_fake_user = True

    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[
        'Camera Collection']


# ------------------------------------------------------------------------
#    Camera creation operator
# ------------------------------------------------------------------------

class CAMGEN_OT_CreateCam(bpy.types.Operator):
    bl_idname = "camgen.createcam"
    bl_label = "Generate Camera"
    bl_description = "Generate a camera model with the specified parameters"

    def execute(self, context):

        # set add-on directory
        addon_directory = bpy.utils.user_resource(
            'SCRIPTS', "addons")+'/Blender_CamGen/'
        scene = bpy.data.scenes[0]

        # set cycles parameters, i.e. number of bounces, and deactivate clamping
        data.set_cycles_parameters(scene)

        # get number of vertices for lens creation
        vertex_count_height = scene.camera_generator.prop_vertex_count_height
        vertex_count_radial = scene.camera_generator.prop_vertex_count_radial

        # read objective paramters
        data.objective = get_lens_file(addon_directory)

        # camera setup: calculate IORs ratios and aperture position
        data.calculate_shader_iors()
        data.calculate_aperture()

        # delete old camera and calibration pattern
        delete_old_camera()
        
        # load basic camera model and materials from resources file
        import_basic_camera(addon_directory)

        # set orthographic camera as render camera
        scene.camera = bpy.data.objects['Orthographic Camera']

        # create lenses and save the outer vertices for housing creation
        outer_vertices, outer_lens_index = create.lenses(vertex_count_height, vertex_count_radial, data.objective)

        # create housing and aperture
        create.housing(outer_vertices, outer_lens_index, vertex_count_radial)
        create.aperture()

        # setup the user defined aperture, i.e. number of blades, scaling and rotation 
        set_aperture_parameters(scene)

        # setup the user defined MLA parameters
        set_MLA_parameters(data, scene, self, context)

        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Calibration pattern creation operator
# ------------------------------------------------------------------------

class CAMGEN_OT_CreateCalibrationPattern(bpy.types.Operator):
    bl_idname = "camgen.createcalibrationpattern"
    bl_label = "Generate Calibration Pattern"
    bl_description = "Generate a calibration pattern approximately located at the focus plane."

    def execute(self, context):

        # delete old calibration pattern
        for object in bpy.data.objects:
            if object.name == 'Calibration Pattern':
                delete_recursive(object)
                break
        # delete orphan meshes
        for mesh in bpy.data.meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        # create new plane
        bpy.ops.mesh.primitive_plane_add(
            size=1, rotation=(0, 0.5*3.14159, 0), location=(0, 0, 0))
        bpy.ops.object.transform_apply()
        calibration_pattern = bpy.context.active_object
        calibration_pattern.name = 'Calibration Pattern'
        # set material

        calibration_pattern.data.materials.append(
            bpy.data.materials['Calibration Pattern Material'])
        calibration_pattern.location[0] = - \
            bpy.data.scenes[0].camera_generator.prop_focal_distance / 100.0

        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Unit test execution operator
# ------------------------------------------------------------------------

class CAMGEN_OT_RunTests(bpy.types.Operator):
    bl_idname = "camgen.runtests"
    bl_label = "Run tests"
    bl_description = "Runs tests"

    def execute(self, context):
        test_main()
        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Camera config save and load operations
# ------------------------------------------------------------------------

class CAMGEN_OT_SaveConfig(bpy.types.Operator, ExportHelper):
    bl_idname = "camgen.saveconfig"
    bl_label = "Save Config"
    bl_description = "Save the camera configuration including MLA properties."

    filename_ext = ".csv"

    def execute(self, context):
        cg = bpy.data.scenes[0].camera_generator

        # the export helper asks the user for saving file location
        filepath = self.filepath

        # create/open file and save parameters to it
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';',
                                quotechar='&', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['prop_objective_list', cg.prop_objective_list])
            writer.writerow(['prop_objective_scale', cg.prop_objective_scale])
            writer.writerow(['prop_vertex_count_radial',
                             cg.prop_vertex_count_radial])
            writer.writerow(['prop_vertex_count_height',
                             cg.prop_vertex_count_height])
            writer.writerow(['prop_aperture_blades', cg.prop_aperture_blades])
            writer.writerow(['prop_aperture_size', cg.prop_aperture_size])
            writer.writerow(['prop_aperture_angle', cg.prop_aperture_angle])
            writer.writerow(['prop_sensor_width', cg.prop_sensor_width])
            writer.writerow(['prop_sensor_height', cg.prop_sensor_height])
            writer.writerow(['prop_wavelength', cg.prop_wavelength])
            writer.writerow(['prop_focal_distance', cg.prop_focal_distance])
            writer.writerow(['prop_sensor_mainlens_distance',
                             cg.prop_sensor_mainlens_distance])
            writer.writerow(['prop_mla_enabled', cg.prop_mla_enabled])
            writer.writerow(['prop_mla_type', cg.prop_mla_type])
            writer.writerow(['prop_microlens_diam', cg.prop_microlens_diam])
            writer.writerow(['prop_mla_sensor_dist', cg.prop_mla_sensor_dist])
            writer.writerow(['prop_three_ml_types', cg.prop_three_ml_types])
            writer.writerow(['prop_ml_type_1_f', cg.prop_ml_type_1_f])
            writer.writerow(['prop_ml_type_2_f', cg.prop_ml_type_2_f])
            writer.writerow(['prop_ml_type_3_f', cg.prop_ml_type_3_f])

        return {'FINISHED'}

class CAMGEN_OT_LoadConfig(bpy.types.Operator, ImportHelper):
    bl_idname = "camgen.loadconfig"
    bl_label = "Load Config"
    bl_description = "Load the camera configuration including MLA properties."

    filename_ext = ".csv"

    def execute(self, context):
        cg = bpy.data.scenes[0].camera_generator

        # the import helper asks the user for file location
        filepath = self.filepath

        # open file and load parameters
        read_data = []
        with open(filepath, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='&')
            for row in reader:
                read_data.append(row)

        counter = 0
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

            counter = counter + 1
            if counter == 4:
                # create camera
                bpy.ops.camgen.createcam()

        return {'FINISHED'}
