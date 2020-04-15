# ------------------------------------------------------------------------
#    Class for object and material creation in Blender
# ------------------------------------------------------------------------

import bpy
import math
import mathutils
import numpy as np
import inspect

from . import calc
from . import data

from typing import Any, List, Dict, Tuple

# ------------------------------------------------------------------------
#    Helper functions
# ------------------------------------------------------------------------

# creates a circle mesh
def add_circle(config: Dict[str, Any]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_circle_add(**config['defaults'])
    circle: bpy.types.Object = bpy.context.active_object
    for setting, value in config.items():
        if setting is 'defaults':
            continue
        setattr(circle, setting, value)
    return circle

# creates refraction material for glasses
def add_glass_material(name: str, ior: float, normal_recalculation: bool) -> bpy.types.Material:
    glass_material: bpy.types.Material = bpy.data.materials['Glass Material'].copy()
    glass_material.name = f'Glass Material {name}'
    glass_material.node_tree.nodes['IOR'].outputs['Value'].default_value = ior

    # delete normal recalculation for flat surface
    if not normal_recalculation:
        glass_material.node_tree.links.remove(glass_material.node_tree.nodes['Vector Transform.002'].outputs[0].links[0]) # fresnel link
        glass_material.node_tree.links.remove(glass_material.node_tree.nodes['Vector Transform.002'].outputs[0].links[0]) # refraction link
        glass_material.node_tree.links.remove(glass_material.node_tree.nodes['Vector Transform.002'].outputs[0].links[0]) # reflection link
    return glass_material

# finds the outer vertex, i.e. the vertex with the largest z value
def find_outer_vertex(vertices: bpy.types.MeshVertices) -> bpy.types.MeshVertex:
    outer_vertex = vertices[0]
    for vertex in vertices:
        if vertex.co.z > outer_vertex.co.z:
            outer_vertex = vertex
    return outer_vertex

# ------------------------------------------------------------------------
#    Single component creation
# ------------------------------------------------------------------------

# creates a flat surface for lenses without curvature
def flat_surface(half_lens_height: float, ior: float, position: float, name: str) -> List[float]:
    circle: bpy.types.Object = add_circle({
        'defaults': {
            'vertices': 64,
            'radius': half_lens_height,
            'fill_type': 'TRIFAN',
            'calc_uvs': False,
            'location': (0, 0, 0),
            'rotation': (0, -math.pi / 2, 0)
        },
        'name': name,
        'parent': bpy.data.objects['Objective']
    })

    bpy.ops.object.transform_apply()
    circle.location[0] = position

    circle.data.materials.append(add_glass_material(name, ior, False))

    # flip normals
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.flip_normals()

    bpy.ops.object.mode_set(mode="OBJECT")

    outer_vertex: bpy.types.MeshVertex = find_outer_vertex(circle.data.vertices)
    return [outer_vertex.co.x, outer_vertex.co.y, outer_vertex.co.z]

# creates a spherical lens surface by rotating a circle section - this leads to non-uniformly distributed vertices!
def rotational_lens_surface(vertex_count_height: int, vertex_count_radial: int, surface_radius: float, half_lens_height: float, ior: float, position: float, name: str) -> List[float]:
    flip = False
    if surface_radius < 0.0:
        flip = True
        surface_radius = -1.0 * surface_radius

    circle: bpy.types.Object = add_circle({
        'defaults': {
            'vertices': calc.number_of_vertices(half_lens_height, surface_radius, vertex_count_height),
            'radius': surface_radius,
            'location': (0, 0, 0)
        }
    })

    # TODO: Refactor
    bpy.ops.object.transform_apply()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode="OBJECT")
    circle.data.vertices[0].co.x = 0.0
    # select all vertices that should be deleted
    for vertex in circle.data.vertices:
        if (vertex.co.y < surface_radius - calc.sagitta(half_lens_height, surface_radius)) or (vertex.co.x > 0.0):
            vertex.select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type='VERT')
    # select all remaining vertices to create a rotational surface
    bpy.ops.mesh.select_all(action='SELECT')
    # use the spin operator to create the rotational surface
    bpy.ops.mesh.spin(steps=vertex_count_radial,
                      angle=2.0*math.pi, axis=(0, 1, 0))
    # remove double vertices resulting from the spinning
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0)
    # flip normals for a convex surface
    if not flip:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    # move to correct position
    circle.rotation_euler[0] = math.pi/2.0
    if flip:
        circle.rotation_euler[1] = math.pi/2.0
    else:
        circle.rotation_euler[1] = -math.pi/2.0
    bpy.ops.object.transform_apply()
    circle.location[0] = position
    # rename object and move it to 'Objective' empty
    circle.name = name
    circle.parent = bpy.data.objects['Objective']
    # add glass material
    circle.data.materials.append(add_glass_material(name, ior, True))
    # return the outer vertex for housing creation
    bpy.ops.object.mode_set(mode="OBJECT")
    outer_vertex: bpy.types.MeshVertex = find_outer_vertex(circle.data.vertices)
    return [outer_vertex.co.x, outer_vertex.co.y, outer_vertex.co.z]

