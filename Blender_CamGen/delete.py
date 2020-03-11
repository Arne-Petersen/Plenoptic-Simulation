# ------------------------------------------------------------------------
#    Class for object and material deletion in Blender
# ------------------------------------------------------------------------

import bpy


# ------------------------------------------------------------------------
#    Single component removal
# ------------------------------------------------------------------------

# deletes an object and all of its children
def recursive(parent_object):
    children = parent_object.children
    for child in children:
        recursive(child)
    bpy.data.objects.remove(parent_object)

# deletes an object by name
def blender_object(name: str):
    for object in bpy.data.objects:
        if object.name == name:
            recursive(object)
            break

# deletes a camera by name
def camera(name: str):
    for camera in bpy.data.cameras:
        if camera.name == name:
            bpy.data.cameras.remove(camera)

# deletes a collection by name
def collection(name: str):
    for collection in bpy.data.collections:
        if collection.name == name:
            bpy.data.collections.remove(bpy.data.collections[name])
            break

# deletes all orphan meshes
def orphan_meshes():
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

# deletes all orphan materials
def orphan_materials():
    for material in bpy.data.materials:
        if material.users == 0 or material.use_fake_user:
            bpy.data.materials.remove(material)

# deletes all orphan node groups
def orphan_node_groups():
    for group in bpy.data.node_groups:
        if group.users == 0:
            bpy.data.node_groups.remove(group)


# ------------------------------------------------------------------------
#    Multiple component removal
# ------------------------------------------------------------------------

# deletes the old camera collection including materials
def old_camera():
    # delete camera object and its children
    blender_object('Camera')
    # delete the camera collection
    collection('Camera Collection')
    # delete the orthographic camera
    camera('Orthographic Camera')
    # delete orphan data
    orphan_meshes()
    orphan_materials
    orphan_node_groups()

# deletes the old calibration pattern
def old_calibration_pattern():
    # delete old calibration pattern
    blender_object('Calibration Pattern')
    # delete orphan meshes
    orphan_meshes()