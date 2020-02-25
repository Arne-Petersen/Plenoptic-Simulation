import bpy
import csv
import math

def init():
    global objective
    objective = []
    global glass_data_known
    glass_data_known = False
    global aperture_index
    aperture_index = -1
    global semi_aperture
    semi_aperture = -1
    global objective_list
    objective_list = ()
    global objective_list_created
    objective_list_created = False
    
    # get add-on folder path
    directory = bpy.utils.user_resource('SCRIPTS', "addons")+'/Blender_CamGen/'
    # read lens material data from files
    
    # Sellmeier type data:
    global sellmeier_data
    sellmeier_data = {}
    with open(directory+'sellmeier_materials.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='&')
        for row in reader:
            #"Glass Type": (B1, B2, B3, C1, C2, C3, IOR)
            sellmeier_data[row[0]] = (float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]),float(row[7]))

    # Cauchy type data:  "Glass Type": (C1, C2, C3, C4, C5, C6, IOR)
    global cauchy_data
    cauchy_data = {}
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
