import bpy
import math
import mathutils

from os import listdir
from os.path import isfile, join

from . raytracer import sensor_position_for_distance

from . import calc
from . import create
from . import data

# ------------------------------------------------------------------------
#    Helper functions
# ------------------------------------------------------------------------

# scans the lens folder for csv files containing lens data. The files are then listed in the objective list selector.
def find_items(self, context):
    # check if list was already created
    if (not data.objective_list_created):
        # get all files in the lenses dir
        lensfiles = [f for f in listdir(data.lens_directory) if isfile(join(data.lens_directory, f))]
        lensfiles.sort()
        result = ()
        counter = 0
        for lensfile in lensfiles:
            # check if file ends with .csv
            file_ending = lensfile[-3:]
            if file_ending == "csv":
                # find "_" which separates lens name and author/company name
                separator = lensfile.find("_")
                # add objective entry to list
                result = result + (('OBJECTIVE_'+str(counter),lensfile[:separator],lensfile),)
                counter = counter + 1
        data.objective_list_created = True
        data.objective_list = result
    return data.objective_list

# ------------------------------------------------------------------------
#    Update functions
# ------------------------------------------------------------------------

def objective_scale(self, context):
    return

def lens_creation_method(self,context):
    data.lens_creation_method = bpy.data.scenes[0].camera_generator.prop_lens_creation_method

def sensor(self, context):
    cg = bpy.data.scenes[0].camera_generator
    # rescale diffusor plane
    bpy.data.objects['Diffusor Plane'].scale[1] = cg.prop_sensor_width / 1000.0
    bpy.data.objects['Diffusor Plane'].scale[2] = cg.prop_sensor_height / 1000.0
    # adjust render resolution assuming square pixels
    bpy.data.scenes[0].render.resolution_y = bpy.data.scenes[0].render.resolution_x / bpy.data.objects['Diffusor Plane'].scale[1] * bpy.data.objects['Diffusor Plane'].scale[2]
    
    # rescale orthographic camera
    bpy.data.cameras['Orthographic Camera'].ortho_scale = max(cg.prop_sensor_width, cg.prop_sensor_height) / 1000.0
    
    # rescale MLA to sensor size
    bpy.data.objects['Two Plane Model'].scale[1] = cg.prop_sensor_width / (1000.0 * bpy.data.objects['Two Plane Model'].dimensions[1])
    bpy.data.objects['Two Plane Model'].scale[2] = cg.prop_sensor_height / (1000.0 * bpy.data.objects['Two Plane Model'].dimensions[2])

    temp_object = bpy.context.active_object
    bpy.context.active_object.select_set(False)
    bpy.data.objects['Two Plane Model'].select_set(True)
    bpy.ops.object.transform_apply(location = False, scale = True, rotation = False)
    bpy.data.objects['Two Plane Model'].select_set(False)
    temp_object.select_set(True)

    bpy.data.materials['MLA Hex Material'].node_tree.nodes['MLA Width in mm'].outputs['Value'].default_value = cg.prop_sensor_width
    bpy.data.materials['MLA Hex Material'].node_tree.nodes['MLA Height in mm'].outputs['Value'].default_value = cg.prop_sensor_height
    bpy.data.materials['MLA Rect Material'].node_tree.nodes['MLA Width in mm'].outputs['Value'].default_value = cg.prop_sensor_width
    bpy.data.materials['MLA Rect Material'].node_tree.nodes['MLA Height in mm'].outputs['Value'].default_value = cg.prop_sensor_height

def sensor_width(self, context):
    sensor(self,context)

def sensor_height(self, context):
    sensor(self,context)

def sensor_mainlens_distance(self, context):
    cg = bpy.data.scenes[0].camera_generator
    # move sensor
    bpy.data.objects['Sensor'].location[0] = cg.prop_sensor_mainlens_distance / 1000.0
    # move MLA
    bpy.data.objects['MLA'].location[0] = cg.prop_sensor_mainlens_distance / 1000.0 - cg.prop_mla_sensor_dist / 1000.0

def aperture_blades(self, context):
    create.aperture()

def aperture_size(self, context):
    cg = bpy.data.scenes[0].camera_generator
    bpy.data.objects['Opening'].scale[1] = cg.prop_aperture_size / 1000.0
    bpy.data.objects['Opening'].scale[2] = cg.prop_aperture_size / 1000.0
    data.semi_aperture = cg.prop_aperture_size / 1000.0

