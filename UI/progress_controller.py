class ProgressController:
    def __init__(self, splash_screen):
        self.splash_screen = splash_screen

    def set_value(self, value: int):
        self.splash_screen.set_progress(value)

    def reset(self):
        self.set_value(0)

    def hide(self):
        self.splash_screen.hide_progress()

    def show(self):
        self.splash_screen.show_progress() 