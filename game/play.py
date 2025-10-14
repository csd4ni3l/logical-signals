import arcade, arcade.gui, random, datetime

from utils.utils import cubic_bezier_points, get_gate_port_position, generate_task_text
from utils.constants import dropdown_style, LOGICAL_GATES, LEVELS

from datetime import datetime

class LogicalGate(arcade.gui.UIBoxLayout):
    def __init__(self, id, x, y, gate_type, value):
        super().__init__(x=x, y=y, space_between=2, vertical=False)

        self.id = id
        self.gate_type = gate_type

        if gate_type == "INPUT":
            self.value = value
        else:
            self.value = 0

        self.input_add_button = self.add(arcade.gui.UIFlatButton(text="+", style=dropdown_style, height=30, width=30))
        self.input_add_button.visible = not self.gate_type == "INPUT"

        self.gate_button = self.add(arcade.gui.UIFlatButton(text=f"{gate_type} ({self.value})", style=dropdown_style, height=30, width=120))
        
        self.output_add_button = self.add(arcade.gui.UIFlatButton(text="+", style=dropdown_style, height=30, width=30))
        self.output_add_button.visible = not self.gate_type == "OUTPUT"
        
        self.input: list[LogicalGate] = []
        self.output: LogicalGate | None = None

    def calculate_value(self):
        if self.gate_type == "OUTPUT" and self.input:
            self.value = self.input[0].calculate_value()
        elif self.gate_type == "INPUT": # dont set INPUT to None
            pass
        elif len(self.input) == 2:
            self.value = int(LOGICAL_GATES[self.gate_type](self.input[0].calculate_value(), self.input[1].calculate_value())) # have to convert to int cause it might return boolean
        else:
            self.value = None

        self.gate_button.text = f"{self.gate_type} ({self.value})"
        return self.value
        
    def __repr__(self):
        return f"{self.gate_type}: {self.value}"

