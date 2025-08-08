from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.metrics import dp
import os


class Notification(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(300), dp(50))
        self.pos_hint = {'center_x': 0.5, 'top': 0.95}
        self.color = get_color_from_hex('#ffffff')
        self.background_color = get_color_from_hex('#ff3333')
        self.opacity = 0
        self.font_size = dp(20)
        self.bold = True
        self.markup = True


class ShopItem(BoxLayout):
    def __init__(self, image_source, price_text, price, app_instance, skin_index, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (dp(300), dp(400))
        self.spacing = dp(10)
        self.padding = dp(10)
        self.app = app_instance
        self.price = price
        self.skin_index = skin_index
        self.purchased = False
        self.image_source = image_source

        if os.path.exists('xui.txt'):
            with open('xui.txt', 'r') as f:
                data = f.read().strip().split(',')
                if len(data) > 6:
                    purchased_skins = data[6].split('|')
                    self.purchased = str(skin_index) in purchased_skins or price == 0

        self.skin_colors = [
            '#f5a742',  # стандартний (0)
            '#ffffff',  # зелений (1)
            '#ffffff',  # блакитний (2)
            '#ffffff'  # рожевий (3)
        ]

        self.image = Image(
            source=image_source,
            size_hint=(1, 0.7),
            allow_stretch=True,
            keep_ratio=False
        )

        if skin_index == 0:
            price_display = "БЕЗЦІННО!"
            self.purchased = True
        else:
            price_display = "БЕЗКОШТОВНО!" if price == 0 else f"{price:,} монет"

        self.price_label = Label(
            text=price_display,
            size_hint=(1, 0.1),
            font_size=dp(20),
            bold=True
        )

        if skin_index == 0:
            btn_text = "Не можна отримати"
            btn_disabled = True
            btn_color = '#cccccc'
        else:
            btn_text = "Отримати" if price == 0 else ("Куплено" if self.purchased else "Купити")
            btn_disabled = self.purchased or (price == 0 and self.purchased)
            btn_color = '#42a1f5' if price == 0 else ('#cccccc' if self.purchased else '#42f554')

        self.buy_button = Button(
            text=btn_text,
            size_hint=(1, 0.1),
            background_color=get_color_from_hex(btn_color),
            background_normal='',
            disabled=btn_disabled,
            on_press=self.buy_item
        )

        select_disabled = not self.purchased or skin_index == 0
        self.select_button = ToggleButton(
            text="Обрано" if self.app.current_skin == skin_index else "Обрати",
            size_hint=(1, 0.1),
            background_color=get_color_from_hex('#42a1f5'),
            background_normal='',
            state='down' if self.app.current_skin == skin_index else 'normal',
            group='skins',
            disabled=select_disabled,
            on_press=self.select_skin
        )

        self.add_widget(self.image)
        self.add_widget(self.price_label)
        self.add_widget(self.buy_button)
        self.add_widget(self.select_button)

    def buy_item(self, instance):
        if self.price == 0 or self.app.coins >= self.price:
            if self.price > 0:
                self.app.coins -= self.price

            self.purchased = True
            self.buy_button.disabled = True
            self.buy_button.text = "Куплено" if self.price > 0 else "Отримано"
            self.buy_button.background_color = get_color_from_hex('#cccccc')
            self.select_button.disabled = False

            if str(self.skin_index) not in self.app.purchased_skins:
                self.app.purchased_skins.append(str(self.skin_index))

            self.select_button.state = 'down'
            self.select_skin(self.select_button)

            self.app.update_balance()
            self.app.save_progress()
        else:
            self.app.show_notification("[b]Недостатньо коштів![/b]")

    def select_skin(self, instance):
        if instance.state == 'down':
            self.app.current_skin = self.skin_index
            if self.skin_index == 0:  # Без скіна
                self.app.click_button.text = "[size=30][b]КЛІКАЙ![/b][/size]"
                self.app.click_button.background_normal = ''
                self.app.click_button.background_down = ''
                self.app.click_button.background_color = get_color_from_hex('#ffffff')
            else:  # Зі скіном
                self.app.click_button.text = ""
                self.app.click_button.background_normal = self.image_source
                self.app.click_button.background_down = self.image_source
                self.app.click_button.background_color = get_color_from_hex('#ffffff')

            for child in self.parent.children:
                if hasattr(child, 'select_button'):
                    child.select_button.text = "Обрати"
            instance.text = "Обрано"

            self.app.save_progress()


class ShopScrollView(ScrollView):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.do_scroll_x = True
        self.do_scroll_y = False
        self.bar_width = dp(10)

        self.items_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            spacing=dp(20),
            padding=dp(20)
        )
        self.items_layout.bind(minimum_width=self.items_layout.setter('width'))

        self.add_widget(self.items_layout)
        self.app = app_instance

    def add_item(self, image_source, price_text, price, skin_index):
        item = ShopItem(image_source, price_text, price, self.app, skin_index)
        self.items_layout.add_widget(item)


class ClickerApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        Window.bind(on_resize=self.on_window_resize)

        self.music_on = True
        self.sound_on = True
        self.current_skin = 0  # 0 - без скіна
        self.purchased_skins = ['0']  # 0 завжди доступний
        self.load_progress()

        self.click_sound = SoundLoader.load('click.mp3')
        self.bg_music = SoundLoader.load('background.mp3')
        self.music_volume = 0.5
        self.sound_volume = 1.0

        self.main_layout = FloatLayout()

        self.notification = Notification()
        self.main_layout.add_widget(self.notification)

        self.splash = Image(
            source='splash.png',
            size_hint=(None, None),
            size=(dp(300), dp(300)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0
        )
        self.main_layout.add_widget(self.splash)
        self.start_splash_animation()

        return self.main_layout

    def show_notification(self, text):
        self.notification.text = text
        anim = Animation(opacity=1, duration=0.3) + Animation(opacity=1, duration=1.5) + Animation(opacity=0,
                                                                                                   duration=0.5)
        anim.start(self.notification)

    def on_window_resize(self, window, width, height):
        if hasattr(self, 'click_button'):
            self.update_ui_layout()

    def load_progress(self):
        try:
            if os.path.exists('xui.txt'):
                with open('xui.txt', 'r') as f:
                    data = f.read().strip().split(',')
                    self.coins = int(data[0]) if len(data) > 0 else 0
                    self.multiplier = int(data[1]) if len(data) > 1 else 1
                    self.upgrade_level = int(data[2]) if len(data) > 2 else 0
                    self.music_volume = float(data[3]) if len(data) > 3 else 0.5
                    self.sound_volume = float(data[4]) if len(data) > 4 else 1.0
                    self.current_skin = int(data[5]) if len(data) > 5 else 0  # 0 - без скіна
                    self.purchased_skins = data[6].split('|') if len(data) > 6 else ['0']  # 0 завжди доступний
        except Exception as e:
            print(f"Помилка завантаження прогресу: {e}")
            self.coins = 0
            self.multiplier = 1
            self.upgrade_level = 0
            self.music_volume = 0.5
            self.sound_volume = 1.0
            self.current_skin = 0  # Без скіна при першому запуску
            self.purchased_skins = ['0']  # 0 завжди доступний

    def save_progress(self):
        data = [
            str(self.coins),
            str(self.multiplier),
            str(self.upgrade_level),
            str(self.music_volume),
            str(self.sound_volume),
            str(self.current_skin),
            "|".join(self.purchased_skins)
        ]
        with open('xui.txt', 'w') as f:
            f.write(",".join(data))

    def start_splash_animation(self):
        anim_in = Animation(opacity=1, duration=1.5)
        anim_out = Animation(opacity=0, duration=1.5)
        anim_in.bind(on_complete=lambda *x: Clock.schedule_once(lambda dt: anim_out.start(self.splash), 2))
        anim_out.bind(on_complete=self.init_game)
        anim_in.start(self.splash)

    def init_game(self, *args):
        self.showing_splash = False
        Window.clearcolor = get_color_from_hex('#2d2d2d')
        self.main_layout.remove_widget(self.splash)

        if self.bg_music:
            self.bg_music.loop = True
            self.bg_music.volume = self.music_volume
            if self.music_on:
                self.bg_music.play()

        self.create_game_ui()

    def create_game_ui(self):
        skin_colors = [
            '#f5a742',  # колір за замовчуванням (без скіна)
            '#ffffff',  # зелений (1)
            '#ffffff',  # блакитний (2)
            '#ffffff'  # рожевий (3)
        ]

        skin_images = [
            None,  # без скіна (0) - тут None
            'item1.png',  # зелений (1)
            'item2.png',  # блакитний (2)
            'item3.png'  # рожевий (3)
        ]

        # Якщо current_skin = 0 (без скіна), то не використовуємо фото
        current_skin_image = skin_images[self.current_skin] if self.current_skin > 0 else None

        self.click_button = Button(
            text="[size=30][b]КЛІКАЙ![/b][/size]" if self.current_skin == 0 else "",
            markup=True,
            size_hint=(None, None),
            size=(dp(250), dp(250)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=get_color_from_hex(skin_colors[0]),  # Колір за замовчуванням
            background_normal=current_skin_image if self.current_skin > 0 else '',
            background_down=current_skin_image if self.current_skin > 0 else '',
            color=get_color_from_hex('#000000'),
            bold=True,
            on_press=self.add_coin
        )
        self.main_layout.add_widget(self.click_button)

        self.balance_label = Label(
            text=f"[size=30][b]Монети:[/b] {self.coins}[/size]",
            markup=True,
            color=get_color_from_hex('#ffffff'),
            size_hint=(None, None),
            size=(dp(300), dp(50)),
            pos=(dp(10), Window.height - dp(60)),
            halign='left',
            valign='top'
        )
        self.main_layout.add_widget(self.balance_label)

        self.multiplier_label = Label(
            text="x2!" if self.upgrade_level >= 1 else "x3!" if self.upgrade_level >= 2 else "",
            markup=True,
            color=get_color_from_hex('#42f554' if self.upgrade_level == 1 else '#42a1f5'),
            size_hint=(None, None),
            size=(dp(100), dp(50)),
            pos_hint={'center_x': 0.5},
            y=Window.height / 2 + dp(180),
            opacity=1 if self.upgrade_level > 0 else 0
        )
        self.main_layout.add_widget(self.multiplier_label)

        self.music_button = Button(
            text="♫" if self.music_on else "🔇",
            size_hint=(None, None),
            size=(dp(50), dp(50)),
            pos_hint={'right': 0.98, 'y': 0.02},
            background_color=get_color_from_hex('#444444') if self.music_on else get_color_from_hex('#ff0000'),
            background_normal='',
            color=get_color_from_hex('#ffffff'),
            font_size=dp(30),
            on_press=self.toggle_music
        )
        self.main_layout.add_widget(self.music_button)

        self.settings_button = Button(
            text="Налаштування",
            size_hint=(None, None),
            size=(dp(150), dp(50)),
            pos_hint={'right': 0.98, 'top': 0.98},
            background_color=get_color_from_hex('#444444'),
            background_normal='',
            color=get_color_from_hex('#ffffff'),
            font_size=dp(20),
            on_press=self.show_settings
        )
        self.main_layout.add_widget(self.settings_button)

        self.shop_button = Button(
            text="Магазин",
            size_hint=(None, None),
            size=(dp(150), dp(50)),
            pos_hint={'x': 0.02, 'y': 0.02},
            background_color=get_color_from_hex('#444444'),
            background_normal='',
            color=get_color_from_hex('#ffffff'),
            font_size=dp(20),
            on_press=self.show_shop
        )
        self.main_layout.add_widget(self.shop_button)

    def show_shop(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        title = Label(
            text="Магазин",
            size_hint=(1, 0.1),
            font_size=dp(25),
            bold=True
        )
        content.add_widget(title)

        scroll_view = ShopScrollView(self)

        scroll_view.add_item('item1.png', '25,000 монет', 25000, 1)
        scroll_view.add_item('item2.png', '35,000 монет', 35000, 2)
        scroll_view.add_item('item3.png', '50,000 монет', 50000, 3)
        scroll_view.add_item('item4.png', 'БЕЗЦІННИЙ!', 0,
                             0)  # Тут item4.png використовується тільки для відображення в магазині

        content.add_widget(scroll_view)

        close_btn = Button(
            text="Закрити",
            size_hint=(1, 0.1),
            background_color=get_color_from_hex('#444444'),
            background_normal='',
            on_press=lambda x: self.shop_popup.dismiss()
        )
        content.add_widget(close_btn)

        self.shop_popup = Popup(
            title='',
            content=content,
            size_hint=(0.9, 0.8),
            auto_dismiss=False,
            separator_height=0
        )
        self.shop_popup.open()

    def show_settings(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))

        music_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        music_box.add_widget(Label(text="Музика:", size_hint_x=0.4))
        self.music_toggle = Button(
            text="Увімк." if self.music_on else "Вимк.",
            background_normal='',
            background_color=get_color_from_hex('#42f554' if self.music_on else '#ff0000'),
            on_press=self.toggle_music_setting
        )
        music_box.add_widget(self.music_toggle)
        content.add_widget(music_box)

        music_vol_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        music_vol_box.add_widget(Label(text="Гучність музики:", size_hint_x=0.4))
        self.music_slider = Slider(min=0, max=1, value=self.music_volume, step=0.1)
        self.music_slider.bind(value=self.update_music_volume)
        music_vol_box.add_widget(self.music_slider)
        content.add_widget(music_vol_box)

        sound_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        sound_box.add_widget(Label(text="Звуки:", size_hint_x=0.4))
        self.sound_toggle = Button(
            text="Увімк." if self.sound_on else "Вимк.",
            background_normal='',
            background_color=get_color_from_hex('#42f554' if self.sound_on else '#ff0000'),
            on_press=self.toggle_sound_setting
        )
        sound_box.add_widget(self.sound_toggle)
        content.add_widget(sound_box)

        sound_vol_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        sound_vol_box.add_widget(Label(text="Гучність звуків:", size_hint_x=0.4))
        self.sound_slider = Slider(min=0, max=1, value=self.sound_volume, step=0.1)
        self.sound_slider.bind(value=self.update_sound_volume)
        sound_vol_box.add_widget(self.sound_slider)
        content.add_widget(sound_vol_box)

        close_btn = Button(
            text="Закрити",
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#444444'),
            background_normal='',
            on_press=lambda x: self.settings_popup.dismiss()
        )
        content.add_widget(close_btn)

        self.settings_popup = Popup(
            title='Налаштування',
            content=content,
            size_hint=(0.8, 0.8),
            auto_dismiss=False
        )
        self.settings_popup.open()

    def toggle_music_setting(self, instance):
        self.music_on = not self.music_on
        instance.text = "Увімк." if self.music_on else "Вимк."
        instance.background_color = get_color_from_hex('#42f554' if self.music_on else '#ff0000')

        if self.bg_music:
            if self.music_on:
                self.bg_music.play()
                self.music_button.text = "Викл звук"
                self.music_button.background_color = get_color_from_hex('#444444')
            else:
                self.bg_music.stop()
                self.music_button.text = "Вкл звук"
                self.music_button.background_color = get_color_from_hex('#ff0000')

        self.save_progress()

    def toggle_sound_setting(self, instance):
        self.sound_on = not self.sound_on
        instance.text = "Увімк." if self.sound_on else "Вимк."
        instance.background_color = get_color_from_hex('#42f554' if self.sound_on else '#ff0000')
        self.save_progress()

    def update_music_volume(self, instance, value):
        self.music_volume = value
        if self.bg_music:
            self.bg_music.volume = value
        self.save_progress()

    def update_sound_volume(self, instance, value):
        self.sound_volume = value
        if self.click_sound:
            self.click_sound.volume = value
        self.save_progress()

    def update_ui_layout(self):
        self.balance_label.pos = (dp(10), Window.height - dp(60))
        self.multiplier_label.y = Window.height / 2 + dp(180)
        self.click_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.music_button.pos_hint = {'right': 0.98, 'y': 0.02}
        self.settings_button.pos_hint = {'right': 0.98, 'top': 0.98}
        self.shop_button.pos_hint = {'x': 0.02, 'y': 0.02}

    def add_coin(self, instance):
        if self.sound_on and self.click_sound:
            self.click_sound.play()

        self.coins += self.multiplier
        self.update_balance()

        if self.coins >= 10000 and self.upgrade_level < 3:
            self.unlock_upgrade(4, "x4!", '#28fc03')
        elif self.coins >= 1000 and self.upgrade_level < 2:
            self.unlock_upgrade(3, "x3!", '#42a1f5')
        elif self.coins >= 250 and self.upgrade_level < 1:
            self.unlock_upgrade(2, "x2!", '#42f554')

        self.save_progress()

    def update_balance(self):
        self.balance_label.text = f"[size=30][b]Монети:[/b] {self.coins}[/size]"

    def unlock_upgrade(self, new_multiplier, text, color):
        self.multiplier = new_multiplier
        self.upgrade_level += 1
        self.multiplier_label.text = f"[size=40][b]{text}[/b][/size]"
        self.multiplier_label.color = get_color_from_hex(color)

        # Просто показуємо мітку з множником без анімації кнопки
        anim = Animation(opacity=1, duration=0.5)
        anim.start(self.multiplier_label)

        self.save_progress()

    def toggle_music(self, instance):
        self.music_on = not self.music_on
        if self.bg_music:
            if self.music_on:
                self.bg_music.play()
                instance.text = "♫"
                instance.background_color = get_color_from_hex('#444444')
            else:
                self.bg_music.stop()
                instance.text = "🔇"
                instance.background_color = get_color_from_hex('#ff0000')
        self.save_progress()

    def on_stop(self):
        self.save_progress()
        if self.bg_music:
            self.bg_music.stop()


if __name__ == "__main__":
    ClickerApp().run()