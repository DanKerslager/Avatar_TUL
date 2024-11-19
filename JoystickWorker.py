import wx
import math


class JoystickPanel(wx.Panel):
    def __init__(self, parent, move_callback):
        wx.Panel.__init__(self, parent, size=(200, 100))  # Wider than it is tall
        self.SetBackgroundColour(wx.Colour(220, 220, 220))
        self.SetMinSize((200, 100))
        self.move_callback = move_callback

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_move)

        # Center of the oval
        self.center = (100, 50)
        # Oval dimensions
        self.oval_radius_x = 90  # Horizontal radius
        self.oval_radius_y = 40  # Vertical radius
        # Joystick properties
        self.joystick_radius = 15
        self.joystick_position = list(self.center)  # Current position of the joystick
        self.dragging = False

        # Define the output ranges for horizontal and vertical movement
        self.horizontal_range = (-2.0857, 2.0857)
        self.vertical_range = (-0.6720, 0.5149)

    def on_paint(self, event):
        dc = wx.PaintDC(self)

        # Draw the boundary oval
        dc.SetBrush(wx.Brush(wx.Colour(240, 240, 240)))
        dc.SetPen(wx.Pen(wx.Colour(100, 100, 100), 2))
        dc.DrawEllipse(self.center[0] - self.oval_radius_x, self.center[1] - self.oval_radius_y,
                       self.oval_radius_x * 2, self.oval_radius_y * 2)

        # Draw the joystick (which is always a circle)
        dc.SetBrush(wx.Brush(wx.Colour(100, 100, 250)))
        dc.DrawCircle(self.joystick_position[0], self.joystick_position[1], self.joystick_radius)

    def on_mouse_down(self, event):
        if self._within_circle(event.GetPosition(), self.joystick_position, self.joystick_radius):
            self.dragging = True

    def on_mouse_up(self, event):
        self.dragging = False
        # Reset joystick to the center
        self.joystick_position = list(self.center)
        self.Refresh()  # Redraw joystick
        self.move_callback(0, 0)  # Send neutral position to move_head

    def on_mouse_move(self, event):
        if self.dragging:
            pos = event.GetPosition()
            # Calculate relative position within the oval
            dx = (pos.x - self.center[0]) / float(self.oval_radius_x)
            dy = (pos.y - self.center[1]) / float(self.oval_radius_y)

            # Limit movement within the oval using the ellipse equation (dx^2 + dy^2 <= 1)
            if (dx ** 2 + dy ** 2) <= 1:
                self.joystick_position = [pos.x, pos.y]
            else:
                # Adjust position to be on the ellipse boundary
                angle = math.atan2(dy, dx)
                self.joystick_position = [
                    self.center[0] + self.oval_radius_x * math.cos(angle),
                    self.center[1] + self.oval_radius_y * math.sin(angle)
                ]

            self.Refresh()

            # Normalize the joystick values to be between -1 and 1
            x_normalized = (self.joystick_position[0] - self.center[0]) / float(self.oval_radius_x)
            y_normalized = (self.joystick_position[1] - self.center[1]) / float(self.oval_radius_y)

            # Scale the normalized values to the desired output ranges
            x_scaled = self._scale_value(x_normalized, -1, 1, self.horizontal_range[0], self.horizontal_range[1])
            y_scaled = self._scale_value(y_normalized, -1, 1, self.vertical_range[0], self.vertical_range[1])

            # Send the scaled position to move_head
            self.move_callback(x_scaled, y_scaled)

    def _scale_value(self, value, old_min, old_max, new_min, new_max):
        # Scale a value from one range to another
        return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

    def _within_circle(self, pos, center, radius):
        dx = pos.x - center[0]
        dy = pos.y - center[1]
        return (dx ** 2 + dy ** 2) <= radius ** 2