# creates a spherical lens surface with uniformly distributed vertices
def uniform_lens_surface(edgelength_target: float, sphere_radius: float, half_lens_height: float, ior: float, position: float, name: str):
    # check lens direction
    flip = False
    if sphere_radius < 0.0:
        flip = True
        sphere_radius = -1.0 * sphere_radius

    # distance between sphere center and bottom of sphere segment
    cut_length = calc.sagitta(half_lens_height, sphere_radius) - sphere_radius
    # radius of most outer slice
    radius_cut = math.sqrt(math.pow(sphere_radius,2) - math.pow(cut_length,2))
    # angle between vetors to sphere tip and outmost ring
    sphere_angle = math.asin(radius_cut / sphere_radius)

    # number of rings (including single-vertex sphere tip)
    ring_count = math.ceil(sphere_radius * sphere_angle / edgelength_target) + 1
    # radius of ring as 2D-slice
    ring_radii = np.zeros(ring_count)
    ring_heights = np.zeros(ring_count)
    ring_vert_counts = np.zeros(ring_count)
    # number of vertices for each ring
    for ring_idx in range(0,ring_count):
        # radius of ring as 2D-slice
        ring_radii[ring_idx] = sphere_radius * math.sin( sphere_angle * ring_idx /(ring_count-1) )
        # height from sphere center of ring as 2D-slice
        ring_heights [ring_idx] = sphere_radius * math.cos( sphere_angle* ring_idx /(ring_count-1) )
        # number of vertices for each ring
        ring_vert_counts[ring_idx] = max(math.ceil(2 * math.pi * ring_radii[ring_idx] / edgelength_target), 1)
    
    # approx triangle edge lengths per ring as radian
    ring_angles = 2 * math.pi / ring_vert_counts

    # overall vertex count
    vert_count = int(np.sum(ring_vert_counts))
    # 3-space vertex positions
    vertices = np.zeros((3, vert_count))
    # per vertex texture map coordinates in uv format
    vertex_uvs = np.zeros((2, vert_count))
    # triangle index list, right hand order
    triangles = np.zeros((3, 4*vert_count)) # worst case: one vertex generates 4 triangles

    # first level is center vertex, radius 0, height = sphere_radius
    vertices[:, 0] = [0, 0, ring_heights[1]]
    # debug vertex count
    written_verts = 1
    # for all rings, add vertices corresponding ring vertex count
    for ring_idx in range(1, ring_count):
        ring_vert_count = int(ring_vert_counts[ring_idx])
        for vert_idx in range(0, ring_vert_count):
            # ring has radius ring_radii(ring_idx) and height ring_heights(ring_idx)
            vertices[:, written_verts+vert_idx] = [ring_radii[ring_idx] * math.cos(vert_idx * ring_angles[ring_idx]), ring_radii[ring_idx] * math.sin(vert_idx*ring_angles[ring_idx]),ring_heights[ring_idx]]
            vertex_uvs[:, written_verts+vert_idx] = [(ring_idx-1)/(ring_count-1) * 0.5 *math.cos(vert_idx*ring_angles[ring_idx]) + 0.5, (ring_idx-1)/(ring_count-1) * 0.5 * math.sin(vert_idx*ring_angles[ring_idx]) + 0.5]
        written_verts = written_verts + ring_vert_count
    if written_verts != vert_count:
        raise ValueError('Vertex count missmatch!')

    # for all rings except sphere tip, create triangle indices depending on circle segment vertex distance
    written_tris = -1
    for ring_idx in range(1, ring_count):
        ring_vert_count = ring_vert_counts[ring_idx]
        ring_vert_id_offset = np.sum(ring_vert_counts[0:ring_idx])
        last_ring_vert_count = ring_vert_counts[ring_idx-1]
        if ring_idx > 1:
            last_ring_vert_idx_offset = np.sum(ring_vert_counts[0:ring_idx-1])
        else:
            # for first run offset is 0 for sphere tip vertex
            last_ring_vert_idx_offset = 0

        # keep track of indices to processed vertices in previous ring
        last_idx_1 = 0

        for vert_idx in range(0, int(ring_vert_count)):
            # index of active vertex edges are drawn from
            active_vert_idx = ring_vert_id_offset + vert_idx
            # index of first vertex in ring after active one
            next_active_vert_idx = ring_vert_id_offset + ((vert_idx + 1) % ring_vert_count)

            # get projection of active vertex to index range of previous ring
            projected_idx = last_ring_vert_count * float(vert_idx) / ring_vert_count
            # idx_1 and idx_2 are vertices in previous ring closest to active vertex
            idx_1 = math.floor( projected_idx )
            # distance between fractional projection and floored index
            dist = projected_idx - idx_1
            # make indices relative to previous ring index offset
            idx_2 = (idx_1 + 1) % last_ring_vert_count
            idx_1 = last_ring_vert_idx_offset + idx_1
            idx_2 = last_ring_vert_idx_offset + idx_2

            written_tris = written_tris+1
            if idx_1 == idx_2:
                # previous ring has only a single vertex
                triangles[:, written_tris] = [active_vert_idx, next_active_vert_idx, idx_1]
            else:
                if last_idx_1 == idx_1:
                    # last step has drawn
                    triangles[:, written_tris] = [active_vert_idx, next_active_vert_idx, idx_2]
                else:
                    if dist < 0.5:
                        # 'left' previous ring vertex is closer to index projection
                        # create triangle active, right of active, left in previous ring
                        triangles[:, written_tris] = [active_vert_idx, next_active_vert_idx, idx_1]
                        # create triangle right of active, right in previous ring, left in previous ring
                        written_tris = written_tris+1
                        triangles[:, written_tris] = [next_active_vert_idx, idx_2, idx_1]
                    else:
                        # 'right' previous ring vertex is closer to index projection
                        # create triangle active, right of active, right in previous ring
                        triangles[:, written_tris] = [active_vert_idx, next_active_vert_idx, idx_2]
                        # create triangle active, right in previous ring, left in previous ring
                        written_tris = written_tris+1
                        triangles[:, written_tris] = [active_vert_idx, idx_2, idx_1]
            # update last used previous ring indices
            last_idx_1 = idx_1

    # create new mesh and object
    lens_mesh = bpy.data.meshes.new(name)
    lens_object = bpy.data.objects.new(name, lens_mesh)
    camera_collection = bpy.data.collections.get("Camera Collection")
    camera_collection.objects.link(lens_object)
    bpy.context.view_layer.objects.active = lens_object
    # convert vertex and triangle data to Blender compatible format
    vertices_vec = []
    triangles_int = []
    for vert_idx in range(0, vert_count):
        vertices_vec.append(mathutils.Vector((vertices[0,vert_idx],vertices[1,vert_idx],vertices[2,vert_idx])))
    for tri_idx in range(0, written_tris + 1):
        triangles_int.append([int(triangles[0,tri_idx]), int(triangles[1,tri_idx]), int(triangles[2,tri_idx])])
    # create mesh from the calculated and converted data
    lens_mesh.from_pydata(vertices_vec,[],triangles_int)

    # rotate the lens and flip normals according to its orientation
    if flip:
        lens_object.rotation_euler[1] = math.pi/2
    else:
        lens_object.rotation_euler[1] = -math.pi/2
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.flip_normals()
    # set the lens position
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.transform_apply()
    lens_object.location[0] = position
    # set parent
    lens_object.parent = bpy.data.objects['Objective']
    # add glass material
    lens_object.data.materials.append(add_glass_material(name, ior, True))

    # save min number of outer ring vertices for housing creation
    data.num_radial_housing_vertices = min(data.num_radial_housing_vertices, int(ring_vert_counts[ring_count-1]))

    # calculate outer vertex for housing creation
    outer_vertex_id = int(np.sum(ring_vert_counts[0:ring_count-1]))
    if flip:
        outer_vert = [vertices[2, outer_vertex_id], 0, vertices[0, outer_vertex_id]]
    else:
        outer_vert = [-vertices[2, outer_vertex_id], 0, vertices[0, outer_vertex_id]]
    return outer_vert

