import bpy
import math

from . import data

# create a flat lens surface
def flat_surface(half_lens_height, ior, position, name):
    bpy.ops.mesh.primitive_circle_add(vertices = 64, radius = half_lens_height, fill_type = 'TRIFAN', calc_uvs = False, location=(0,0,0), rotation = (0, -3.1415926536/2.0, 0))
    bpy.ops.object.transform_apply()
    bpy.context.active_object.location[0] = position
    # rename object and move it to 'Objective' empty
    bpy.context.active_object.name = name
    bpy.context.active_object.parent = bpy.data.objects['Objective']
    # add glass material
    glass_material = bpy.data.materials['Glass Material'].copy()
    glass_material.name = "Glass Material "+name
    glass_material.node_tree.nodes['IOR'].outputs['Value'].default_value = ior
    glass_material.node_tree.links.remove(glass_material.node_tree.nodes['Vector Transform.002'].outputs[0].links[0]) #delete normal recalculation for flat surface
    bpy.context.active_object.data.materials.append(glass_material)
    # get outer vertex for housing creation
    bpy.ops.object.mode_set(mode="OBJECT")
    outer_vertex = bpy.context.active_object.data.vertices[0]
    for vertex in bpy.context.active_object.data.vertices:
        if vertex.co.z > outer_vertex.co.z:
            outer_vertex = vertex
    return [outer_vertex.co.x, outer_vertex.co.y, outer_vertex.co.z]

# create a spherical lens surface
def lens_surface(vertex_count_height, vertex_count_radial, surface_radius, half_lens_height, ior, position, name):
    flip = False
    if surface_radius < 0.0:
        flip = True
        surface_radius = -1.0 * surface_radius

    # calculate sagitta
    sagitta = 0.0
    if(half_lens_height < surface_radius):
        sagitta = surface_radius - math.sqrt(surface_radius*surface_radius - half_lens_height*half_lens_height)
    else:
        sagitta = surface_radius

    # calculate number of vertices needed to get vertex_count_height vertices
    ratio = math.asin(half_lens_height/surface_radius) / 3.1415926536
    num_vertices = 2 * int(vertex_count_height/ratio+0.5)

    # create circle
    bpy.ops.mesh.primitive_circle_add(vertices = num_vertices, radius = surface_radius, location = (0,0,0))
    bpy.ops.object.transform_apply()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.active_object.data.vertices[0].co.x = 0.0
    # select all vertices that should be deleted
    for vertex in bpy.context.active_object.data.vertices:
        if (vertex.co.y < surface_radius - sagitta) or (vertex.co.x > 0.0):
            vertex.select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type='VERT')
    #select all remaining vertices to create a rotational surface
    bpy.ops.mesh.select_all(action='SELECT')
    # use the spin operator to create the rotational surface
    bpy.ops.mesh.spin(steps = vertex_count_radial, angle = 2.0*math.pi, axis = (0,1,0))
    # remove double vertices resulting from the spinning
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0)
    # flip normals for a convex surface
    if not flip:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode = "OBJECT")
    # move to correct position
    bpy.context.active_object.rotation_euler[0] = math.pi/2.0
    if flip:
        bpy.context.active_object.rotation_euler[1] = math.pi/2.0
    else:
        bpy.context.active_object.rotation_euler[1] = -math.pi/2.0
    bpy.ops.object.transform_apply()
    bpy.context.active_object.location[0] = position
    # rename object and move it to 'Objective' empty
    bpy.context.active_object.name = name
    bpy.context.active_object.parent = bpy.data.objects['Objective']
    # add glass material
    glass_material = bpy.data.materials['Glass Material'].copy()
    glass_material.name = "Glass Material "+name
    glass_material.node_tree.nodes['IOR'].outputs['Value'].default_value = ior
    bpy.context.active_object.data.materials.append(glass_material)
    #return the outer vertex for housing creation
    bpy.ops.object.mode_set(mode="OBJECT")
    outer_vertex = bpy.context.active_object.data.vertices[0]
    for vertex in bpy.context.active_object.data.vertices:
        if vertex.co.z > outer_vertex.co.z:
            outer_vertex = vertex
    return [outer_vertex.co.x, outer_vertex.co.y, outer_vertex.co.z]

# create camera and objective housing as a rotational surface using the outer vertices of the lenses
def housing(outer_vertices, outer_lens_index, vertex_count_radial):
    bpy.data.meshes['Housing Mesh'].vertices.add(len(outer_vertices)+3)
    # add outer lens vertices to mesh
    for i in range(0, len(outer_vertices)):
        bpy.data.meshes['Housing Mesh'].vertices[i].co.x = outer_vertices[i][0] + data.objective[outer_lens_index[i]]['position']
        bpy.data.meshes['Housing Mesh'].vertices[i].co.y = outer_vertices[i][1]
        bpy.data.meshes['Housing Mesh'].vertices[i].co.z = outer_vertices[i][2]
    
    # add camera housing vertices to mesh
    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.x = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)-1].co.x
    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.y = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)-1].co.y
    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.z = 1.5 * bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)-1].co.z

    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+1].co.x = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.x + max(3.0 * data.objective[len(data.objective)-1]['thickness'], bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)-1].co.x-bpy.data.meshes['Housing Mesh'].vertices[0].co.x)
    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+1].co.y = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.y
    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+1].co.z = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)].co.z

    bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+2].co.x = bpy.data.meshes['Housing Mesh'].vertices[len(outer_vertices)+1].co.x
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
    bpy.ops.mesh.spin(steps = vertex_count_radial, angle = 2.0*3.1415926536, axis = (1,0,0), center = (0,0,0))
    # remove double vertices resulting from the spinning
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0, use_unselected=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects['Objective Housing'].display_type='WIRE'
    
# create aperture by using the difference modifier on a plane
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
    bpy.ops.mesh.primitive_circle_add(vertices=num_of_blades,radius=0.5, location=(0,0,0))
    # rename
    bpy.context.active_object.name="Opening"
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
    bpy.context.active_object.parent=bpy.data.objects['Aperture']
    # set difference modifier of aperture plane to use new shape
    bpy.data.objects['Aperture Plane'].modifiers['Difference'].object=bpy.data.objects['Opening']
    bpy.data.objects['Opening'].hide_viewport=True
    bpy.data.objects['Opening'].hide_render = True
    # rescale opening according to currently set scaling
    bpy.data.objects['Opening'].scale[1] = bpy.data.scenes[0].camera_generator.prop_aperture_size/1000.0
    bpy.data.objects['Opening'].scale[2] = bpy.data.scenes[0].camera_generator.prop_aperture_size/1000.0
    # rotate opening according to currently set angle
    bpy.data.objects['Opening'].rotation_euler[0] = bpy.data.scenes[0].camera_generator.prop_aperture_angle/180.0*math.pi