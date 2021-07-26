import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper
import math

from . import data
from . import calc
from . import create
from . import delete
from . import io
from . import update
from . test_camera_generator import test_main

from typing import Any, List, Dict, Tuple

# ------------------------------------------------------------------------
#    Helper functions
# ------------------------------------------------------------------------

def set_aperture_parameters(scene):
    # set opening rotation
    bpy.data.objects['Opening'].rotation_euler[0] = scene.camera_generator.prop_aperture_angle/180.0*math.pi

    if data.aperture_index != -1:
        # rescale opening according to currently set scaling
        if data.use_gui_data:
            opening_size = min(2.0 * data.objective[data.aperture_index]['semi_aperture'], scene.camera_generator.prop_aperture_size / 1000.0)
        else:
            opening_size = 2.0 * data.objective[data.aperture_index]['semi_aperture']
        bpy.data.objects['Opening'].scale[1] = opening_size
        bpy.data.objects['Opening'].scale[2] = opening_size
        scene.camera_generator.prop_aperture_size = opening_size * 1000.0
        # rescale aperture plane to neighboring lens sizes
        aperture_plane_scale = 1.0
        if data.aperture_index == 0 and len(data.objective) > 1:
            aperture_plane_scale = 2.0 * data.objective[data.aperture_index+1]['semi_aperture']
        elif data.aperture_index > 0 and data.aperture_index < len(data.objective)-1:
            aperture_plane_scale = 2.0 * max(data.objective[data.aperture_index-1]['semi_aperture'], data.objective[data.aperture_index+1]['semi_aperture'])
        elif data.aperture_index > 0 and data.aperture_index == len(data.objective)-1:
            aperture_plane_scale = 2.0 * data.objective[data.aperture_index-1]['semi_aperture']

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


def set_MLA_parameters(scene, self, context):
    cg = bpy.data.scenes[0].camera_generator

    # if previous config is loaded from file, the GUI parameters are used for MLA and sensor position
    if data.use_gui_data:
        bpy.data.objects['Sensor'].location[0] = cg.prop_sensor_mainlens_distance / 1000.0
        bpy.data.objects['MLA'].location[0] = (cg.prop_sensor_mainlens_distance - cg.prop_mla_sensor_dist) / 1000.0

    # otherwise these parameters are calculated
    else:
        last_lens = data.objective[len(data.objective)-1]
        bpy.data.objects['Sensor'].location[0] = last_lens['position'] + math.fabs(last_lens['radius'])+last_lens['thickness']
        cg.prop_sensor_mainlens_distance = bpy.data.objects['Sensor'].location[0] * 1000.0

        min_ml_focal_length = 0.001 * min(cg.prop_ml_type_1_f,cg.prop_ml_type_2_f, cg.prop_ml_type_3_f)
        bpy.data.objects['MLA'].location[0] = last_lens['position']+math.fabs(last_lens['radius'])+last_lens['thickness'] - (0.9 * min_ml_focal_length)
        cg.prop_mla_sensor_dist = 0.9 * min_ml_focal_length * 1000.0

    # update models and shaders
    update.mla_type(self, context)
    update.sensor(self, context)
    update.microlens_diam(self, context)
    update.ml_type_1_f(self, context)
    update.ml_type_2_f(self, context)
    update.ml_type_3_f(self, context)
    update.three_ml_types(self,context)
    update.mla_enabled(self, context)



# applies cycles settings
def set_cycles_parameters(scene: bpy.types.Scene):
    global cycles_settings
    for setting in data.cycles_settings:
        setattr(scene.cycles, setting, data.cycles_settings[setting])


# ------------------------------------------------------------------------
#    Camera creation operator
# ------------------------------------------------------------------------

class CAMGEN_OT_CreateCam(bpy.types.Operator):
    bl_idname = "camgen.createcam"
    bl_label = "Generate Camera"
    bl_description = "Generate a camera model with the specified parameters"

    def execute(self, context):
        scene = bpy.data.scenes[0]

        # set cycles as render engine (other engines have not been tested)
        scene.render.engine='CYCLES'

        # set cycles parameters, i.e. number of bounces, and deactivate clamping
        set_cycles_parameters(scene)

        # get number of vertices and patch size for lens creation
        lens_patch_size = scene.camera_generator.prop_lens_patch_size / 1000
        vertex_count_height = scene.camera_generator.prop_vertex_count_height
        vertex_count_radial = scene.camera_generator.prop_vertex_count_radial

        # read objective paramters
        data.objective, data.glass_data_known = io.load_lens_file(data.lens_directory)
        # camera setup: calculate IORs ratios and aperture position
        data.objective = calc.shader_iors(data.objective)
        data.objective, data.aperture_index = calc.aperture(data.objective)

        # delete old camera and calibration pattern
        delete.old_camera()
        
        # load basic camera model and materials from resources file
        io.load_basic_camera(data.addon_directory)

        # set orthographic camera as render camera
        scene.camera = bpy.data.objects['Orthographic Camera']

        # create lenses and save the outer vertices for housing creation
        outer_vertices, outer_lens_index = create.lenses(lens_patch_size, vertex_count_height, vertex_count_radial, data.objective)

        # create housing and aperture
        create.housing(outer_vertices, outer_lens_index, data.num_radial_housing_vertices)
        create.aperture()

        # setup the user defined aperture, i.e. number of blades, scaling and rotation 
        set_aperture_parameters(scene)

        # setup the user defined MLA parameters
        set_MLA_parameters(scene, self, context)

        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Calibration pattern operators
# ------------------------------------------------------------------------

# deletes old calibration patterns and creates a new one at specified position
class CAMGEN_OT_CreateCalibrationPattern(bpy.types.Operator):
    bl_idname = "camgen.createcalibrationpattern"
    bl_label = "Generate Calibration Pattern"
    bl_description = "Generate a calibration pattern approximately located at the focus plane."

    def execute(self, context):
        # delete old calibration pattern
        delete.old_calibration_pattern()
        # create the new calibration pattern
        create.calibration_pattern()

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

# opens file dialog to chose save file and writes the camera setup to that file
class CAMGEN_OT_SaveConfig(bpy.types.Operator, ExportHelper):
    bl_idname = "camgen.saveconfig"
    bl_label = "Save Config"
    bl_description = "Save the camera configuration including MLA properties."
    filename_ext = ".csv"

    def execute(self, context):
        cg = bpy.data.scenes[0].camera_generator
        # the export helper asks the user for saving file location
        filepath = self.filepath
        # save camera parameters to file
        io.write_cam_params(filepath)

        return {'FINISHED'}

# opens file dialog to chose config file from, loads the camera config from chosen file and creates the camera
class CAMGEN_OT_LoadConfig(bpy.types.Operator, ImportHelper):
    bl_idname = "camgen.loadconfig"
    bl_label = "Load Config"
    bl_description = "Load the camera configuration including MLA properties."
    filename_ext = ".csv"

    def execute(self, context):
        cg = bpy.data.scenes[0].camera_generator
        # the import helper asks the user for file location
        filepath = self.filepath
        # read the camera parameters from csv file
        io.read_cam_params(filepath)
        # create camera using the GUI setup
        data.use_gui_data = True
        bpy.ops.camgen.createcam()
        data.use_gui_data = False

        return {'FINISHED'}
