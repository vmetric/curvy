import sys
import os
import json
try:
    from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                                   QPushButton, QLabel, QSlider, QGridLayout, QComboBox,
                                   QInputDialog, QMessageBox, QScrollArea, QSizePolicy,
                                   QMenu)
    from PySide6.QtCore import Qt, QPointF, QRectF, Signal
    from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush, QFont, QPolygonF
except ImportError:
    print("Error: PySide6 is not installed. Please install it using 'pip install PySide6'.")
    sys.exit(1)

# --- Custom Presets Persistence ---
def get_presets_file_path():
    """Returns the path to the custom presets JSON file, next to this script."""
    try:
        script_path = os.path.abspath(__file__)
    except NameError:
        # __file__ is not defined when running inside DaVinci Resolve
        if sys.argv and sys.argv[0]:
            script_path = os.path.abspath(sys.argv[0])
        else:
            # Last resort: use platform-specific Fusion scripts directory
            if sys.platform == 'win32':
                base = os.environ.get('APPDATA', os.path.expanduser('~'))
                script_dir = os.path.join(base, 'Blackmagic Design', 'DaVinci Resolve',
                                          'Support', 'Fusion', 'Scripts', 'Comp')
            elif sys.platform == 'darwin':
                script_dir = os.path.expanduser(
                    '~/Library/Application Support/Blackmagic Design/'
                    'DaVinci Resolve/Fusion/Scripts/Comp')
            else:
                script_dir = os.path.expanduser(
                    '~/.local/share/DaVinciResolve/Fusion/Scripts/Comp')
            return os.path.join(script_dir, "Curvy_presets.json")
    script_dir = os.path.dirname(script_path)
    return os.path.join(script_dir, "Curvy_presets.json")

# --- DaVinci Resolve Integration Stub ---
# Resolve injects 'fusion', 'resolve', and 'bmd' into the global namespace
# when launching a script from the menu.

_FUSION_INSTANCE = None

def _init_fusion():
    global _FUSION_INSTANCE
    # 1. Check globals (if injected directly)
    if 'fusion' in globals():
        _FUSION_INSTANCE = globals()['fusion']
        return
    if 'resolve' in globals():
        _FUSION_INSTANCE = globals()['resolve'].Fusion()
        return

    # 2. Check built-ins
    try:
        import builtins
        if hasattr(builtins, 'fusion'):
            _FUSION_INSTANCE = builtins.fusion
            return
        if hasattr(builtins, 'resolve'):
            _FUSION_INSTANCE = builtins.resolve.Fusion()
            return
    except Exception:
        pass

    # 3. Check __main__ builtins (where Resolve usually injects them)
    try:
        import __main__
        if hasattr(__main__, 'fusion'):
            _FUSION_INSTANCE = __main__.fusion
            return
        if hasattr(__main__, 'resolve'):
            _FUSION_INSTANCE = __main__.resolve.Fusion()
            return
    except Exception:
        pass

    # 4. Try to initialize via fusionscript module
    try:
        import fusionscript as bmd
        f = bmd.scriptapp("Fusion")
        if f:
            _FUSION_INSTANCE = f
            return
        r = bmd.scriptapp("Resolve")
        if r:
            _FUSION_INSTANCE = r.Fusion()
            return
    except Exception:
        pass

    # 5. Try via DaVinciResolveScript
    try:
        import DaVinciResolveScript as dvr_script
        r = dvr_script.scriptapp("Resolve")
        if r:
            _FUSION_INSTANCE = r.Fusion()
            return
        f = dvr_script.scriptapp("Fusion")
        if f:
            _FUSION_INSTANCE = f
            return
    except Exception:
        pass

_init_fusion()

def get_fusion():
    global _FUSION_INSTANCE
    return _FUSION_INSTANCE

