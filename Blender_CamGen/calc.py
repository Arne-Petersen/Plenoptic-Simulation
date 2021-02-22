# ------------------------------------------------------------------------
#    Class containing various calculations
# ------------------------------------------------------------------------

import math

from . import data

# calculates the IOR for the given material and wavelength based on the sellmeier equation
def sellmeier_ior(material_name: str, wavelength: float) -> float:
    B1, B2, B3, C1, C2, C3, _ior = data.sellmeier_data[material_name]
    
    w2 = math.pow(wavelength, 2)
    a1 = (B1 * w2) / (w2 - C1)
    a2 = (B2 * w2) / (w2 - C2)
    a3 = (B3 * w2) / (w2 - C3)
    
    return math.sqrt(1 + a1 + a2 + a3)

# calculates the IOR for the given material and wavelength based on the cauchy equation
def cauchy_ior(material_name: str, wavelength: float) -> float:
    C1, C2, C3, C4, C5, C6, _ior = data.cauchy_data[material_name]
    
    w2 = math.pow(wavelength, 2)
    wm2 = math.pow(wavelength, -2)
    wm4 = math.pow(wavelength, -4)
    wm6 = math.pow(wavelength, -6)
    wm8 = math.pow(wavelength, -8)
    
    return math.sqrt(C1 + C2*w2 + C3*wm2 + C4*wm4 + C5*wm6 + C6*wm8)

# calculates the IOR for the given material and wavelength if the material is known
def ior(material_name: str, wavelength: float) -> float:
    if material_name in data.sellmeier_data.keys():
        return sellmeier_ior(material_name, wavelength)
    if material_name in data.cauchy_data.keys():
        return cauchy_ior(material_name, wavelength)
    return None

# calculates the ratio of the two material IORs for the refraction shader
def shader_iors(objective):
    for i in range(len(objective)-1, 0, -1):
        objective[i]['ior_ratio'] = objective[i - 1]['ior_wavelength']/objective[i]['ior_wavelength']
    objective[0]['ior_ratio'] = 1.0/objective[0]['ior_wavelength']
    return objective

# calculates the aperture position based on the lens data
def aperture(objective):
    aperture_index = -1
    for i in range(0, len(objective)-1):
        if objective[i]['material'] == "air" and objective[i+1]['material'] == "air":
            aperture_index = i+1
            break
    aperture_position = 0.0

    if aperture_index != -1:
        for i in range(0, aperture_index):
            aperture_position = aperture_position + objective[i]['thickness']
    else:
        if objective[0]['radius'] >= 0.0:
            aperture_position = -0.001
        else:
            radius = objective[0]['radius']
            height = objective[0]['semi_aperture']
            aperture_position = min(-0.001, 1.1 * (radius + math.sqrt(radius*radius - height*height)))

    for i in range(0, len(objective)):
        objective[i]['position'] = objective[i]['radius'] - aperture_position
        for j in range(0, i):
            objective[i]['position'] = objective[i]['position'] + objective[j]['thickness']

    return objective, aperture_index

# calculates sagitta for a lens with the given parameters
def sagitta(half_lens_height: float, surface_radius: float) -> float:
    if half_lens_height > surface_radius:
        return surface_radius
    return surface_radius - math.sqrt(surface_radius * surface_radius - half_lens_height * half_lens_height)

# calculates the number of vertices
def number_of_vertices(half_lens_height: float, surface_radius: float, vertex_count_height: int) -> int:
    return int(vertex_count_height / (math.asin(half_lens_height / surface_radius) / math.pi) + 0.5) * 2