import arcade.gui, arcade

from utils.constants import LOGICAL_GATES

from PIL import ImageDraw, ImageFont

button_texture = arcade.gui.NinePatchTexture(64 // 4, 64 // 4, 64 // 4, 64 // 4, arcade.load_texture("assets/graphics/button.png"))
button_hovered_texture = arcade.gui.NinePatchTexture(64 // 4, 64 // 4, 64 // 4, 64 // 4, arcade.load_texture("assets/graphics/button_hovered.png"))

true_logic_gate = arcade.load_image("assets/graphics/logic_gate_true.png")
false_logic_gate = arcade.load_image("assets/graphics/logic_gate_false.png")

true_input_logic_gate = arcade.load_image("assets/graphics/logic_gate_input_true.png")
false_input_logic_gate = arcade.load_image("assets/graphics/logic_gate_input_false.png")

true_output_logic_gate = arcade.load_image("assets/graphics/logic_gate_output_true.png")
false_output_logic_gate = arcade.load_image("assets/graphics/logic_gate_output_false.png")

logic_gate_textures = {}

font = ImageFont.truetype("assets/fonts/Roboto-Black.ttf", 14)

for gate_name in list(LOGICAL_GATES.keys()) + ["INPUT", "OUTPUT"]:
    logic_gate_textures[gate_name] = []

    for i in range(2):
        if not i:
            if gate_name == "INPUT":
                img = false_input_logic_gate.copy()
            elif gate_name == "OUTPUT":
                img = false_output_logic_gate.copy()
            else:
                img = false_logic_gate.copy()
        else:
            if gate_name == "INPUT":
                img = true_input_logic_gate.copy()
            elif gate_name == "OUTPUT":
                img = true_output_logic_gate.copy()
            else:
                img = true_logic_gate.copy()

        draw = ImageDraw.Draw(img)

        bbox = draw.textbbox((0, 0), gate_name, font=font)
        text_w = (bbox[2] - bbox[0]) * 1.25
        text_h = (bbox[3] - bbox[1]) * 1.25

        width, height = img.size
        text_x = (width - text_w) // 2
        text_y = (height - text_h) // 2

        draw.text((text_x, text_y), gate_name, font=font, fill=(0, 0, 0, 255))

        logic_gate_textures[gate_name].append(arcade.Texture(name=gate_name, image=img))