def apply_easing_to_resolve(control_points):
    """
    Applies the bezier curve to the active tool in the active Fusion comp.
    control_points is a list of [x1, y1, x2, y2] representing the two bezier handles.
    """
    fusion = get_fusion()
    if not fusion:
        print(f"Error: Could not connect to Fusion API.")
        print(f"[Debug - Not in Resolve] Applying curve: {control_points}")
        return 0

    comp = fusion.GetCurrentComp()
    if not comp:
        print("No active Fusion Composition. Please open a Fusion composition.")
        return 0

    tool = comp.ActiveTool
    if not tool:
        print("No active tool selected in Fusion.")
        return 0

    # Fusion bezier handles are defined by (x, y) relative to the keyframe.
    # We need to map [x1, y1, x2, y2] to Fusion's Handle values.
    # This involves iterating through inputs, finding BezierSplines, and modifying handles.
    # Due to API complexity, this is a simplified stub showing the process.

    x1, y1, x2, y2 = control_points

    inputs = tool.GetInputList()
    applied_count = 0

    comp.Lock()
    comp.StartUndo("Curvy Apply Easing")

    # Handle COM objects that might not have items()
    if hasattr(inputs, "items") and callable(getattr(inputs, "items")):
        items_iter = inputs.items()
    elif hasattr(inputs, "keys") and callable(getattr(inputs, "keys")):
        items_iter = [(k, inputs[k]) for k in inputs.keys()]
    else:
        items_iter = [(k, inputs[k]) for k in inputs]

    for input_id, input_obj in items_iter:
        connected = input_obj.GetConnectedOutput()
        if connected:
            spline = connected.GetTool()
            if spline and spline.ID == "BezierSpline":
                all_keyframes = spline.GetKeyFrames()
                if not all_keyframes or len(all_keyframes) < 2:
                    continue

                # Check for selected keyframes
                selected_keyframes = {}
                try:
                    selected_keyframes = spline.GetSelectedKeyFrames()
                except Exception:
                    pass

                if not selected_keyframes or len(selected_keyframes) < 2:
                    target_keyframes = all_keyframes
                else:
                    target_keyframes = selected_keyframes

                # Sort target keyframes by time
                if hasattr(target_keyframes, "keys") and callable(getattr(target_keyframes, "keys")):
                    times = sorted(target_keyframes.keys())
                else:
                    times = sorted([k for k in target_keyframes])

                # Normalize all keyframes to dictionary format for safety
                new_keyframes = {}

                if hasattr(all_keyframes, "items") and callable(getattr(all_keyframes, "items")):
                    kf_iter = all_keyframes.items()
                elif hasattr(all_keyframes, "keys") and callable(getattr(all_keyframes, "keys")):
                    kf_iter = [(k, all_keyframes[k]) for k in all_keyframes.keys()]
                else:
                    kf_iter = [(k, all_keyframes[k]) for k in all_keyframes]

                for t, kf_val in kf_iter:
                    if isinstance(kf_val, (int, float)):
                        new_keyframes[t] = {1: float(kf_val), 'LH': {1: 0.0, 2: 0.0}, 'RH': {1: 0.0, 2: 0.0}}
                    else:
                        new_keyframes[t] = dict(kf_val)
                        if 'LH' not in new_keyframes[t]:
                            new_keyframes[t]['LH'] = {1: 0.0, 2: 0.0}
                        if 'RH' not in new_keyframes[t]:
                            new_keyframes[t]['RH'] = {1: 0.0, 2: 0.0}

                # Apply easing between sequential target keyframes
                for i in range(len(times) - 1):
                    t1 = times[i]
                    t2 = times[i+1]
                    v1 = new_keyframes[t1].get(1, new_keyframes[t1].get(1.0, new_keyframes[t1].get('1', new_keyframes[t1].get('1.0', 0.0))))
                    v2 = new_keyframes[t2].get(1, new_keyframes[t2].get(1.0, new_keyframes[t2].get('1', new_keyframes[t2].get('1.0', 0.0))))

                    dt = t2 - t1
                    dv = v2 - v1

                    # Fusion handles are RELATIVE to the keyframe
                    rh_x = float(x1 * dt)
                    rh_y = float(y1 * dv)

                    lh_x = float((x2 - 1.0) * dt)
                    lh_y = float((y2 - 1.0) * dv)

                    new_keyframes[t1]['RH'] = {1: rh_x, 2: rh_y}
                    new_keyframes[t2]['LH'] = {1: lh_x, 2: lh_y}

                # Apply the newly constructed keyframes back to the spline
                spline.SetKeyFrames(new_keyframes)
                print(f"Applied curve ({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f}) to {input_id}")

                applied_count += 1

    comp.EndUndo(True)
    comp.Unlock()

    print(f"Applied easing to {applied_count} parameters on {tool.Name}.")
    return applied_count