def aperture_angle(self, context):
    bpy.data.objects['Opening'].rotation_euler[0] = bpy.data.scenes[0].camera_generator.prop_aperture_angle/180.0*math.pi

def wavelength(self,context):
    if data.glass_data_known == False:
        # reset wavelength since not all glass materials are known
        if abs(bpy.data.scenes[0].camera_generator.prop_wavelength - 587.6) > 0.01:
            bpy.data.scenes[0].camera_generator.prop_wavelength = 587.6
        return

    # check whether objective is available
    if len(data.objective) == 0:
        return
    else:
        wavelength_um = bpy.data.scenes[0].camera_generator.prop_wavelength/1000.0
        iors = []
        for lens in data.objective:
            if lens['material'] == 'air' or lens['material'] == 'Air':
                iors.append(1.0)
            else:
                new_ior = calc.ior(lens['material'], wavelength_um)
                if new_ior == None:
                    iors.clear()
                    break
                else:
                    iors.append(new_ior)
        
        if len(iors) > 0:
            counter = 0
            for lens in data.objective:
                lens['ior_wavelength'] = iors[counter]
                counter = counter + 1

            for i in range(len(data.objective)-1, 0, -1):
                data.objective[i]['ior_ratio'] = data.objective[i-1]['ior_wavelength']/data.objective[i]['ior_wavelength']
            data.objective[0]['ior_ratio'] = 1.0/data.objective[0]['ior_wavelength']

            for lens in data.objective:
                for object in bpy.data.objects:
                    if object.name == lens['name']:
                        bpy.data.materials[object.material_slots[0].name].node_tree.nodes['IOR'].outputs[0].default_value = lens['ior_ratio']

def fresnel_reflection_enabled(self,context):
    # check whether objective is available
    if (len(data.objective) == 0) or (not self.prop_fresnel_transmission_enabled):
        return
    else:
        for lens in data.objective:
                for object in bpy.data.objects:
                    if object.name == lens['name']:
                        material = bpy.data.materials[object.material_slots[0].name]
                        if self.prop_fresnel_reflection_enabled:
                            material.node_tree.nodes['Reflection BSDF'].inputs['Color'].default_value[0]=1
                            material.node_tree.nodes['Reflection BSDF'].inputs['Color'].default_value[1]=1
                            material.node_tree.nodes['Reflection BSDF'].inputs['Color'].default_value[2]=1
                        else:
                            material.node_tree.nodes['Reflection BSDF'].inputs['Color'].default_value[0]=0
                            material.node_tree.nodes['Reflection BSDF'].inputs['Color'].default_value[1]=0
                            material.node_tree.nodes['Reflection BSDF'].inputs['Color'].default_value[2]=0

def fresnel_transmission_enabled(self,context):
    # check whether objective is available
    if len(data.objective) == 0:
        return
    else:
        for lens in data.objective:
                for object in bpy.data.objects:
                    if object.name == lens['name']:
                        material = bpy.data.materials[object.material_slots[0].name]
                        if self.prop_fresnel_transmission_enabled:
                            material.node_tree.links.new(material.node_tree.nodes['Mix Shader'].outputs[0],material.node_tree.nodes['Material Output'].inputs[0])
                        else:
                            material.node_tree.links.new(material.node_tree.nodes['Refraction BSDF'].outputs[0],material.node_tree.nodes['Material Output'].inputs[0])

    fresnel_reflection_enabled(self,context)

def mla_enabled(self, context):
    hide = not bpy.data.scenes[0].camera_generator.prop_mla_enabled
    if 'Two Plane Model' in bpy.data.objects:
        bpy.data.objects['Two Plane Model'].hide_render = hide
        bpy.data.objects['Two Plane Model'].hide_viewport = hide
    if 'MLA' in bpy.data.objects:
        bpy.data.objects['MLA'].hide_render = hide
        bpy.data.objects['MLA'].hide_viewport = hide
    data.use_mla = not hide
    if data.use_mla:
        sensor(self, context)

def microlens_diam(self, context):
    # set microlens size
    bpy.data.materials['MLA Hex Material'].node_tree.nodes['Microlens Diameter in um'].outputs['Value'].default_value = bpy.data.scenes[0].camera_generator.prop_microlens_diam
    bpy.data.materials['MLA Rect Material'].node_tree.nodes['Microlens Diameter in um'].outputs['Value'].default_value = bpy.data.scenes[0].camera_generator.prop_microlens_diam

