# ------------------------------------------------------------------------
#    Class containing data shared across different parts of the addon
# ------------------------------------------------------------------------

from bpy.utils import user_resource

from .io import read_dispersion_data


# flag for de/activation of debug output and unit tests
debug: bool = False

# set addon dir
addon_directory = user_resource('SCRIPTS', "addons")+'/Blender_CamGen/'
# set lens directory
lens_directory = addon_directory+'Lenses'

# cycles setup required for accurate tracing through multiple lenses
cycles_settings: dict = {
    'max_bounces': 128,
    'diffuse_bounces': 32,
    'glossy_bounces': 32,
    'transparent_max_bounces': 64,
    'transmission_bounces': 65,
    'sample_clamp_indirect': 0,
    'blur_glossy': 0
}

# objective data
objective = []
glass_data_known = False
aperture_index = -1
semi_aperture = -1

# objective list for drop down lens selector
objective_list = ()
objective_list_created = False

# coefficients for dispersion accodring to Sellmeier equation: (B1, B2, B3, C1, C2, C3, IOR)
sellmeier_data = {}
# coefficients for dispersion accodring to Cauchy equation: (C1, C2, C3, C4, C5, C6, IOR)
cauchy_data = {}

# flag which specifies whether user defined data should be used for camera creation
use_gui_data = False

# initializes global variables
def init():
    global objective
    global glass_data_known
    global aperture_index
    global semi_aperture
    global objective_list
    global objective_list_created
    global use_gui_data
    global sellmeier_data
    global cauchy_data
    global addon_directory
    global lens_directory
    # load dispersion data
    sellmeier_data = read_dispersion_data(addon_directory+'sellmeier_materials.csv')
    cauchy_data = read_dispersion_data(addon_directory+'cauchy_materials.csv')