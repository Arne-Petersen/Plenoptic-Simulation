import bpy
import csv
import math

# flag for de/activation of debug output and unit tests
debug: bool = False

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

# applies cycles settings
def set_cycles_parameters(scene: bpy.types.Scene):
    global cycles_settings
    for setting in cycles_settings:
        setattr(scene.cycles, setting, cycles_settings[setting])


# initializes global variables
objective = []
glass_data_known = False
aperture_index = -1
semi_aperture = -1
objective_list = ()
objective_list_created = False
sellmeier_data = {}
cauchy_data = {}

def init():
    global objective
    global glass_data_known
    global aperture_index
    global semi_aperture
    global objective_list
    global objective_list_created
    
    # get add-on folder path
    directory = bpy.utils.user_resource('SCRIPTS', "addons")+'/Blender_CamGen/'
    # read lens material data from files
    
    # Sellmeier type data:
    global sellmeier_data
    with open(directory+'sellmeier_materials.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='&')
        for row in reader:
            #"Glass Type": (B1, B2, B3, C1, C2, C3, IOR)
            sellmeier_data[row[0]] = (float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]),float(row[7]))

    # Cauchy type data:  "Glass Type": (C1, C2, C3, C4, C5, C6, IOR)
    global cauchy_data
    with open(directory+'cauchy_materials.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='&')
        for row in reader:
            #"Glass Type": (C1, C2, C3, C4, C5, C6, IOR)
            cauchy_data[row[0]] = (float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]),float(row[7]))


# calculates the IOR for the given material and wavelength based on the sellmeier equation
def calc_sellmeier(material_name, wavelength):
    B1, B2, B3, C1, C2, C3, _ior = sellmeier_data[material_name]
    
    w2 = math.pow(wavelength, 2)
    a1 = (B1 * w2) / (w2 - C1)
    a2 = (B2 * w2) / (w2 - C2)
    a3 = (B3 * w2) / (w2 - C3)
    
    return math.sqrt(1 + a1 + a2 + a3)

# calculates the IOR for the given material and wavelength based on the cauchy equation
def calc_cauchy(material_name, wavelength):
    C1, C2, C3, C4, C5, C6, _ior = cauchy_data[material_name]
    
    w2 = math.pow(wavelength, 2)
    wm2 = math.pow(wavelength, -2)
    wm4 = math.pow(wavelength, -4)
    wm6 = math.pow(wavelength, -6)
    wm8 = math.pow(wavelength, -8)
    
    return math.sqrt(C1 + C2*w2 + C3*wm2 + C4*wm4 + C5*wm6 + C6*wm8)

# calculates the IOR for the given material and wavelength if the material is known
def calculate_ior(material_name, wavelength):
    if material_name in sellmeier_data.keys():
        return calc_sellmeier(material_name, wavelength)
    if material_name in cauchy_data.keys():
        return calc_cauchy(material_name, wavelength)
    return None

# calculates the ratio of the two material IORs for the refraction shader
def calculate_shader_iors():
    global objective

    for i in range(len(objective)-1, 0, -1):
        objective[i]['ior_ratio'] = objective[i - 1]['ior_wavelength']/objective[i]['ior_wavelength']
    objective[0]['ior_ratio'] = 1.0/objective[0]['ior_wavelength']

# calculates the aperture position based on the lens data
def calculate_aperture():
    global aperture_index
    global objective

    for i in range(0, len(objective)-1):
        if objective[i]['material'] == "air" and objective[i+1]['material'] == "air":
            aperture_index = i+1
            break
    aperture_position = 0.0

    if aperture_index != -1:
        for i in range(0, aperture_index):
            aperture_position = aperture_position + objective[i]['thickness']
    else:
        if objective[0]['radius'] > 0.0:
            aperture_position = -0.01
        else:
            radius = objective[0]['radius']
            height = objective[0]['semi_aperture']
            aperture_position = min(-0.01, 1.1 * (radius + math.sqrt(radius*radius - height*height)))

    for i in range(0, len(objective)):
        objective[i]['position'] = objective[i]['radius'] - aperture_position
        for j in range(0, i):
            objective[i]['position'] = objective[i]['position'] + objective[j]['thickness']

# calculates sagitta for a lens with the given parameters
def calculate_sagitta(half_lens_height: float, surface_radius: float) -> float:
    if half_lens_height > surface_radius:
        return surface_radius
    return surface_radius - math.sqrt(surface_radius * surface_radius - half_lens_height * half_lens_height)

# calculates the number of vertices
def calculate_number_of_vertices(half_lens_height: float, surface_radius: float, vertex_count_height: int) -> int:
    return int(vertex_count_height / (math.asin(half_lens_height / surface_radius) / math.pi) + 0.5) * 2