# creates the objective and camera housing
def housing(outer_vertices, outer_lens_index, vertex_count_radial):
    bpy.data.meshes['Housing Mesh'].vertices.add(len(outer_vertices)+3)
    # add outer lens vertices to mesh
    for i in range(0, len(outer_vertices)):
        bpy.data.meshes['Housing Mesh'].vertices[i].co.x = outer_vertices[i][0] + \
            data.objective[outer_lens_index[i]]['position']
        bpy.data.meshes['Housing Mesh'].vertices[i].co.y = outer_vertices[i][1]
        bpy.data.meshes['Housing Mesh'].vertices[i].co.z = outer_vertices[i][2]

    # add camera housing vertices to mesh
    bpy.data.meshes['Housing Mesh'].vertices[len(
        outer_vertices)].co.x = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)-1].co.x
    bpy.data.meshes['Housing Mesh'].vertices[len(
        outer_vertices)].co.y = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)-1].co.y
    bpy.data.meshes['Housing Mesh'].vertices[len(
        outer_vertices)].co.z = 1.5 * bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)-1].co.z

    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+1].co.x = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.x + max(3.0 * data.objective[len(
        data.objective)-1]['thickness'], bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)-1].co.x-bpy.data.meshes['Housing Mesh'].vertices[0].co.x)
    bpy.data.meshes['Housing Mesh'].vertices[len(
        outer_vertices)+1].co.y = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.y
    bpy.data.meshes['Housing Mesh'].vertices[len(
        outer_vertices)+1].co.z = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.z

    bpy.data.meshes['Housing Mesh'].vertices[len(
        outer_vertices)+2].co.x = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+1].co.x
    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+2].co.y = 0.0
    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+2].co.z = 0.0

    # connect vertices
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects['Objective Housing']
    for i in range(0, len(outer_vertices)+2):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode="OBJECT")
        # select two vertices
        bpy.data.objects['Objective Housing'].data.vertices[i].select = True
        bpy.data.objects['Objective Housing'].data.vertices[i+1].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.edge_face_add()

    # select all vertices to create a rotational surface
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    # use the spin operator to create the rotational surface
    bpy.ops.mesh.spin(steps=vertex_count_radial, angle=2.0 *
                      3.1415926536, axis=(1, 0, 0), center=(0, 0, 0))
    # remove double vertices resulting from the spinning
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0, use_unselected=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects['Objective Housing'].display_type = 'WIRE'