def mla_sensor_dist(self, context):
    bpy.data.objects['MLA'].location[0] = bpy.data.objects['Sensor'].location[0] - bpy.data.scenes[0].camera_generator.prop_mla_sensor_dist / 1000.0

def ml_type_1_f(self, context):
    cg = bpy.data.scenes[0].camera_generator
    # get currently active MLA type
    is_hex_mla = (cg.prop_mla_type == 'HEX')
    if is_hex_mla:
        bpy.data.materials['MLA Hex Material'].node_tree.nodes['Lens 1 f'].outputs['Value'].default_value = cg.prop_ml_type_1_f
        if not cg.prop_three_ml_types:
            cg.prop_ml_type_2_f = cg.prop_ml_type_1_f
            cg.prop_ml_type_3_f = cg.prop_ml_type_1_f
            bpy.data.materials['MLA Hex Material'].node_tree.nodes['Lens 2 f'].outputs['Value'].default_value = cg.prop_ml_type_1_f
            bpy.data.materials['MLA Hex Material'].node_tree.nodes['Lens 3 f'].outputs['Value'].default_value = cg.prop_ml_type_1_f
    else:
        bpy.data.materials['MLA Rect Material'].node_tree.nodes['Microlens f'].outputs['Value'].default_value = cg.prop_ml_type_1_f
        cg.prop_ml_type_2_f = cg.prop_ml_type_1_f
        cg.prop_ml_type_3_f = cg.prop_ml_type_1_f

def ml_type_2_f(self, context):
    # get currently active MLA type
    cg = bpy.data.scenes[0].camera_generator
    is_hex_mla = (cg.prop_mla_type == 'HEX')
    if is_hex_mla:
        if cg.prop_three_ml_types:
            bpy.data.materials['MLA Hex Material'].node_tree.nodes['Lens 2 f'].outputs['Value'].default_value = cg.prop_ml_type_2_f
        else:
            bpy.data.materials['MLA Hex Material'].node_tree.nodes['Lens 2 f'].outputs['Value'].default_value = cg.prop_ml_type_1_f
    else:
        cg.prop_ml_type_2_f = cg.prop_ml_type_1_f

def ml_type_3_f(self, context):
    # get currently active MLA type
    cg = bpy.data.scenes[0].camera_generator
    is_hex_mla = (cg.prop_mla_type == 'HEX')
    if is_hex_mla:
        if cg.prop_three_ml_types:
            bpy.data.materials['MLA Hex Material'].node_tree.nodes['Lens 3 f'].outputs['Value'].default_value = cg.prop_ml_type_3_f
        else:
            bpy.data.materials['MLA Hex Material'].node_tree.nodes['Lens 3 f'].outputs['Value'].default_value = cg.prop_ml_type_1_f
    else:
        cg.prop_ml_type_3_f = cg.prop_ml_type_1_f

def three_ml_types(self, context):
    cg = bpy.data.scenes[0].camera_generator
    if not cg.prop_three_ml_types:
        cg.prop_ml_type_2_f = cg.prop_ml_type_1_f
        cg.prop_ml_type_3_f = cg.prop_ml_type_1_f
    else:
        if cg.prop_mla_type == 'RECT':
            cg.prop_three_ml_types = False

def mla_type(self, context):
    cg = bpy.data.scenes[0].camera_generator
    # get currently active MLA type
    is_hex_mla = (cg.prop_mla_type == 'HEX')
    # set materials
    if is_hex_mla:
        bpy.data.objects['Two Plane Model'].data.materials[0] = bpy.data.materials['MLA Hex Material']
    else:
        bpy.data.objects['Two Plane Model'].data.materials[0] = bpy.data.materials['MLA Rect Material']
        ml_type_1_f(self,context)
        cg.prop_three_ml_types = False
        three_ml_types(self,context)

def focal_distance(self, context):
    cg = bpy.data.scenes[0].camera_generator
    # calculate the new sensor distance
    sensor_position = sensor_position_for_distance(cg.prop_focal_distance / 100.0)
    if sensor_position != -1.0:
        cg.prop_sensor_mainlens_distance = sensor_position * 1000.0
        sensor_mainlens_distance(self, context)
    # set the calibration pattern to new distance
    if 'Calibration Pattern' in bpy.data.objects:
        calibration_pattern = bpy.data.objects['Calibration Pattern']
        translation = mathutils.Vector((-bpy.data.scenes[0].camera_generator.prop_focal_distance / 100.0, 0.0, 0.0))
        translation.rotate(calibration_pattern.rotation_euler) 
        calibration_pattern.location = translation
        print(translation)