# --- UI Components ---

class BezierCurveEditor(QWidget):
    curveChanged = Signal(list) # Emits [x1, y1, x2, y2]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.setMaximumSize(500, 500)

        # Grid dimensions
        self.margin_x = 40
        self.margin_y = 70
        self.zoom = 1.0

        # Control points (normalized 0-1)
        # Default is a linear curve
        self.p1 = QPointF(0.0, 0.0) # Bottom Left (Start)
        self.p2 = QPointF(1.0, 1.0) # Top Right (End)
        self.cp1 = QPointF(0.25, 0.25) # Handle 1
        self.cp2 = QPointF(0.75, 0.75) # Handle 2

        self.dragging = None
        self.handle_radius = 6

        # Colors (Dark Theme)
        self.bg_color = QColor(40, 40, 45)
        self.grid_color = QColor(80, 80, 90)
        self.curve_color = QColor(100, 150, 255)
        self.handle_line_color = QColor(150, 150, 150)
        self.handle_color = QColor(200, 200, 200)
        self.active_handle_color = QColor(255, 255, 255)

    def get_bezier_values(self):
        # Y is flipped in screen coordinates (0 is top), so we invert it for standard math
        return [
            self.cp1.x(),
            1.0 - self.cp1.y(),
            self.cp2.x(),
            1.0 - self.cp2.y()
        ]

    def set_bezier_values(self, x1, y1, x2, y2):
        self.cp1 = QPointF(x1, 1.0 - y1)
        self.cp2 = QPointF(x2, 1.0 - y2)
        self.update()
        self.curveChanged.emit(self.get_bezier_values())

    def _get_margins(self):
        # Calculate dynamic margins based on zoom level
        w = self.width()
        h = self.height()

        gw = max(1, w - self.margin_x * 2)
        gh = max(1, h - self.margin_y * 2)

        new_gw = gw / self.zoom
        new_gh = gh / self.zoom

        mx = (w - new_gw) / 2.0
        my = (h - new_gh) / 2.0
        return int(mx), int(my)

    def set_zoom(self, value):
        self.zoom = value
        self.update()

    def _to_screen(self, p):
        # Convert normalized 0-1 coordinates to screen coordinates
        mx, my = self._get_margins()
        rect = self.rect().adjusted(mx, my, -mx, -my)
        w = rect.width()
        h = rect.height()
        # Note: Y is NOT inverted here because p.y() is already in screen-relative space (0 is top)
        # However, visually, we want bottom-left to be (0,0). So the points are stored such that
        # when y=1.0, it's at the bottom of the screen.
        return QPointF(rect.left() + p.x() * w, rect.top() + p.y() * h)

    def _to_normalized(self, pos):
        # Convert screen coordinates to normalized 0-1
        mx, my = self._get_margins()
        rect = self.rect().adjusted(mx, my, -mx, -my)
        w = rect.width()
        h = rect.height()

        # Clamp to bounds (0 to 1) for X, allow slightly outside for Y (overshoot/undershoot)
        x = max(0.0, min(1.0, (pos.x() - rect.left()) / w))
        y = (pos.y() - rect.top()) / h

        return QPointF(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw Background
        painter.fillRect(self.rect(), self.bg_color)

        mx, my = self._get_margins()
        rect = self.rect().adjusted(mx, my, -mx, -my)

        # Draw Grid
        painter.setPen(QPen(self.grid_color, 1, Qt.SolidLine))
        painter.drawRect(rect)

        # Draw diagonals / internal lines
        painter.setPen(QPen(self.grid_color, 1, Qt.DotLine))
        painter.drawLine(rect.bottomLeft(), rect.topRight())

        # Convert points
        s_p1 = self._to_screen(QPointF(0, 1)) # Bottom left
        s_p2 = self._to_screen(QPointF(1, 0)) # Top right
        s_cp1 = self._to_screen(self.cp1)
        s_cp2 = self._to_screen(self.cp2)

        # Draw Handle Lines
        painter.setPen(QPen(self.handle_line_color, 1, Qt.SolidLine))
        painter.drawLine(s_p1, s_cp1)
        painter.drawLine(s_p2, s_cp2)

        # Draw Curve
        path = QPainterPath()
        path.moveTo(s_p1)
        path.cubicTo(s_cp1, s_cp2, s_p2)

        painter.setPen(QPen(self.curve_color, 3, Qt.SolidLine))
        painter.drawPath(path)

        # Draw Handles
        for i, cp in enumerate([s_cp1, s_cp2]):
            handle_rect = QRectF(cp.x() - self.handle_radius, cp.y() - self.handle_radius,
                                 self.handle_radius * 2, self.handle_radius * 2)
            if self.dragging == i:
                painter.setBrush(QBrush(self.active_handle_color))
            else:
                painter.setBrush(QBrush(self.handle_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(handle_rect)

        # Draw Text (Values)
        vals = self.get_bezier_values()
        text = f"cubic-bezier({vals[0]:.2f}, {vals[1]:.2f}, {vals[2]:.2f}, {vals[3]:.2f})"
        painter.setPen(QPen(Qt.white))
        painter.setFont(QFont("Consolas", 9))
        painter.drawText(self.rect().adjusted(10, 10, -10, -10), Qt.AlignTop | Qt.AlignHCenter, text)


    def mousePressEvent(self, event):
        pos = event.position()
        s_cp1 = self._to_screen(self.cp1)
        s_cp2 = self._to_screen(self.cp2)

        # Check if we clicked near a handle
        if (s_cp1 - pos).manhattanLength() < self.handle_radius * 2:
            self.dragging = 0
        elif (s_cp2 - pos).manhattanLength() < self.handle_radius * 2:
            self.dragging = 1

        if self.dragging is not None:
            self.update()

    def mouseMoveEvent(self, event):
        if self.dragging is not None:
            norm_pos = self._to_normalized(event.position())
            if self.dragging == 0:
                self.cp1 = norm_pos
            elif self.dragging == 1:
                self.cp2 = norm_pos

            self.update()
            self.curveChanged.emit(self.get_bezier_values())

    def mouseReleaseEvent(self, event):
        if self.dragging is not None:
            self.dragging = None
            self.update()

class PresetButton(QWidget):
    clicked = Signal(str)
    overwrite_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, name, values, is_custom=False, parent=None):
        super().__init__(parent)
        self.name = name
        self.values = values
        self.is_custom = is_custom
        self.setFixedSize(100, 100)
        self.is_selected = False

        self.bg_color = QColor(45, 45, 50)
        self.hover_color = QColor(55, 55, 60)
        self.selected_color = QColor(70, 70, 80)
        self.curve_color = QColor(150, 150, 150)
        self.selected_curve_color = QColor(100, 150, 255)
        self.custom_border_color = QColor(255, 180, 50)  # Orange for custom presets
        self.is_hovered = False
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def _show_context_menu(self, pos):
        if not self.is_custom:
            return
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #5a5a5a;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #505060;
            }
        """)
        overwrite_action = menu.addAction("✏️ Overwrite Preset")
        delete_action = menu.addAction("🗑️ Delete Preset")
        action = menu.exec(self.mapToGlobal(pos))
        if action == overwrite_action:
            self.overwrite_requested.emit(self.name)
        elif action == delete_action:
            self.delete_requested.emit(self.name)

    def mousePressEvent(self, event):
        # Check standard and explicit enum for button to avoid PySide discrepancies
        if event.button() == Qt.LeftButton or event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.name)
        super().mousePressEvent(event)

    def set_selected(self, selected):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        if self.is_selected:
            painter.setBrush(QBrush(self.selected_color))
        elif self.is_hovered:
            painter.setBrush(QBrush(self.hover_color))
        else:
            painter.setBrush(QBrush(self.bg_color))

        if self.is_selected:
            if self.is_custom:
                painter.setPen(QPen(self.custom_border_color, 2))
            else:
                painter.setPen(QPen(QColor(100, 150, 255), 2))
        else:
            if self.is_custom:
                painter.setPen(QPen(QColor(200, 140, 40), 1))
            else:
                painter.setPen(QPen(QColor(60, 60, 65), 1))

        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        # Draw custom preset indicator (small diamond in top-right)
        if self.is_custom:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.custom_border_color))
            # QPolygonF imported at top level
            diamond = QPolygonF()
            cx, cy = rect.width() - 12, 10
            d = 4
            diamond.append(QPointF(cx, cy - d))
            diamond.append(QPointF(cx + d, cy))
            diamond.append(QPointF(cx, cy + d))
            diamond.append(QPointF(cx - d, cy))
            painter.drawPolygon(diamond)

        # Draw a safer inner bounding box that accommodates overshoots
        margin_x = 15
        margin_y = 15
        text_height = 25
        w = rect.width() - margin_x * 2
        h = rect.height() - margin_y * 2 - text_height

        # Scale graph vertically by 50% so handles like y=1.6 or y=-0.6 fit safely inside
        graph_h = h * 0.5
        offset_y = margin_y + h * 0.25

        x1, y1, x2, y2 = self.values

        s_p1 = QPointF(margin_x, offset_y + graph_h)
        s_p2 = QPointF(margin_x + w, offset_y)

        s_cp1 = QPointF(margin_x + x1 * w, offset_y + graph_h - y1 * graph_h)
        s_cp2 = QPointF(margin_x + x2 * w, offset_y + graph_h - y2 * graph_h)

        path = QPainterPath()
        path.moveTo(s_p1)
        path.cubicTo(s_cp1, s_cp2, s_p2)

        c_color = self.selected_curve_color if self.is_selected else self.curve_color
        painter.setPen(QPen(c_color, 2, Qt.SolidLine))
        painter.drawPath(path)

        # Draw start/end dots
        painter.setBrush(QBrush(c_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(s_p1, 2, 2)
        painter.drawEllipse(s_p2, 2, 2)

        if self.is_selected:
            painter.setPen(QPen(QColor(255, 255, 255)))
        else:
            painter.setPen(QPen(QColor(180, 180, 180)))

        painter.setFont(QFont("Arial", 8))
        text_rect = QRectF(0, rect.height() - text_height, rect.width(), 20)
        painter.drawText(text_rect, Qt.AlignCenter, self.name)

class Curvy(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Curvy")
        self.resize(750, 480)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #5a5a5a;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #666666;
            }
        """)

        # Built-in presets (cannot be modified)
        self.builtin_presets = {
            "Linear": (0.0, 0.0, 1.0, 1.0),
            "Ease": (0.25, 0.1, 0.25, 1.0),
            "Ease In": (0.42, 0.0, 1.0, 1.0),
            "Ease Out": (0.0, 0.0, 0.58, 1.0),
            "Ease In Out": (0.42, 0.0, 0.58, 1.0),
            "Back In": (0.36, 0, 0.66, -0.56),
            "Back Out": (0.34, 1.56, 0.64, 1),
            "Back In Out": (0.68, -0.6, 0.32, 1.6)
        }

        # Custom presets (loaded from JSON, can be modified)
        self.custom_presets = self._load_custom_presets_from_file()

        # Combined presets for lookup
        self.presets = {}
        self.presets.update(self.builtin_presets)
        self.presets.update(self.custom_presets)

        # Track currently selected preset
        self.selected_preset_name = None
        self.selected_is_custom = False


        main_layout = QHBoxLayout(self)

        # Left side: Presets Grid with scroll area
        left_widget = QWidget()
        left_widget.setFixedWidth(340)
        left_outer_layout = QVBoxLayout(left_widget)
        left_outer_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for presets
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.presets_container = QWidget()
        self.presets_grid_layout = QGridLayout(self.presets_container)
        self.presets_grid_layout.setSpacing(10)

        scroll_area.setWidget(self.presets_container)
        left_outer_layout.addWidget(scroll_area)

        # Buttons for custom presets
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setToolTip("Save current curve as a new custom preset")
        self.save_btn.clicked.connect(self.save_preset)
        left_outer_layout.addWidget(self.save_btn)

        main_layout.addWidget(left_widget, 0)

        # Right side: Editor
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Header
        header = QLabel("Easing Curve Editor")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(header)

        # Editor
        self.editor = BezierCurveEditor()
        self.editor.curveChanged.connect(self.on_curve_changed)
        right_layout.addWidget(self.editor)

        # Zoom Slider
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom Graph Out:")
        zoom_label.setStyleSheet("color: #aaaaaa;")
        zoom_layout.addWidget(zoom_label)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10) # 1.0x
        self.zoom_slider.setMaximum(40) # 4.0x
        self.zoom_slider.setValue(10)
        self.zoom_slider.valueChanged.connect(lambda v: self.editor.set_zoom(v / 10.0))
        zoom_layout.addWidget(self.zoom_slider)
        right_layout.addLayout(zoom_layout)

        # Apply Button
        self.apply_btn = QPushButton("Apply to Selected Tool in Fusion")
        self.apply_btn.setMinimumHeight(40)
        self.apply_btn.clicked.connect(self.apply_curve)
        right_layout.addWidget(self.apply_btn)

        # Status Label
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        right_layout.addWidget(self.status_label)

        main_layout.addWidget(right_widget, 1)

        # Build preset buttons
        self.preset_buttons = {}
        self._rebuild_preset_grid()

        # Initial Load
        self.load_preset("Ease In Out")

    def _load_custom_presets_from_file(self):
        """Load custom presets from JSON file."""
        try:
            path = get_presets_file_path()
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                # Validate and convert to tuples
                presets = {}
                for name, vals in data.items():
                    if isinstance(vals, (list, tuple)) and len(vals) == 4:
                        presets[name] = tuple(float(v) for v in vals)
                return presets
        except Exception as e:
            print(f"Warning: Could not load custom presets: {e}")
        return {}

    def _save_custom_presets_to_file(self):
        """Save custom presets to JSON file."""
        try:
            path = get_presets_file_path()
            with open(path, 'w') as f:
                json.dump(self.custom_presets, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save custom presets: {e}")

    def _rebuild_preset_grid(self):
        """Rebuild all preset buttons in the grid layout."""
        # Clear existing buttons
        for btn in self.preset_buttons.values():
            self.presets_grid_layout.removeWidget(btn)
            btn.deleteLater()
        self.preset_buttons.clear()

        # Combine presets: built-in first, then custom
        all_presets = list(self.builtin_presets.items()) + list(self.custom_presets.items())

        row, col = 0, 0
        for name, vals in all_presets:
            is_custom = name in self.custom_presets
            btn = PresetButton(name, vals, is_custom=is_custom)
            btn.clicked.connect(self.load_preset)
            btn.overwrite_requested.connect(self.overwrite_preset)
            btn.delete_requested.connect(self.delete_preset)
            self.preset_buttons[name] = btn
            self.presets_grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        self.presets_grid_layout.setRowStretch(row + 1, 1)

    def load_preset(self, name):
        if name in self.presets:
            # Track selection
            self.selected_preset_name = name
            self.selected_is_custom = name in self.custom_presets
            # Update selection visuals
            for btn_name, btn in self.preset_buttons.items():
                btn.set_selected(btn_name == name)

            # Block signals so on_curve_changed doesn't fire and override
            # our selection with a float-comparison mismatch
            self.editor.blockSignals(True)
            p = self.presets[name]
            self.editor.set_bezier_values(*p)
            self.editor.blockSignals(False)

    def on_curve_changed(self, vals):
        # Check if curve matches any preset
        matched = False
        for name, p in self.presets.items():
            if all(abs(a - b) < 0.015 for a, b in zip(p, vals)):
                self.preset_buttons[name].set_selected(True)
                self.selected_preset_name = name
                self.selected_is_custom = name in self.custom_presets
                matched = True
            else:
                self.preset_buttons[name].set_selected(False)

        if not matched:
            self.selected_preset_name = None
            self.selected_is_custom = False

    def save_preset(self):
        """Save the current curve as a new custom preset."""
        vals = self.editor.get_bezier_values()

        # Suggest a default name
        default_name = "Custom"
        counter = 1
        while default_name in self.presets:
            counter += 1
            default_name = f"Custom {counter}"

        name, ok = QInputDialog.getText(
            self, "Save Preset", "Enter a name for this preset:",
            text=default_name
        )

        if not ok or not name.strip():
            return

        name = name.strip()

        if name in self.builtin_presets:
            QMessageBox.warning(self, "Cannot Overwrite",
                f"'{name}' is a built-in preset and cannot be overwritten.\n"
                f"Please choose a different name.")
            return

        if name in self.custom_presets:
            result = QMessageBox.question(self, "Preset Exists",
                f"A custom preset named '{name}' already exists.\n"
                f"Do you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if result != QMessageBox.Yes:
                return

        self.custom_presets[name] = tuple(vals)
        self.presets[name] = tuple(vals)
        self._save_custom_presets_to_file()
        self._rebuild_preset_grid()
        self.load_preset(name)
        self.status_label.setText(f"Saved preset '{name}'.")
        self.status_label.setStyleSheet("color: #55ff55; font-size: 11px;")

    def overwrite_preset(self, name=None):
        """Overwrite the selected custom preset with the current curve values."""
        if name is None:
            name = self.selected_preset_name

        if not name or name not in self.custom_presets:
            QMessageBox.information(self, "No Custom Preset Selected",
                "Please select a custom preset to edit.\n"
                "(Built-in presets cannot be modified.)")
            return

        vals = self.editor.get_bezier_values()
        self.custom_presets[name] = tuple(vals)
        self.presets[name] = tuple(vals)
        self._save_custom_presets_to_file()
        self._rebuild_preset_grid()
        self.load_preset(name)
        self.status_label.setText(f"Updated preset '{name}'.")
        self.status_label.setStyleSheet("color: #55ff55; font-size: 11px;")

    def delete_preset(self, name=None):
        """Delete the selected custom preset."""
        if name is None:
            name = self.selected_preset_name

        if not name or name not in self.custom_presets:
            QMessageBox.information(self, "No Custom Preset Selected",
                "Please select a custom preset to delete.\n"
                "(Built-in presets cannot be deleted.)")
            return

        result = QMessageBox.question(self, "Delete Preset",
            f"Are you sure you want to delete the preset '{name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if result != QMessageBox.Yes:
            return

        del self.custom_presets[name]
        del self.presets[name]
        self.selected_preset_name = None
        self.selected_is_custom = False
        self._save_custom_presets_to_file()
        self._rebuild_preset_grid()

        self.status_label.setText(f"Deleted preset '{name}'.")
        self.status_label.setStyleSheet("color: #ffaa00; font-size: 11px;")

    def apply_curve(self):
        vals = self.editor.get_bezier_values()
        try:
            count = apply_easing_to_resolve(vals)
            if count is not None and count > 0:
                self.status_label.setText(f"Success! Applied to {count} parameter(s).")
                self.status_label.setStyleSheet("color: #55ff55; font-size: 12px; font-weight: bold;")
            else:
                self.status_label.setText("No keyframes found on selected tool.")
                self.status_label.setStyleSheet("color: #ffaa00; font-size: 11px;")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: #ff5555; font-size: 11px;")

if __name__ == "__main__":
    # If app exists, use it (sometimes Resolve scripts context provides one)
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = Curvy()
    window.show()

    # We must start the event loop if running outside of a blocking script environment
    sys.exit(app.exec())
