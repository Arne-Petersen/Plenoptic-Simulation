import unittest
import sys
import bpy

from . import camera_generator
from . import data

class TestCameraGenerator(unittest.TestCase):
    def test_str_to_float(self):
        self.assertEqual(camera_generator.str_to_float('1'), 1.0)
        self.assertEqual(camera_generator.str_to_float(' 1 '), 1.0)
        self.assertEqual(camera_generator.str_to_float('-1'), -1.0)
        self.assertEqual(camera_generator.str_to_float(''), 0.0)
        self.assertRaises(ValueError, camera_generator.str_to_float, 'abc')

    def test_initialise_cycles(self):
        scene = bpy.data.scenes[0]
        camera_generator.initialise_cycles(scene, data.cycles_settings)
        for setting in data.cycles_settings:
            self.assertEquals(scene.cycles[setting], data.cycles_settings[setting])

    def test_parse_lensfile(self):
        lensfile = 'D-Gauss F1.4 45deg_Mandler USP2975673 p351.csv'
        self.assertDictEqual(camera_generator.parse_lensfile(lensfile)[0],
                             {
            'radius': 0.08824,
            'thickness': 0.00894,
            'material': 'LAF3',
            'ior': 1.717,
            'ior_wavelength': 1.717,
            'ior_ratio': 1.717,
            'semi_aperture': 0.043,
            'position': 0.0,
            'name': 'Surface_01_LAF3'
        })

    def test_delete_recursive(self):
        mesh = bpy.data.meshes.new("mesh")
        object1 = bpy.data.objects.new("object1", mesh)
        object2 = bpy.data.objects.new("object1", mesh)
        object2.parent = object1
        camera_generator.delete_recursive(object1)
        self.assertRaises(
            ReferenceError, camera_generator.delete_recursive, object1)


def test_main():
    import os
    path = os.path.dirname(__file__)
    sys.path.append(path)

    test_cases = [
        TestCameraGenerator
    ]

    suite = unittest.TestSuite()
    for case in test_cases:
        suite.addTest(unittest.makeSuite(case))
    unittest.TextTestRunner().run(suite).wasSuccessful()


if __name__ == "__main__":
    test_main()
