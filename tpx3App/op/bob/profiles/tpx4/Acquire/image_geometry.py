"""Fit Phoebus images with square pixels, allowing for axes and color bar.

Jython inputs: image width, image height, waveform, selected view. The latter
two trigger a check after a hidden plot becomes visible or receives data.
All scene access and delayed layout checks run on the JavaFX application thread.
"""
from __future__ import division

import math


def fitted_size(pixel_width, pixel_height, available_width, available_height,
                horizontal_margin, vertical_margin):
    """Largest whole-pixel widget size that fits without stretching the raster."""
    values = (pixel_width, pixel_height, available_width, available_height,
              horizontal_margin, vertical_margin)
    if any(math.isnan(v) or math.isinf(v) for v in values):
        return None
    if (pixel_width <= 0 or pixel_height <= 0 or horizontal_margin < 0 or
            vertical_margin < 0 or available_width <= horizontal_margin or
            available_height <= vertical_margin):
        return None
    scale = min((available_width - horizontal_margin) / pixel_width,
                (available_height - vertical_margin) / pixel_height)
    return (int(math.floor(horizontal_margin + pixel_width * scale + 0.5)),
            int(math.floor(vertical_margin + pixel_height * scale + 0.5)))


def install(image, inputs):
    from javafx.animation import PauseTransition
    from javafx.application import Platform
    from javafx.util import Duration
    from org.csstudio.display.builder.representation.javafx.widgets import JFXBaseRepresentation
    from org.csstudio.display.builder.runtime.script import PVUtil

    # PV callbacks run off the FX thread. Capture values before queuing the task.
    try:
        dimensions = (PVUtil.getDouble(inputs[0]), PVUtil.getDouble(inputs[1]))
    except Exception:
        return  # Disconnected dimensions leave the existing display intact.

    def request():
        controller = image.getUserData('tpx4_image_geometry')
        if controller is None:
            class Geometry(object):
                def __init__(self):
                    self.available_width = image.getPropertyValue('width')
                    self.available_height = image.getPropertyValue('height')
                    self.dimensions = None
                    self.remaining = 0
                    self.timer = PauseTransition(Duration.millis(250))
                    self.timer.setOnFinished(lambda event: self.check())

                def check(self):
                    self.remaining -= 1
                    node = JFXBaseRepresentation.getJFXNode(image)
                    if node is None or node.getScene() is None:
                        self.remaining = 0
                        return
                    # ImageRepresentation's Pane contains the native RTImagePlot.
                    # Use its public axes; do not reflect into private plot fields.
                    plot = node.getChildren().get(0)
                    x_bounds = plot.getXAxis().getBounds()
                    y_bounds = plot.getYAxis().getBounds()
                    outer_width = int(round(plot.getWidth()))
                    outer_height = int(round(plot.getHeight()))
                    # Axes are laid out asynchronously. Ignore their initial bounds
                    # and any sample taken before the widget resize reaches JavaFX.
                    if (x_bounds.y == y_bounds.height and x_bounds.y > 0 and
                            x_bounds.width > 0 and y_bounds.height > 0 and
                            outer_width == image.getPropertyValue('width') and
                            outer_height == image.getPropertyValue('height')):
                        target = fitted_size(
                            self.dimensions[0], self.dimensions[1],
                            self.available_width, self.available_height,
                            outer_width - x_bounds.width,
                            outer_height - y_bounds.height)
                        if target is not None:
                            for name, value in zip(('width', 'height'), target):
                                if image.getPropertyValue(name) != value:
                                    image.setPropertyValue(name, value)
                    if self.remaining > 0:
                        self.timer.playFromStart()

            controller = Geometry()
            image.setUserData('tpx4_image_geometry', controller)
        controller.dimensions = dimensions
        # Coalesce acquisition updates. Each burst has a finite lifetime, including
        # when a display is closed. No worker thread or perpetual timer is created.
        if controller.remaining <= 0:
            controller.remaining = 4
            controller.check()

    Platform.runLater(request)


if 'widget' in globals() and 'pvs' in globals():
    install(widget, pvs)
