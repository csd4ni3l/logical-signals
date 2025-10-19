import arcade, arcade.gui, random, datetime, os, json

from datetime import datetime

from utils.utils import cubic_bezier_points, get_gate_port_position, generate_task_text, multi_gate
from utils.constants import button_style, LOGICAL_GATES, LEVELS, SINGLE_INPUT_LOGICAL_GATES
from utils.preload import button_texture, button_hovered_texture, logic_gate_textures

class LogicalGate(arcade.Sprite):
    def __init__(self, id, x, y, gate_type):
        super().__init__(center_x=x, center_y=y, img=logic_gate_textures[gate_type][0])

        self.id = id
        self.gate_type = gate_type
        self.value = None
        
        self.input: list[LogicalGate] = []
        self.output: LogicalGate | None = None

    def calculate_value(self):
        if self.gate_type == "OUTPUT" and self.input:
            self.value = self.input[0].calculate_value()

        elif self.gate_type == "INPUT": # dont set INPUT to None
            pass
        elif self.gate_type in SINGLE_INPUT_LOGICAL_GATES and len(self.input) == 1:
            if self.input[0].value is not None:
                self.value = int(LOGICAL_GATES[self.gate_type](self.input[0].calculate_value()))
            else:
                self.value = None
        elif len(self.input) > 1:
            if len(self.input) == 2:
                value = LOGICAL_GATES[self.gate_type](self.input[0].calculate_value(), self.input[1].calculate_value())
                self.value = int(value) if value is not None else value # have to convert to int cause it might return boolean
            else:
                self.value = multi_gate([input.calculate_value() for input in self.input], LOGICAL_GATES[self.gate_type])
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

        self.gates: list[LogicalGate | arcade.gui.UIInputText] = []
        self.connections = []
        self.bezier_points = []

        self.default_gate_type = "AND"
        self.dragged_gate = None

        self.selected_input = None
        self.selected_output = None

        self.anchor = self.add_widget(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))
        self.tools_box = self.anchor.add(arcade.gui.UIBoxLayout(space_between=5), anchor_x="right", anchor_y="center", align_x=-10)

        if not level_num == -1:
            self.task_label = self.anchor.add(arcade.gui.UILabel(text=generate_task_text(LEVELS[level_num]), font_size=20, multiline=True), anchor_x="center", anchor_y="top", align_y=-15)
            for requirement in LEVELS[level_num]:
                if requirement[1] == "INPUT":
                    for _ in range(requirement[0]):
                        self.add_gate(random.randint(50, 200), random.randint(200, self.window.height - 100), "INPUT")
                elif requirement[1] == "OUTPUT":
                    for _ in range(requirement[0]):
                        self.add_gate(random.randint(self.window.width - 500, self.window.width - 350), random.randint(200, self.window.height - 100), "OUTPUT")
                else:
                    for _ in range(requirement[0]):
                        self.add_gate(random.randint(300, self.window.width - 600), random.randint(200, self.window.height - 100), requirement[1])
        else:
            self.task_label = self.anchor.add(arcade.gui.UILabel(text="Task: Have fun! Do whatever you want!", font_size=20), anchor_x="center", anchor_y="top", align_y=-15)

            for gate in list(LOGICAL_GATES.keys()) + ["INPUT", "OUTPUT", "LABEL"]:
                button = self.tools_box.add(arcade.gui.UITextureButton(width=self.window.width * 0.125, height=self.window.height * 0.05, text=f"Create {gate} gate", style=button_style, texture=button_texture, texture_hovered=button_hovered_texture))
                
                if "INPUT" in gate:
                    func = lambda: (random.randint(50, 200), random.randint(200, self.window.height - 100))
                elif gate == "OUTPUT":
                    func = lambda: (random.randint(self.window.width - 500, self.window.width - 350), random.randint(200, self.window.height - 100))
                else:
                    func = lambda: (random.randint(300, self.window.width - 600), random.randint(200, self.window.height - 100))
                
                button.on_click = lambda event, func=func, gate=gate: self.add_gate(*func(), gate)

        screenshot_button = self.tools_box.add(arcade.gui.UITextureButton(width=self.window.width * 0.125, height=self.window.height * 0.05, text="Screenshot", style=button_style, texture=button_texture, texture_hovered=button_hovered_texture))
        screenshot_button.on_click = lambda event: self.screenshot()

        if level_num == -1:
            load_button = self.tools_box.add(arcade.gui.UITextureButton(width=self.window.width * 0.125, height=self.window.height * 0.05, text="Load", style=button_style, texture=button_texture, texture_hovered=button_hovered_texture))
            load_button.on_click = lambda event: self.show_load_ui()

        save_button = self.tools_box.add(arcade.gui.UITextureButton(width=self.window.width * 0.125, height=self.window.height * 0.05, text="Save", style=button_style, texture=button_texture, texture_hovered=button_hovered_texture))
        save_button.on_click = lambda event: self.save()

        hide_button = self.tools_box.add(arcade.gui.UITextureButton(width=self.window.width * 0.125, height=self.window.height * 0.05, text="Hide", style=button_style, texture=button_texture, texture_hovered=button_hovered_texture))
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

        self.ui.on_event = self.on_event

    def save(self):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

        data = []

        for gate in self.gates:
            if gate.gate_type != "LABEL":
                data.append([gate.id, gate.center_x, gate.center_y, gate.gate_type, gate.value, [input_gate.id for input_gate in gate.input], gate.output.id if gate.output else None])
            else:
                data.append([gate.id, gate.center_x, gate.center_y, gate.gate_type, gate.text])

        with open(f"saves/{timestamp}-save.json", "w") as file:
            file.write(json.dumps(data, indent=4))

        self.add_widget(arcade.gui.UIMessageBox(
            width=self.window.width / 2,
            height=self.window.height / 2,
            message_text=f"Level was succesfully saved as {timestamp}-save.json in the current directory!",
            title="Save successful.",
            buttons=("OK",)
        ))

    def close_load_ui(self):
        self.anchor.remove(self.load_ui_box)
        del self.load_ui_box

        self.ui._requires_render = True # for some reason, it doesn't automatically mark it as render required?

    def show_load_ui(self):
        self.load_ui_box = self.anchor.add(arcade.gui.UIBoxLayout(size_hint=(0.75, 0.75), space_between=5).with_background(color=arcade.color.DARK_GRAY), anchor_x="center", anchor_y="center", align_x=-self.window.width / 12)
        
        self.load_ui_box.add(arcade.gui.UILabel(text="Pick save to load", font_size=28, text_color=arcade.color.BLACK))

        for save_filename in os.listdir("saves"):
            button = self.load_ui_box.add(arcade.gui.UITextureButton(text=save_filename, style=button_style, texture=button_texture, texture_hovered=button_hovered_texture, width=self.window.width / 2, height=self.window.height / 20))
            button.on_click = lambda event, save_filename=save_filename: self.load(save_filename)

        close_button = self.load_ui_box.add(arcade.gui.UITextureButton(text="Close", style=button_style, texture=button_texture, texture_hovered=button_hovered_texture, width=self.window.width / 2, height=self.window.height / 20))
        close_button.on_click = lambda event: self.close_load_ui()

    def load(self, save_filename):
        self.gates.clear()

        [self.ui.remove(gate) for gate in self.gates if gate.gate_type == "LABEL"]

        self.spritelist.clear()
        self.connections.clear()

        with open(f"saves/{save_filename}", "r") as file:
            data = json.load(file)

        for gate in data:
            if gate[3] != "LABEL":
                sprite = LogicalGate(gate[0], gate[1], gate[2], gate[3])
                sprite.value = gate[4]
                sprite.input = gate[5]
                sprite.output = gate[6]

                self.gates.append(sprite)
                self.spritelist.append(sprite)
            else:
                label = self.add_widget(arcade.gui.UIInputText(text=gate[4], x=gate[1], y=gate[2], font_name="Roboto", width=self.window.width / 10, height=self.window.height / 30))
                self.gates.append(label)
                label.id = gate[0]
                label.gate_type = "LABEL"

        for gate_cls in self.gates:
            if gate_cls.gate_type != "LABEL":
                gate_cls.input = [self.gates[input_id] for input_id in gate_cls.input]
                gate_cls.output = self.gates[gate_cls.output] if gate_cls.output else None

        for gate_x in self.gates:
            if gate_x.gate_type == "LABEL":
                continue

            for gate_y in self.gates:
                if gate_x == gate_y or gate_y.gate_type == "LABEL":
                    continue
            
                if gate_x in gate_y.input:
                    self.connections.append([gate_x.id, gate_y.id])

        self.evaluate()

        self.close_load_ui()

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
            if gate.gate_type == "LABEL":
                continue

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
        
        if self.level_num != -1:
            if self.gates[gate_id].gate_type not in SINGLE_INPUT_LOGICAL_GATES and len(self.gates[gate_id].input) == 2:
                return
            
        if self.gates[gate_id].gate_type in SINGLE_INPUT_LOGICAL_GATES and len(self.gates[gate_id].input) == 1:
            return

        self.selected_input = gate_id

        if self.selected_output is not None:
            self.add_connection()

    def add_gate(self, x, y, gate_type):
        if gate_type != "LABEL":
            sprite = LogicalGate(len(self.gates), x, y, gate_type)
            self.gates.append(sprite)
            self.spritelist.append(sprite)
        else:
            label = self.add_widget(arcade.gui.UIInputText(text="Placeholder", x=x, y=y, font_name="Roboto", font_size=14, width=self.window.width / 10, height=self.window.height / 30))
            self.gates.append(label)
            label.id = len(self.gates)
            label.gate_type = "LABEL"

        self.evaluate()

    def connection_between(self, p0, p3):
        dx = p3[0] - p0[0]
        offset = max(60, abs(dx) * 0.45)
        c1 = (p0[0] + offset, p0[1])
        c2 = (p3[0] - offset, p3[1])

        return cubic_bezier_points(p0, c1, c2, p3, segments=100)
            
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.camera.zoom += scroll_y * 0.1

        gate: arcade.gui.UIInputText
        for gate in self.gates:
            if scroll_y == 1:
                gate.scale(1.1)
            else:
                gate.scale(1 / 1.1)

            if gate.width < self.window.width / 18:
                gate.doc.set_style(
                    0,
                    len(gate.text),
                    dict(font_name="Roboto", font_size=7, color=gate._text_color),
                )
            elif gate.width < self.window.width / 16:
                gate.doc.set_style(
                    0,
                    len(gate.text),
                    dict(font_name="Roboto", font_size=9, color=gate._text_color),
                )
            elif gate.width < self.window.width / 14:
                  gate.doc.set_style(
                    0,
                    len(gate.text),
                    dict(font_name="Roboto", font_size=11, color=gate._text_color),
                )              
            
            elif gate.width < self.window.width / 12:
                  gate.doc.set_style(
                    0,
                    len(gate.text),
                    dict(font_name="Roboto", font_size=13, color=gate._text_color),
                )            
            elif gate.width < self.window.width / 10:
                  gate.doc.set_style(
                    0,
                    len(gate.text),
                    dict(font_name="Roboto", font_size=15, color=gate._text_color),
                )            
            elif gate.width < self.window.width / 8:
                  gate.doc.set_style(
                    0,
                    len(gate.text),
                    dict(font_name="Roboto", font_size=17, color=gate._text_color),
                )              
            elif gate.width < self.window.width / 6:
                  gate.doc.set_style(
                    0,
                    len(gate.text),
                    dict(font_name="Roboto", font_size=19, color=gate._text_color),
                )              

    def on_event(self, event):
        arcade.gui.UIManager.on_event(self.ui, event)

        if isinstance(event, arcade.gui.UIOnClickEvent):
            unprojected_vec = self.camera.unproject((event.x, event.y))
            world_vec = arcade.math.Vec2(unprojected_vec.x, unprojected_vec.y)

            for gate in self.gates:
                if gate.rect.point_in_rect(world_vec):
                    self.dragged_gate = gate

    def on_mouse_press(self, x, y, button, modifiers):
        unprojected_vec = self.camera.unproject((x, y))
        world_vec = arcade.math.Vec2(unprojected_vec.x, unprojected_vec.y)

        if button == arcade.MOUSE_BUTTON_RIGHT:
            for i in range(len(self.bezier_points) - 1, -1, -1):
                for point in self.bezier_points[i]:
                    if world_vec.distance(point) < 5:
                        self.gates[self.connections[i][0]].output = None
                        self.gates[self.connections[i][1]].input.remove(self.gates[self.connections[i][0]])
                        self.gates[self.connections[i][1]].calculate_value()

                        self.connections.pop(i)
                        self.bezier_points.pop(i)
                        break

        elif button == arcade.MOUSE_BUTTON_LEFT:
            for gate in self.gates:
                if gate.rect.point_in_rect((world_vec.x, world_vec.y)):
                    width_x = gate.center_x - world_vec.x
                    if abs(width_x) < (58 if gate.gate_type not in ["INPUT", "OUTPUT"] else 43): # INPUT and OUTPUT buttons are smaller, so they have to be adjusted to 43
                        self.dragged_gate = gate
                        if gate.gate_type == "INPUT":
                            gate.value = not gate.value
                            self.evaluate()
                        break
                    else:
                        if width_x > 0:
                            if not gate.gate_type == "INPUT":
                                self.select_input(gate.id)
                        elif not gate.gate_type == "OUTPUT":
                            self.select_output(gate.id)

    def on_mouse_drag(self, x, y, dx, dy, button, _modifiers):
        if button == arcade.MOUSE_BUTTON_MIDDLE:
            self.camera.position = self.camera.position - arcade.math.Vec2(dx / self.camera.zoom, dy / self.camera.zoom)

        elif self.dragged_gate is not None:
            if not isinstance(self.dragged_gate, arcade.gui.UIInputText):
                self.dragged_gate.center_x += dx / self.camera.zoom
                self.dragged_gate.center_y += dy / self.camera.zoom
            else:
                self.dragged_gate.rect = self.dragged_gate.rect.move(dx / self.camera.zoom, dy / self.camera.zoom)
            
    def on_mouse_release(self, x, y, button, modifiers):
        self.dragged_gate = None

    def main_exit(self):
        from menus.main import Main
        self.window.show_view(Main(self.pypresence_client))

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.main_exit()

    def on_draw(self):
        self.window.clear()

        with self.camera.activate():
            self.spritelist.draw()

            self.bezier_points = []

            for conn in self.connections:
                start_id, end_id = conn
                start_gate = self.gates[start_id]
                end_gate = self.gates[end_id]

                points = self.connection_between(get_gate_port_position(start_gate, "output"), get_gate_port_position(end_gate, "input"))
                self.bezier_points.append(points)

                arcade.draw_line_strip(points, arcade.color.WHITE, 6)

            mouse_x, mouse_y = self.window.mouse.data.get("x", 0), self.window.mouse.data.get("y", 0)

            if self.selected_input is not None and self.selected_output is None:
                points = self.connection_between(get_gate_port_position(self.gates[self.selected_input], "input"), (mouse_x, mouse_y))
                arcade.draw_line_strip(points, arcade.color.WHITE, 6)

            if self.selected_output is not None and self.selected_input is None:
                points = self.connection_between(get_gate_port_position(self.gates[self.selected_output], "output"), (mouse_x, mouse_y))
                arcade.draw_line_strip(points, arcade.color.WHITE, 6)
        
        self.ui.draw()
