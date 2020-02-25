import bpy

from bpy.props import (BoolProperty,IntProperty,FloatProperty,EnumProperty)
from bpy.types import (Panel,Menu,Operator,PropertyGroup)

from . import update


# ------------------------------------------------------------------------
#    Properties
# ------------------------------------------------------------------------

class CAMGEN_Properties(PropertyGroup):

    prop_objective_list: EnumProperty(
        name = "",
        description = "Choose an objective.",
        items = update.find_items
        )

    prop_objective_scale: FloatProperty(
        name = "",
        description = "Scaling of the objective - press 'Create Camera Model' after adjusting the scale in order to generate a new model.",
        default = 1.0,
        min = 0.001,
        max = 1000.0,
        update = update.objective_scale
        )

    prop_vertex_count_radial: IntProperty(
        name = "",
        description="Latitudinal/radial number of vertices used for lens creation.",
        default = 32,
        min = 3,
        max = 1000
        )

    prop_vertex_count_height: IntProperty(
        name = "",
        description="Longitudinal number of vertices used for lens creation.",
        default = 36,
        min = 3,
        max = 1000
        )

    prop_sensor_width: FloatProperty(
        name = "",
        description = "Sensor Width in mm.",
        default = 10.0,
        min = 0.1,
        max = 1000.0,
        update = update.sensor_width
        )
    
    prop_sensor_height: FloatProperty(
        name = "",
        description = "Sensor Height in mm.",
        default = 10.0,
        min = 0.1,
        max = 1000.0,
        update = update.sensor_height
        )

    prop_sensor_mainlens_distance: FloatProperty(
        name = "",
        description = "Objective-Sensor Distance in mm",
        default = 100.0,
        min = 0.1,
        max = 10000.0,
        update = update.sensor_mainlens_distance
        )

    prop_aperture_blades: IntProperty(
        name = "",
        description="Number of Aperture Blades.",
        default = 6,
        min = 3,
        max = 100,
        update = update.aperture_blades
        )

    prop_aperture_size: FloatProperty(
        name = "",
        description = "Aperture opening size in mm",
        default = 100.0,
        min = 0.1,
        max = 10000.0,
        update = update.aperture_size
        )
    
    prop_aperture_angle: FloatProperty(
        name = "",
        description = "Aperture angle in degree",
        default = 0.0,
        min = 0.0,
        max = 180.0,
        update = update.aperture_angle
        )

    prop_wavelength: FloatProperty(
        name = "",
        description = "Wavelength in nm used for IOR calculation",
        default = 587.6,
        min = 380.0,
        max = 780.0,
        update = update.wavelength
        )

    prop_mla_enabled: BoolProperty(
        name="",
        description="Activate if microlens array should be used.",
        default = True,
        update = update.mla_enabled
        )

    prop_microlens_diam: FloatProperty(
        name = "",
        description="Diameter of a single microlens in mikrometers.",
        default = 100.0,
        min = 1,
        max = 1000000.0,
        update = update.microlens_diam
        )

    prop_mla_sensor_dist: FloatProperty(
        name = "",
        description = "Sets the distance between MLA and sensor/diffusor plane.",
        default = 0.1,
        min = 0.001,
        max = 100.0,
        update = update.mla_sensor_dist
        )

    prop_mla_type: EnumProperty(
        name="",
        description="Choose hexagonal or rectangular microlens layout.",
        items=[ ('HEX', "Hexagonal Layout", ""),
                ('RECT', "Rectangular Layout", ""),
               ],
        update = update.mla_type
        )

    prop_three_ml_types: BoolProperty(
        name="",
        description="Use three differently focused microlens types.",
        default = True,
        update = update.three_ml_types
        )

    prop_ml_type_1_f: FloatProperty(
        name = "",
        description = "Focal length of first microlens type in mm.",
        default = 1.7,
        min = 0.0,
        max = 1000.0,
        update = update.ml_type_1_f
        )

    prop_ml_type_2_f: FloatProperty(
        name = "",
        description = "Focal length of second microlens type in mm.",
        default = 2,
        min = 0.0,
        max = 1000.0,
        update = update.ml_type_2_f
        )

    prop_ml_type_3_f: FloatProperty(
        name = "",
        description = "Focal length of third microlens type in mm.",
        default = 2.3,
        min = 0.0,
        max = 1000.0,
        update = update.ml_type_3_f
        )

    prop_focal_distance: FloatProperty(
        name = "",
        description = "Object distance in cm the camera is focused on",
        default = 50,
        min = 1.0,
        max = 10000.0,
        update = update.focal_distance
        )