# creates the aperture via difference modifier
def aperture():
    # check if old opening exists and delete it
    for current_object in bpy.data.objects:
        current_object.select_set(False)
        if current_object.name == 'Opening':
            bpy.data.objects['Opening'].hide_viewport = False
            bpy.data.objects['Opening'].hide_render = False
            bpy.context.active_object.select_set(False)
            current_object.select_set(True)
            bpy.ops.object.delete()

    # create circle
    num_of_blades = bpy.data.scenes[0].camera_generator.prop_aperture_blades
    bpy.ops.mesh.primitive_circle_add(
        vertices=num_of_blades, radius=0.5, location=(0, 0, 0))
    # rename
    bpy.context.active_object.name = "Opening"
    # rotate
    bpy.context.active_object.rotation_euler[0] = 90.0/180.0*3.1415926536
    bpy.context.active_object.rotation_euler[2] = 90.0/180.0*3.1415926536

    # switch to edit mode, add face and extrude object
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.extrude_edges_move()
    bpy.ops.transform.translate(value=(0.01, 0, 0))
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.select_all()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    # switch back to object mode and reset position
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.active_object.location[0] = -0.005
    bpy.ops.object.transform_apply()
    # move object to aperture empty
    bpy.context.active_object.parent = bpy.data.objects['Aperture']
    # set difference modifier of aperture plane to use new shape
    bpy.data.objects['Aperture Plane'].modifiers['Difference'].object = bpy.data.objects['Opening']
    bpy.data.objects['Opening'].hide_viewport = True
    bpy.data.objects['Opening'].hide_render = True
    # rescale opening according to currently set scaling
    bpy.data.objects['Opening'].scale[1] = bpy.data.scenes[0].camera_generator.prop_aperture_size/1000.0
    bpy.data.objects['Opening'].scale[2] = bpy.data.scenes[0].camera_generator.prop_aperture_size/1000.0
    # rotate opening according to currently set angle
    bpy.data.objects['Opening'].rotation_euler[0] = bpy.data.scenes[0].camera_generator.prop_aperture_angle/180.0*math.pi


