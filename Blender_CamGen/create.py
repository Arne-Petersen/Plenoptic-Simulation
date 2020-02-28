import bpy
import math
import inspect

from . import data

from typing import Any, List, Dict, Tuple

# Helper classes


def add_circle(config: Dict[str, Any]) -> bpy.types.Object:
    '''Adds a circle'''
    bpy.ops.mesh.primitive_circle_add(**config['defaults'])
    circle: bpy.types.Object = bpy.context.active_object
    for setting, value in config.items():
        if setting is 'defaults':
            continue
        setattr(circle, setting, value)
    return circle


def calculate_sagitta(half_lens_height: float, surface_radius: float) -> float:
    '''Calculates sagitta'''
    if half_lens_height > surface_radius:
        return surface_radius
    return surface_radius - math.sqrt(surface_radius * surface_radius - half_lens_height * half_lens_height)


def calculate_number_of_vertices(half_lens_height: float, surface_radius: float, vertex_count_height: int) -> int:
    '''Calculates the number of vertices'''
    return int(vertex_count_height / (math.asin(half_lens_height / surface_radius) / math.pi) + 0.5) * 2


def create_glass_material(name: str, ior: float, remove_transform: bool) -> bpy.types.Material:
    '''Creates a glass material'''
    glass_material: bpy.types.Material = bpy.data.materials['Glass Material'].copy(
    )
    glass_material.name = f'Glass Material {name}'
    glass_material.node_tree.nodes['IOR'].outputs['Value'].default_value = ior

    if remove_transform:
        glass_material.node_tree.links.remove(
            glass_material.node_tree.nodes['Vector Transform.002'].outputs[0].links[0])

    return glass_material


def calculate_outer_vertex(vertices: bpy.types.MeshVertices) -> bpy.types.MeshVertex:
    '''Calculates the outer vertex'''
    outer_vertex = vertices[0]
    for vertex in vertices:
        if vertex.co.z > outer_vertex.co.z:
            outer_vertex = vertex
    return outer_vertex

# Main


def flat_surface(half_lens_height: float, ior: float, position: float, name: str) -> List[float]:
    '''Creates a flat surface as part of the lens stack'''
    circle: bpy.types.Object = add_circle({
        'defaults': {
            'vertices': 64,
            'radius': half_lens_height,
            'fill_type': 'TRIFAN',
            'calc_uvs': False,
            'location': (position, 0, 0),
            'rotation': (0, -math.pi / 2, 0)
        },
        'name': name,
        'parent': bpy.data.objects['Objective']
    })

    circle.data.materials.append(create_glass_material(name, ior, True))

    bpy.ops.object.mode_set(mode="OBJECT")

    outer_vertex: bpy.types.MeshVertex = calculate_outer_vertex(
        circle.data.vertices)

    return [outer_vertex.co.x, outer_vertex.co.y, outer_vertex.co.z]


def lens_surface(vertex_count_height: int, vertex_count_radial: int, surface_radius: float, half_lens_height: float, ior: float, position: float, name: str) -> List[float]:
    '''Creates a lens surface as part of the lens stack'''
    flip = False
    if surface_radius < 0.0:
        flip = True
        surface_radius = -1.0 * surface_radius

    circle: bpy.types.Object = add_circle({
        'defaults': {
            'vertices': calculate_number_of_vertices(half_lens_height, surface_radius, vertex_count_height),
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
        if (vertex.co.y < surface_radius - calculate_sagitta(half_lens_height, surface_radius)) or (vertex.co.x > 0.0):
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
    circle.data.materials.append(create_glass_material(name, ior, False))
    # return the outer vertex for housing creation
    bpy.ops.object.mode_set(mode="OBJECT")
    outer_vertex: bpy.types.MeshVertex = calculate_outer_vertex(
        circle.data.vertices)

    return [outer_vertex.co.x, outer_vertex.co.y, outer_vertex.co.z]
    flip = False
    if surface_radius < 0.0:
        flip = True
        surface_radius = -1.0 * surface_radius

    # create circle
    circle = {
        'defaults': {
            'vertices': calculate_number_of_vertices(half_lens_height, surface_radius, vertex_count_height),
            'radius': surface_radius,
            'location': (0, 0, 0)
        }
    }
    circle = add_circle(circle)

    # ================================================MAGIC
    bpy.ops.object.transform_apply()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode="OBJECT")
    circle.data.vertices[0].co.x = 0.0
    # select all vertices that should be deleted
    for vertex in circle.data.vertices:
        if (vertex.co.y < surface_radius - calculate_sagitta(half_lens_height, surface_radius)) or (vertex.co.x > 0.0):
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
    glass_material = bpy.data.materials['Glass Material'].copy()
    glass_material.name = "Glass Material "+name
    glass_material.node_tree.nodes['IOR'].outputs['Value'].default_value = ior
    circle.data.materials.append(glass_material)
    # return the outer vertex for housing creation
    bpy.ops.object.mode_set(mode="OBJECT")
    outer_vertex = circle.data.vertices[0]
    for vertex in circle.data.vertices:
        if vertex.co.z > outer_vertex.co.z:
            outer_vertex = vertex

    # ================================================END MAGIC
    return [outer_vertex.co.x, outer_vertex.co.y, outer_vertex.co.z]


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
