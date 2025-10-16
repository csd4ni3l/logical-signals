import arcade, arcade.gui, random, datetime, os, json

from datetime import datetime

from utils.utils import cubic_bezier_points, get_gate_port_position, generate_task_text
from utils.constants import button_style, dropdown_style, LOGICAL_GATES, LEVELS, SINGLE_INPUT_LOGICAL_GATES
from utils.preload import button_texture, button_hovered_texture, logic_gate_textures

class LogicalGate(arcade.Sprite):
    def __init__(self, id, x, y, gate_type, value):
        super().__init__(center_x=x, center_y=y, img=logic_gate_textures[gate_type][value if value is not None else 0])

        self.id = id
        self.gate_type = gate_type

        if gate_type == "INPUT":
            self.value = value
        else:
            self.value = 0
        
        self.input: list[LogicalGate] = []
        self.output: LogicalGate | None = None

    def calculate_value(self):
        if self.gate_type == "OUTPUT" and self.input:
            self.value = self.input[0].calculate_value()

        elif self.gate_type == "INPUT": # dont set INPUT to None
            pass
        elif self.gate_type in SINGLE_INPUT_LOGICAL_GATES and len(self.input) == 1:
            self.value = int(LOGICAL_GATES[self.gate_type](self.input[0].calculate_value()))
        elif len(self.input) == 2:
            self.value = int(LOGICAL_GATES[self.gate_type](self.input[0].calculate_value(), self.input[1].calculate_value())) # have to convert to int cause it might return boolean
        else:
            self.value = None

        self.texture = logic_gate_textures[self.gate_type][self.value if self.value is not None else 0]
        return self.value
        
    def __repr__(self):
        return f"{self.gate_type}: {self.value}"