# ------------------------------------------------------------------------
#    Multiple component creation
# ------------------------------------------------------------------------

# creates multiple lenses from list and return a list of outer vertices for housing creation
def lenses(lens_patch_size: float, vertex_count_height: int, vertex_count_radial: int, lenses: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[int]]:
    outer_vertices, outer_lens_index = [], list(range(len(lenses)))

    for index, lens in enumerate(lenses):
        if lens['material'] == "air" and lenses[index - 1]['material'] == "air":
            outer_lens_index.remove(index)
            continue
        if lens['radius'] == 0.0:
            outer_vertices.append(flat_surface(
                lens['semi_aperture'], lens['ior_ratio'], lens['position'], lens['name']))
            continue
        if data.lens_creation_method == 'UNIFORM':
            data.num_radial_housing_vertices = 120
            outer_vertices.append(uniform_lens_surface(lens_patch_size, lens['radius'], lens['semi_aperture'], lens['ior_ratio'], lens['position'], lens['name']))
        else:
            data.num_radial_housing_vertices = vertex_count_radial
            outer_vertices.append(rotational_lens_surface(vertex_count_height, vertex_count_radial, lens['radius'], lens['semi_aperture'], lens['ior_ratio'], lens['position'], lens['name']))
        
    return outer_vertices, outer_lens_index

# creates a new calibration pattern
def calibration_pattern():
    # create new plane
    bpy.ops.mesh.primitive_plane_add(size=1, rotation=(0, 0.5*3.14159, 0), location=(0, 0, 0))
    bpy.ops.object.transform_apply()
    calibration_pattern = bpy.context.active_object
    calibration_pattern.name = 'Calibration Pattern'
    # set material
    calibration_pattern.data.materials.append(bpy.data.materials['Calibration Pattern Material'])
    # set location and rotation relative to camera
    calibration_pattern.location = bpy.data.objects['Camera'].location
    calibration_pattern.rotation_euler = bpy.data.objects['Camera'].rotation_euler
    bpy.ops.object.transform_apply(location = True, rotation = False, scale = False, properties = False)

    translation = mathutils.Vector((-bpy.data.scenes[0].camera_generator.prop_focal_distance / 100.0, 0.0, 0.0))
    translation.rotate(calibration_pattern.rotation_euler) 
    calibration_pattern.location = translation