# ------------------------------------------------------------------------
#    Main Panel
# ------------------------------------------------------------------------

class CAMGEN_PT_Main(bpy.types.Panel):
    bl_idname = "CAMGEN_PT_Main"
    bl_label = "Camera Generator"
    bl_category = "Camera Generator Addon"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_order = 999999  #Used by Blender for sorting the panels (large number means lower position)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Objective")
        row.prop(context.scene.camera_generator, "prop_objective_list")
        row = layout.row()
        row.label(text="Objective Scale")       
        row.prop(context.scene.camera_generator, "prop_objective_scale")
        row = layout.row()
        row.label(text="Radial Vertices per Lens")       
        row.prop(context.scene.camera_generator, "prop_vertex_count_radial")
        row = layout.row()
        row.label(text="Longitudinal Vertices per Lens")       
        row.prop(context.scene.camera_generator, "prop_vertex_count_height")
        row = layout.row()
        row.operator('camgen.createcam', text="Create Camera Model")
        row = layout.row()
        row.operator('camgen.loadconfig', text="Load Camera Config")
        row.operator('camgen.saveconfig', text="Save Camera Config")
        row = layout.row()
        row.label(text="")
        row = layout.row()
        row.label(text="Aperture Blades")
        row.prop(context.scene.camera_generator, "prop_aperture_blades")
        row = layout.row()
        row.label(text="Aperture Scale")
        row.prop(context.scene.camera_generator, "prop_aperture_size")
        row = layout.row()
        row.label(text="Aperture Angle")
        row.prop(context.scene.camera_generator, "prop_aperture_angle")
        row = layout.row()
        row.label(text="Sensor Width in mm")
        row.prop(context.scene.camera_generator, "prop_sensor_width")
        row = layout.row()
        row.label(text="Sensor Height in mm")
        row.prop(context.scene.camera_generator, "prop_sensor_height")
        row = layout.row()
        row.label(text="Wavelength in nm")
        row.prop(context.scene.camera_generator, "prop_wavelength")
        row = layout.row()
        row.label(text="Sensor-Objective Distance in mm")
        row.prop(context.scene.camera_generator, "prop_sensor_mainlens_distance")
        row = layout.row()
        row.label(text="Focal distance in cm")
        row.prop(context.scene.camera_generator, "prop_focal_distance")
        row = layout.row()
        row.label(text="")
        row.operator('camgen.createcheckerboard', text="Create Checkerboard")


# ------------------------------------------------------------------------
#    MLA-Config Subpanel
# ------------------------------------------------------------------------

class CAMGEN_PT_MLAConfig(bpy.types.Panel):
    bl_idname = "CAMGEN_PT_MLAConfig"
    bl_label = "MLA Config"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_parent_id = "CAMGEN_PT_Main"
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Use MLA")
        row.prop(context.scene.camera_generator, "prop_mla_enabled")
        row = layout.row()
        row.label(text="MLA Type")
        row.prop(context.scene.camera_generator, "prop_mla_type") 
        row = layout.row()
        row.label(text="Microlens Diameter in um")
        row.prop(context.scene.camera_generator, "prop_microlens_diam")
        row = layout.row()
        row.label(text="MLA-Sensor Distance in mm")
        row.prop(context.scene.camera_generator, "prop_mla_sensor_dist")
        row = layout.row()
        row.label(text="Use three ML types")
        row.prop(context.scene.camera_generator, "prop_three_ml_types")
        row = layout.row()
        row.label(text="Focal length ML type 1")
        row.prop(context.scene.camera_generator, "prop_ml_type_1_f")
        row = layout.row()
        row.label(text="Focal length ML type 2")
        row.prop(context.scene.camera_generator, "prop_ml_type_2_f")
        row = layout.row()
        row.label(text="Focal length ML type 3")
        row.prop(context.scene.camera_generator, "prop_ml_type_3_f")

class CAMGEN_PT_Tests(bpy.types.Panel):
    bl_idname = "CAMGEN_PT_Tests"
    bl_label = "Tests"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_parent_id = "CAMGEN_PT_Main"
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="")
        row.operator('camgen.runtests', text="Run Tests")
