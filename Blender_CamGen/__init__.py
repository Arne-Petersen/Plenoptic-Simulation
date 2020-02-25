bl_info = {
    "name" : "Camera_Generator",
    "author" : "Tim Michels",
    "description": "Creates a camera model",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View3D",
    "warning" : "",
    "category" : "Generic"
}

import bpy

from bpy.utils import ( register_class, unregister_class )
from bpy.props import PointerProperty

from . camera_generator import CAMGEN_OT_CreateCam
from . camera_generator import CAMGEN_OT_CreateCheckerboard
from . camera_generator import CAMGEN_OT_LoadConfig
from . camera_generator import CAMGEN_OT_SaveConfig
from . camgen_panel import CAMGEN_Properties
from . camgen_panel import CAMGEN_PT_Main
from . camgen_panel import CAMGEN_PT_MLAConfig
from . import data

classes = (CAMGEN_OT_CreateCam, CAMGEN_OT_CreateCheckerboard, CAMGEN_OT_LoadConfig, CAMGEN_OT_SaveConfig, CAMGEN_Properties, CAMGEN_PT_Main, CAMGEN_PT_MLAConfig)

def register():
    # init data
    data.init()

    # register classes
    for cls in classes:
        register_class(cls)
    # create properties
    bpy.types.Scene.camera_generator = PointerProperty(type=CAMGEN_Properties)

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.camera_generator