class Game(arcade.gui.UIView):
    def __init__(self, pypresence_client, level_num):
        super().__init__()

        self.pypresence_client = pypresence_client
        self.pypresence_client.update(state="In game")

        self.level_num = level_num

        self.gates: list[LogicalGate] = []
        self.connections = []
        self.default_gate_type = "AND"
        self.dragged_gate = None

        self.selected_input = None
        self.selected_output = None

        self.ui.on_event = self.on_event

        self.anchor = self.add_widget(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))
        self.tools_box = self.anchor.add(arcade.gui.UIBoxLayout(space_between=5), anchor_x="right", anchor_y="bottom", align_x=-5, align_y=20)

        gate_names = list(LOGICAL_GATES.keys())

        if not level_num == -1:
            self.task_label = self.anchor.add(arcade.gui.UILabel(text=generate_task_text(LEVELS[level_num]), font_size=20, multiline=True), anchor_x="center", anchor_y="top")
            for requirement in LEVELS[level_num]:
                if requirement[1] == "INPUT":
                    for _ in range(requirement[0]):
                        self.add_gate(random.randint(0, self.window.width - 300), random.randint(200, self.window.height - 100), "INPUT", requirement[2])
                elif requirement[1] == "OUTPUT":
                    for _ in range(requirement[0]):
                        self.add_gate(random.randint(0, self.window.width - 300), random.randint(200, self.window.height - 100), "OUTPUT")
        else:
            self.task_label = self.anchor.add(arcade.gui.UILabel(text="Task: Have fun! Do whatever you want!", font_size=20), anchor_x="center", anchor_y="top")
            gate_names.extend(["INPUT 0", "INPUT 1", "OUTPUT"])

        for gate in gate_names:
            button = self.tools_box.add(arcade.gui.UIFlatButton(width=self.window.width * 0.1, height=self.window.height * 0.075, text=f"Create {gate} gate", style=dropdown_style))
            button.on_click = lambda event, gate=gate: self.add_gate(random.randint(0, self.window.width - 300), random.randint(200, self.window.height - 100), gate)

        screenshot_button = self.tools_box.add(arcade.gui.UIFlatButton(width=self.window.width * 0.1, height=self.window.height * 0.075, text="Screenshot", style=dropdown_style))
        screenshot_button.on_click = lambda event: self.screenshot()

        hide_button = self.tools_box.add(arcade.gui.UIFlatButton(width=self.window.width * 0.1, height=self.window.height * 0.075, text="Hide", style=dropdown_style))
        hide_button.on_click = lambda event: self.hide_show_panel()

    def screenshot(self):
        self.tools_box.visible = False
        self.tools_box._requires_render = True
        self.on_draw()

        image = arcade.get_image()
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        image.save(f"{timestamp}.png")

        self.tools_box.visible = True

        self.add_widget(arcade.gui.UIMessageBox(
            width=self.window.width / 2,
            height=self.window.height / 2,
            message_text=f"Screenshot was succesfully saved as {timestamp}.png in the current directory!",
            title="Screenshot successful.",
            buttons=("OK",)
        ))

    def hide_show_panel(self):
        new_state = not self.tools_box.children[0].visible
        hide_button = None

        for button in self.tools_box.children:
            if not button.text == "Hide" and not button.text == "Show":
                button.visible = new_state
            else:
                hide_button = button

        if new_state:
            hide_button.text = "Hide"
        else:
            hide_button.text = "Show"

    def evaluate(self):
        for gate in self.gates:
            if not gate.output:
                gate.calculate_value()

    def select_output(self, gate_id):
        if self.gates[gate_id].output:
            return

        self.selected_output = gate_id
        self.selected_input = None

    def select_input(self, gate_id):
        if len(self.gates[gate_id].input) == 2:
            return

        if self.selected_output is not None:
            self.selected_input = gate_id
            
            output_gate = self.gates[self.selected_output]
            input_gate = self.gates[self.selected_input]

            output_gate.output = input_gate
            input_gate.input.append(output_gate)

            self.connections.append([self.selected_output, self.selected_input])
            
            self.selected_output = None 
            self.selected_input = None

            self.evaluate()

    def add_gate(self, x, y, gate_type, value=None):
        if gate_type == "INPUT 0":
            gate_type = "INPUT"
            value = 0
        elif gate_type == "INPUT 1":
            gate_type = "INPUT"
            value = 1

        self.gates.append(self.add_widget(LogicalGate(len(self.gates), x, y, gate_type, value)))
        
        self.gates[-1].input_add_button.on_click = lambda e, gate_id=len(self.gates) - 1: self.select_input(gate_id)
        self.gates[-1].output_add_button.on_click = lambda e, gate_id=len(self.gates) - 1: self.select_output(gate_id)

        self.evaluate()

    def on_event(self, event):
        arcade.gui.UIManager.on_event(self.ui, event)

        if isinstance(event, arcade.gui.UIMousePressEvent):
            if not self.dragged_gate:
                for gate in self.gates:
                    if gate.gate_button.rect.point_in_rect((event.x, event.y)):
                        self.dragged_gate = gate
                        break

    def on_mouse_drag(self, x, y, dx, dy, _buttons, _modifiers):
        if self.dragged_gate is not None:
            self.dragged_gate.rect = self.dragged_gate.rect.move(dx, dy)

    def on_mouse_release(self, x, y, button, modifiers):
        self.dragged_gate = None

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            from menus.main import Main
            self.window.show_view(Main(self.pypresence_client))

    def on_draw(self):
        super().on_draw()

        for conn in self.connections:
            start_id, end_id = conn
            start_gate = self.gates[start_id]
            end_gate = self.gates[end_id]

            p0 = get_gate_port_position(start_gate, "output")
            p3 = get_gate_port_position(end_gate, "input")

            dx = p3[0] - p0[0]
            offset = max(60, abs(dx) * 0.45)
            c1 = (p0[0] + offset, p0[1])
            c2 = (p3[0] - offset, p3[1])

            points = cubic_bezier_points(p0, c1, c2, p3, segments=40)
            arcade.draw_line_strip(points, arcade.color.WHITE, 3)