class Game(arcade.gui.UIView):
    def __init__(self, pypresence_client, level_num):
        super().__init__()

        self.camera = arcade.Camera2D()
        self.camera.match_window()

        self.spritelist = arcade.SpriteList()

        self.pypresence_client = pypresence_client
        self.pypresence_client.update(state="In game")

        self.level_num = level_num

        self.gates: list[LogicalGate] = []
        self.connections = []
        self.bezier_points = []

        self.default_gate_type = "AND"
        self.dragged_gate = None

        self.selected_input = None
        self.selected_output = None

        self.ui.on_event = self.on_event

        self.anchor = self.add_widget(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))
        self.tools_box = self.anchor.add(arcade.gui.UIBoxLayout(space_between=5), anchor_x="right", anchor_y="bottom", align_x=-5, align_y=20)

        if not level_num == -1:
            self.task_label = self.anchor.add(arcade.gui.UILabel(text=generate_task_text(LEVELS[level_num]), font_size=20, multiline=True), anchor_x="center", anchor_y="top", align_y=-15)
            for requirement in LEVELS[level_num]:
                if requirement[1] == "INPUT":
                    for _ in range(requirement[0]):
                        self.add_gate(random.randint(0, 200), random.randint(200, self.window.height - 100), "INPUT", requirement[2])
                elif requirement[1] == "OUTPUT":
                    for _ in range(requirement[0]):
                        self.add_gate(random.randint(self.window.width - 500, self.window.width - 350), random.randint(200, self.window.height - 100), "OUTPUT", requirement[2])
                else:
                    for _ in range(requirement[0]):
                        self.add_gate(random.randint(300, self.window.width - 600), random.randint(200, self.window.height - 100), requirement[1])
        else:
            self.task_label = self.anchor.add(arcade.gui.UILabel(text="Task: Have fun! Do whatever you want!", font_size=20), anchor_x="center", anchor_y="top", align_y=-15)

            for gate in list(LOGICAL_GATES.keys()) + ["INPUT 0", "INPUT 1", "OUTPUT"]:
                button = self.tools_box.add(arcade.gui.UIFlatButton(width=self.window.width * 0.1, height=self.window.height * 0.075, text=f"Create {gate} gate", style=dropdown_style))
                
                if "INPUT" in gate:
                    func = lambda: (random.randint(0, 200), random.randint(200, self.window.height - 100))
                elif gate == "OUTPUT":
                    func = lambda: (random.randint(self.window.width - 500, self.window.width - 350), random.randint(200, self.window.height - 100))
                else:
                    func = lambda: (random.randint(300, self.window.width - 600), random.randint(200, self.window.height - 100))
                
                button.on_click = lambda event, func=func, gate=gate: self.add_gate(*func(), gate)

        screenshot_button = self.tools_box.add(arcade.gui.UIFlatButton(width=self.window.width * 0.1, height=self.window.height * 0.075, text="Screenshot", style=dropdown_style))
        screenshot_button.on_click = lambda event: self.screenshot()

        hide_button = self.tools_box.add(arcade.gui.UIFlatButton(width=self.window.width * 0.1, height=self.window.height * 0.075, text="Hide", style=dropdown_style))
        hide_button.on_click = lambda event: self.hide_show_panel()

        self.back_button = arcade.gui.UITextureButton(texture=button_texture, texture_hovered=button_hovered_texture, text='<--', style=button_style, width=100, height=50)
        self.back_button.on_click = lambda event: self.main_exit()
        self.anchor.add(self.back_button, anchor_x="left", anchor_y="top", align_x=5, align_y=-5)

        if os.path.exists("data.json"):
            with open("data.json", "r") as file:
                self.data = json.load(file)
        else:
            self.data = {}

        if not "completed_levels" in self.data:
            self.data["completed_levels"] = []

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
        process_nodes = []
        outputs = []

        for gate in self.gates:
            if not gate.output:
                gate.calculate_value()

            if gate.gate_type == "OUTPUT" and gate.input:
                outputs.append(gate.value)

            if not gate.gate_type in ["INPUT", "OUTPUT"] and gate.input and gate.output:
                process_nodes.append(gate.gate_type)

        for requirement in LEVELS[self.level_num]:
            if requirement[1] == "INPUT":
                continue

            if requirement[1] == "OUTPUT":
                for _ in range(requirement[0]):
                    if not requirement[2] in outputs:
                        return
                    else:
                        outputs.remove(requirement[2])
            else:
                for _ in range(requirement[0]):
                    if not requirement[1] in process_nodes:
                        return
                    else:
                        process_nodes.remove(requirement[1])

        if not self.level_num in self.data["completed_levels"]:
            self.data["completed_levels"].append(self.level_num)
            
        self.task_label.text = f"You Successfully Completed Level {self.level_num + 1}!"

        with open("data.json", "w") as file:
            file.write(json.dumps(self.data, indent=4))
                    
    def add_connection(self):
        output_gate = self.gates[self.selected_output]
        input_gate = self.gates[self.selected_input]

        output_gate.output = input_gate
        input_gate.input.append(output_gate)

        self.connections.append([self.selected_output, self.selected_input])
        
        self.selected_output = None 
        self.selected_input = None

        self.evaluate()

    def select_output(self, gate_id):
        if gate_id == self.selected_input:
            return

        if self.gates[gate_id].output:
            return
        
        self.selected_output = gate_id

        if self.selected_input is not None:
            self.add_connection()

    def select_input(self, gate_id):
        if gate_id == self.selected_output:
            return
        
        if self.gates[gate_id].gate_type not in SINGLE_INPUT_LOGICAL_GATES and len(self.gates[gate_id].input) == 2:
            return
        elif self.gates[gate_id].gate_type in SINGLE_INPUT_LOGICAL_GATES and len(self.gates[gate_id].input) == 1:
            return

        self.selected_input = gate_id

        if self.selected_output is not None:
            self.add_connection()

    def add_gate(self, x, y, gate_type, value=None):
        if gate_type == "INPUT 0":
            gate_type = "INPUT"
            value = 0
        elif gate_type == "INPUT 1":
            gate_type = "INPUT"
            value = 1

        sprite = LogicalGate(len(self.gates), x, y, gate_type, value)
        self.gates.append(sprite)
        self.spritelist.append(sprite)

        self.evaluate()

    def on_event(self, event):
        arcade.gui.UIManager.on_event(self.ui, event)

        if isinstance(event, arcade.gui.UIMousePressEvent):
            if event.button == arcade.MOUSE_BUTTON_RIGHT:
                for i in range(len(self.bezier_points) - 1, -1, -1):
                    for point in self.bezier_points[i]:
                        if event.pos.distance(point) < 5:
                            self.gates[self.connections[i][0]].output = None
                            self.gates[self.connections[i][1]].input.remove(self.gates[self.connections[i][0]])
                            self.gates[self.connections[i][1]].calculate_value()

                            self.connections.pop(i)
                            self.bezier_points.pop(i)
                            break

            elif event.button == arcade.MOUSE_BUTTON_LEFT:
                for gate in self.gates:
                    if gate.rect.point_in_rect((event.x, event.y)):
                        x = gate.center_x - event.x
                        if abs(x) < 58:
                            self.dragged_gate = gate
                            break
                        else:
                            if x > 0:
                                self.select_input(gate.id)
                            else:
                                self.select_output(gate.id)

    def on_mouse_drag(self, x, y, dx, dy, _buttons, _modifiers):
        if self.dragged_gate is not None:
            self.dragged_gate.center_x += dx
            self.dragged_gate.center_y += dy

    def on_mouse_release(self, x, y, button, modifiers):
        self.dragged_gate = None

    def main_exit(self):
        from menus.main import Main
        self.window.show_view(Main(self.pypresence_client))

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.main_exit()
            
    def on_draw(self):
        super().on_draw()

        self.camera.use()
        self.spritelist.draw()

        self.bezier_points = []

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

            points = cubic_bezier_points(p0, c1, c2, p3, segments=100)
            self.bezier_points.append(points)

            arcade.draw_line_strip(points, arcade.color.WHITE, 6)