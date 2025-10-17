import arcade, arcade.gui

from utils.constants import button_style
from utils.preload import button_texture, button_hovered_texture

class Tutorial(arcade.gui.UIView):
    def __init__(self, pypresence_client):
        super().__init__()

        self.pypresence_client = pypresence_client

        self.anchor = self.add_widget(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))

        self.title_label = self.anchor.add(arcade.gui.UILabel(text="Tutorial", font_size=40), anchor_x="center", anchor_y="top")

        self.instructions_label = self.anchor.add(arcade.gui.UILabel(text="""How to play:
- You can move gates by dragging their buttons (not the plus ones)
- To create connections, click on the + buttons, left is the input, right is the output
- On levels, a node has to have 2 inputs(Except the OUTPUT and NOT node), but only 1 output
- On DIY mode, a node can have more than 2 inputs, except for OUTPUT and NOT
- You have to connect the nodes in a way to meet the required result
                                                     
Logical Gates explanation:
- AND: Returns 1 if all inputs are 1, otherwise 0
- OR: Returns 1 if any inputs are 1, otherwise 0
- NAND: Returns 1 if any inputs are 0, otherwise 0
- NOR: Returns 1 if all inputs are 0, otherwise 0
- XOR: Returns 1 if atleast 1 input is different, otherwise 0
- XNOR: Returns 1 if all inputs are the same, otherwise 0
""", multiline=True, font_size=22), anchor_x="center", anchor_y="center")

        self.back_button = arcade.gui.UITextureButton(texture=button_texture, texture_hovered=button_hovered_texture, text='<--', style=button_style, width=100, height=50)
        self.back_button.on_click = lambda event: self.main_exit()
        self.anchor.add(self.back_button, anchor_x="left", anchor_y="top", align_x=5, align_y=-5)

    def main_exit(self):
        from menus.main import Main
        self.window.show_view(Main(self.pypresence_client))

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.main_exit()