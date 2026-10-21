"""Display-only intensity controls for Phoebus (Jython 2.7).

Input PV order: Auto, minimum, maximum, image waveform. Native autoscale keeps
its effective limits private, so Java computes a full-image range and this
controller applies it with native autoscale disabled. No pixel loop runs in
Python. Scalar feedback reuses the range cached for the current waveform.
"""

from __future__ import division

import math
from threading import RLock


class ImageIntensity(object):
    def __init__(self, image, slider, hint, read, write, data, bounds):
        self.image = image
        self.slider = slider
        self.hint = hint
        self.read = read
        self.write = write
        self.data = data
        self.bounds = bounds
        self.lock = RLock()
        self.updating = False
        self.auto = None
        self.last_data = None
        self.last_range = (0.0, 1000.0)
        self.slider_ceiling = 2000.0

    @staticmethod
    def valid(low, high):
        return (not math.isnan(low) and not math.isinf(low) and
                not math.isnan(high) and not math.isinf(high) and high > low and
                not math.isinf(high - low))

    def put(self, index, value):
        if self.read(index) != value:
            self.write(index, value)

    def publish(self, low, high):
        self.last_range = (low, high)
        self.put(1, low)
        self.put(2, high)
        span = high - low
        if self.auto or high >= self.slider_ceiling or low >= self.slider_ceiling:
            # Keep headroom stable while dragging. Numeric entry can extend it.
            ceiling = high + span
            self.slider_ceiling = ceiling if not math.isinf(ceiling) else high
        self.slider.setPropertyValue("minimum", low)
        self.slider.setPropertyValue("maximum", self.slider_ceiling)
        self.slider.setPropertyValue("increment", max(1.0, span / 1000.0))

    def synchronize(self):
        with self.lock:
            if self.updating:
                return
            self.updating = True
            try:
                requested_auto = self.read(0) != 0
                if requested_auto:
                    data = self.data()
                    if self.auto is not True or data != self.last_data:
                        low, high = self.bounds()
                        # Flat frames still need a nonzero color-bar span.
                        if low == high:
                            low, high = min(0.0, low), max(1.0, high)
                        self.last_data = data
                    else:
                        low, high = self.last_range
                elif self.auto:
                    # Freeze the exact range last applied, even when a new
                    # waveform arrives before the mode-change script runs.
                    low, high = self.last_range
                else:
                    low, high = self.read(1), self.read(2)
                self.auto = requested_auto

                if not self.valid(low, high):
                    low, high = self.last_range
                    message = "Invalid limits;\nprevious range restored."
                else:
                    message = "Auto: full image" if self.auto else "Manual: drag upper limit"

                self.image.setPropertyValue("autoscale", False)
                self.image.setPropertyValue("minimum", low)
                self.image.setPropertyValue("maximum", high)
                self.publish(low, high)
                self.hint.setPropertyValue("text", message)
            finally:
                self.updating = False


def install(image, inputs):
    from java.util import Arrays
    from org.csstudio.display.builder.runtime.script import PVUtil, ScriptUtil

    key = "tpx4_image_intensity"
    control = image.getUserData(key)
    if control is None:
        name = str(image.getPropertyValue("name"))
        slider = ScriptUtil.findWidgetByName(image, name + "ScaleSlider")
        hint = ScriptUtil.findWidgetByName(image, name + "ScaleHint")

        def bounds():
            values = PVUtil.getDoubleArray(inputs[3])
            stats = Arrays.stream(values).summaryStatistics()
            return stats.getMin(), stats.getMax()

        control = ImageIntensity(image, slider, hint,
                                 lambda index: PVUtil.getDouble(inputs[index]),
                                 lambda index, value: inputs[index].write(value),
                                 lambda: PVUtil.getVType(inputs[3]), bounds)
        image.setUserData(key, control)
    control.synchronize()


if "widget" in globals() and "pvs" in globals():
    install(widget, pvs)
