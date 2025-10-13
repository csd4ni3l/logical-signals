import arcade, arcade.gui

from math import ceil

from utils.constants import button_style, LEVELS
from utils.preload import button_texture, button_hovered_texture

class LevelSelector(arcade.gui.UIView):
    def __init__(self, pypresence_client):
        super().__init__()

        self.pypresence_client = pypresence_client
        self.pypresence_client.update(state="In Menus", details="Level Selector")

        self.anchor = self.add_widget(arcade.gui.UIAnchorLayout(size_hint=(1, 1)))
        self.grid = self.anchor.add(arcade.gui.UIGridLayout(width=self.window.width / 2, height=self.window.height / 2, vertical_spacing=10, horizontal_spacing=10, column_count=5, row_count=ceil(len(LEVELS) / 5)), anchor_x="center", anchor_y="top", align_y=-self.window.height / 8)

    def on_show_view(self):
        super().on_show_view()

        self.back_button = arcade.gui.UITextureButton(texture=button_texture, texture_hovered=button_hovered_texture, text='<--', style=button_style, width=100, height=50)
        self.back_button.on_click = lambda event: self.main_exit()
        self.anchor.add(self.back_button, anchor_x="left", anchor_y="top", align_x=5, align_y=-5)

        self.anchor.add(arcade.gui.UILabel(text="Level Selector", font_size=40), anchor_x="center", anchor_y="top")

        for n in range(len(LEVELS)):
            row, col = n // 5, n % 5
            level_button = self.grid.add(arcade.gui.UITextureButton(width=self.window.width / 8, height=self.window.height / 8, text=f"Level {n + 1}", texture=button_texture, texture_hovered=button_hovered_texture, style=button_style), row=row, column=col)
            level_button.on_click = lambda event, n=n: self.play(n)
        
        self.grid._trigger_size_hint_update()

    def main_exit(self):
        from menus.main import Main
        self.window.show_view(Main(self.pypresence_client))

    def play(self, n):
        from game.play import Game
        self.window.show_view(Game(self.pypresence_client, n))

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.main_exit()
