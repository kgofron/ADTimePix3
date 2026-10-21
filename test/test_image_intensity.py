#!/usr/bin/env python3
"""Exercise image intensity behavior without a running IOC or JavaFX display.

Also runs under Jython 2.7, where the adapter test uses real Java array statistics.
"""
from __future__ import division

import os
import sys
import types
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREEN = os.path.join(ROOT, 'tpx3App/op/bob/profiles/tpx4/Acquire')
sys.path.insert(0, SCREEN)
import image_intensity


class Widget(object):
    def __init__(self, **properties):
        self.properties = properties
        self.user_data = {}

    def getPropertyValue(self, name):
        return self.properties[name]

    def setPropertyValue(self, name, value):
        self.properties[name] = value

    def getUserData(self, key):
        return self.user_data.get(key)

    def setUserData(self, key, value):
        self.user_data[key] = value


class Frame(object):
    def __init__(self, values):
        self.values = values


class Monitor(object):
    def __init__(self, values=(2.0, 8.0, 2048.0), controls=None):
        self.image = Widget(autoscale=False, minimum=0.0, maximum=1000.0)
        self.slider = Widget()
        self.hint = Widget()
        self.controls = controls or [1.0, 0.0, 1000.0]
        self.frame = Frame(values)
        self.scans = 0
        self.pending = 0
        self.control = image_intensity.ImageIntensity(
            self.image, self.slider, self.hint,
            lambda i: self.controls[i], self.write, lambda: self.frame, self.bounds)
        self.run()

    def bounds(self):
        self.scans += 1
        values = self.frame.values
        return (min(values), max(values)) if values else (float('inf'), -float('inf'))

    def write(self, index, value):
        self.controls[index] = value
        self.pending += 1

    def run(self):
        self.control.synchronize()
        for _ in range(20):
            if not self.pending:
                return
            self.pending -= 1
            self.control.synchronize()
        raise AssertionError('Scalar feedback did not settle')

    def edit(self, index, value):
        self.controls[index] = value
        self.run()

    def new_frame(self, values):
        self.frame = Frame(values)
        self.run()

    def limits(self):
        return self.image.properties['minimum'], self.image.properties['maximum']


class IntensityTests(unittest.TestCase):
    def test_auto_tracks_image_and_fields_without_feedback_rescans(self):
        m = Monitor()
        self.assertEqual(m.limits(), (2.0, 2048.0))
        self.assertEqual(m.controls[1:], [2.0, 2048.0])
        self.assertFalse(m.image.properties['autoscale'])
        self.assertEqual(m.scans, 1)
        m.new_frame((0.0, 5.0, 4000.0))
        self.assertEqual(m.limits(), (0.0, 4000.0))
        self.assertEqual(m.controls[1:], [0.0, 4000.0])
        self.assertEqual(m.scans, 2)

    def test_manual_freezes_display_even_with_stale_fields_and_queued_frame(self):
        m = Monitor()
        m.controls = [0.0, 0.0, 1000.0]
        m.frame = Frame((0.0, 9000.0))
        m.run()
        self.assertEqual(m.limits(), (2.0, 2048.0))
        self.assertEqual(m.controls[1:], [2.0, 2048.0])
        self.assertEqual(m.scans, 1)
        m.new_frame((0.0, 12000.0))
        self.assertEqual(m.limits(), (2.0, 2048.0))
        self.assertEqual(m.scans, 1)
        m.edit(0, 1)
        self.assertEqual(m.limits(), (0.0, 12000.0))

    def test_numeric_and_slider_edits_with_stable_headroom(self):
        m = Monitor()
        m.edit(0, 0)
        ceiling = m.slider.properties['maximum']
        m.edit(2, 1000.0)
        m.edit(2, 500.0)
        self.assertEqual(m.slider.properties['maximum'], ceiling)
        self.assertEqual(m.limits(), (2.0, 500.0))
        m.edit(1, 10.0)
        m.edit(2, 50000.0)
        self.assertEqual(m.limits(), (10.0, 50000.0))
        self.assertGreater(m.slider.properties['maximum'], 50000.0)
        m.new_frame((0.0, 1.0))
        self.assertEqual(m.limits(), (10.0, 50000.0))

    def test_invalid_manual_limits_restore_last_valid_range(self):
        for index, value in ((1, 3000.0), (2, -1.0), (2, 2.0),
                             (1, float('nan')), (2, float('inf'))):
            m = Monitor()
            m.edit(0, 0)
            m.edit(index, value)
            self.assertEqual(m.limits(), (2.0, 2048.0))
            self.assertEqual(m.controls[1:], [2.0, 2048.0])

    def test_flat_empty_and_large_sum_frames(self):
        for pixels, expected in (((0.0, 0.0), (0.0, 1.0)),
                                 ((42.0, 42.0), (0.0, 42.0)),
                                 ((-5.0, -5.0), (-5.0, 1.0)),
                                 ((0.0, float(2 ** 60)), (0.0, float(2 ** 60)))):
            m = Monitor(pixels)
            self.assertEqual(m.limits(), expected)
        m = Monitor()
        m.new_frame(())
        self.assertEqual(m.limits(), (2.0, 2048.0))

    def test_three_views_keep_independent_settings(self):
        latest, rolling, total = Monitor(), Monitor((0.0, 3000.0)), Monitor((0.0, 9000.0))
        latest.edit(0, 0)
        latest.edit(2, 500.0)
        rolling.edit(0, 0)
        rolling.edit(2, 2000.0)
        for view in (latest, rolling, total):
            view.new_frame((0.0, 100000.0))
        self.assertEqual(latest.limits(), (2.0, 500.0))
        self.assertEqual(rolling.limits(), (0.0, 2000.0))
        self.assertEqual(total.limits(), (0.0, 100000.0))
        latest.edit(0, 1)
        self.assertEqual(latest.limits(), (0.0, 100000.0))
        self.assertEqual(rolling.limits(), (0.0, 2000.0))

    def test_initial_manual_settings_are_respected(self):
        m = Monitor(controls=[0.0, 7.0, 17.0])
        self.assertEqual(m.limits(), (7.0, 17.0))
        self.assertEqual(m.scans, 0)

    def test_synchronous_feedback_is_safe(self):
        m = Monitor()
        original = m.control.write
        def immediate(index, value):
            original(index, value)
            m.control.synchronize()
        m.control.write = immediate
        m.new_frame((0.0, 10000.0))
        self.assertEqual(m.limits(), (0.0, 10000.0))
        self.assertEqual(m.scans, 2)


