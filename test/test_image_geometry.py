#!/usr/bin/env python3
"""Check square-pixel fitting independently of detector data and display fonts."""
from __future__ import division

import os
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREEN = os.path.join(ROOT, 'tpx3App/op/bob/profiles/tpx4/Acquire')
sys.path.insert(0, SCREEN)
from image_geometry import fitted_size


class GeometryTests(unittest.TestCase):
    def test_pixels_stay_square_with_different_shapes_and_axis_fonts(self):
        for pixels in ((448, 512), (512, 448), (256, 256), (1024, 256), (1, 512)):
            for margins in ((84, 44), (106, 62), (55, 35)):
                for available in ((638, 672), (900, 700)):
                    width, height = fitted_size(*(pixels + available + margins))
                    raster_width = width - margins[0]
                    raster_height = height - margins[1]
                    self.assertLessEqual(width, available[0])
                    self.assertLessEqual(height, available[1])
                    self.assertGreater(raster_width, 0)
                    self.assertGreater(raster_height, 0)
                    # The integer screen size can differ by at most half a pixel
                    # from the ideal common scale; one direction fills the slot.
                    scale = min((available[0] - margins[0]) / pixels[0],
                                (available[1] - margins[1]) / pixels[1])
                    self.assertLessEqual(abs(raster_width - scale * pixels[0]), 0.5)
                    self.assertLessEqual(abs(raster_height - scale * pixels[1]), 0.5)
                    self.assertTrue(width == available[0] or height == available[1])

    def test_portrait_uses_height_and_landscape_uses_width(self):
        self.assertEqual(fitted_size(448, 512, 638, 672, 84, 44), (634, 672))
        self.assertEqual(fitted_size(512, 448, 638, 672, 84, 44), (638, 529))

    def test_invalid_dimensions_leave_previous_size_unchanged(self):
        for pixels in ((0, 512), (448, 0), (-1, 512),
                       (float('nan'), 512), (448, float('inf'))):
            self.assertIsNone(fitted_size(*(pixels + (638, 672, 84, 44))))
        self.assertIsNone(fitted_size(448, 512, 80, 40, 84, 44))

    def test_each_view_fits_its_actual_axes_and_has_refresh_triggers(self):
        root = ET.parse(os.path.join(SCREEN, 'Tpx4Image.bob')).getroot()
        images = [w for w in root.findall('widget') if w.get('type') == 'image']
        self.assertEqual(len(images), 3)
        for image in images:
            script = image.find("scripts/script[@file='image_geometry.py']")
            self.assertIsNotNone(script)
            inputs = script.findall('pv_name')
            self.assertEqual([p.text for p in inputs[:3]],
                             ['$(P)$(R)ImgSizeX_RBV', '$(P)$(R)ImgSizeY_RBV',
                              image.findtext('pv_name')])
            self.assertIn('Tpx4ImageViewMode', inputs[3].text)
            self.assertTrue(all(p.get('trigger') == 'true' for p in inputs))
            # A competing outer-size rule would undo the runtime fit.
            for rule in image.findall('rules/rule'):
                self.assertNotIn(rule.get('prop_id'), ('width', 'height'))


if __name__ == '__main__':
    unittest.main()