class DisplayWiringTests(unittest.TestCase):
    def test_each_view_has_its_own_script_controls_and_slider(self):
        root = ET.parse(os.path.join(SCREEN, 'Tpx4Image.bob')).getroot()
        widgets = dict((w.findtext('name'), w) for w in root.findall('widget'))
        inputs_seen = set()
        for name in ('LatestFrame', 'LastNSum', 'AccumulatedSum'):
            image = widgets[name]
            script = image.find('scripts/script')
            self.assertEqual(script.get('file'), 'image_intensity.py')
            inputs = [p.text for p in script.findall('pv_name')]
            self.assertEqual(len(inputs), 4)
            self.assertEqual(inputs[3], image.findtext('pv_name'))
            self.assertFalse(inputs_seen.intersection(inputs[:3]))
            inputs_seen.update(inputs[:3])
            for suffix, index in (('Autoscale', 0), ('Minimum', 1), ('Maximum', 2), ('ScaleSlider', 2)):
                self.assertEqual(widgets[name + suffix].findtext('pv_name'), inputs[index])
            slider = widgets[name + 'ScaleSlider']
            self.assertEqual(slider.get('type'), 'scaledslider')
            self.assertEqual(slider.findtext('horizontal'), 'false')
            self.assertEqual(slider.findtext('limits_from_pv'), 'false')
            self.assertIn(name + 'ScaleHint', widgets)
            # Competing rules would overwrite the script's applied range.
            for rule in image.findall('rules/rule'):
                self.assertNotIn(rule.get('prop_id'), ('autoscale', 'minimum', 'maximum'))


@unittest.skipUnless(sys.platform.startswith('java'), 'requires Jython for the Java/Phoebus adapter')
class JythonAdapterTests(unittest.TestCase):
    def test_java_statistics_and_adapter_installation(self):
        from jarray import array
        script_module = types.ModuleType('org.csstudio.display.builder.runtime.script')
        class PVUtil(object):
            @staticmethod
            def getDouble(pv):
                return pv.value
            @staticmethod
            def getDoubleArray(pv):
                return array(pv.value.values, 'd')
            @staticmethod
            def getVType(pv):
                return pv.value
        image = Widget(name='LatestFrame', minimum=0.0, maximum=1000.0, autoscale=False)
        slider, hint = Widget(), Widget()
        class ScriptUtil(object):
            @staticmethod
            def findWidgetByName(widget, name):
                return {'LatestFrameScaleSlider': slider, 'LatestFrameScaleHint': hint}[name]
        class PV(object):
            def __init__(self, value):
                self.value = value
            def write(self, value):
                self.value = value
        script_module.PVUtil = PVUtil
        script_module.ScriptUtil = ScriptUtil
        key = 'org.csstudio.display.builder.runtime.script'
        # Jython resolves each package before the final module, unlike CPython
        # importing a fully qualified entry already present in sys.modules.
        names = ['.'.join(key.split('.')[:n]) for n in range(1, len(key.split('.')) + 1)]
        old_modules = dict((name, sys.modules.get(name)) for name in names)
        for name in names:
            module = script_module if name == key else types.ModuleType(name)
            module.__path__ = []
            sys.modules[name] = module
            if '.' in name:
                parent, child = name.rsplit('.', 1)
                setattr(sys.modules[parent], child, module)
        try:
            inputs = [PV(1.0), PV(0.0), PV(1000.0), PV(Frame((0.0, 7.0, 1e12)))]
            image_intensity.install(image, inputs)
            first = image.getUserData('tpx4_image_intensity')
            self.assertEqual(image.properties['maximum'], 1e12)
            self.assertEqual(inputs[2].value, 1e12)
            image_intensity.install(image, inputs)
            self.assertIs(first, image.getUserData('tpx4_image_intensity'))
            inputs[0].value = 0.0
            inputs[3].value = Frame((0.0, 2e12))
            image_intensity.install(image, inputs)
            self.assertEqual(image.properties['maximum'], 1e12)
        finally:
            for name, old_module in old_modules.items():
                if old_module is None:
                    del sys.modules[name]
                else:
                    sys.modules[name] = old_module


if __name__ == '__main__':
    unittest.main()
