"""✨ MustThings — 每日任务清单 (KivyMD)"""

# ── Window size for desktop testing ──────────────────────────
from kivy.config import Config

Config.set("graphics", "width", "420")
Config.set("graphics", "height", "780")
Config.set("kivy", "keyboard_mode", "system")  # Fix IME/Chinese input on Windows

import os
import sys
import datetime
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

from kivy.core.text import LabelBase

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView

import database

# ── Theme ────────────────────────────────────────────────────
PRIMARY = "#FF6B6B"        # Coral
PRIMARY_LIGHT = "#FF8E8E"
BG_WARM = "#FFF8F5"        # Warm off-white
CARD_WHITE = "#FFFFFF"
TEXT_GREY = "#9E9E9E"
ACCENT_GREEN = "#4CAF50"
BG_COMPLETED = "#F5F5F5"

# ── KV layout ───────────────────────────────────────────────
KV = """
ScreenManager:
    id: sm
    HomeScreen:
        name: "home"
    FixedTasksScreen:
        name: "fixed"


<SectionHeader@MDLabel>:
    font_style: "H6"
    theme_text_color: "Custom"
    text_color: "#FF6B6B"
    bold: True
    size_hint_y: None
    height: dp(40)
    padding: [dp(16), dp(8), 0, 0]


<EmptyHint@MDLabel>:
    text: "还没有任务，点 + 添加吧"
    theme_text_color: "Custom"
    text_color: "#BDBDBD"
    italic: True
    size_hint_y: None
    height: dp(48)
    padding: [dp(20), dp(12), 0, 0]


<HomeScreen>:
    BoxLayout:
        orientation: "vertical"
        spacing: 0

        MDTopAppBar:
            title: "今日任务"
            md_bg_color: "#FF6B6B"
            specific_text_color: 1, 1, 1, 1
            elevation: 2
            right_action_items: [["cog-outline", lambda x: app.open_fixed_tasks()]]

        BoxLayout:
            id: header_area
            orientation: "vertical"
            padding: [dp(20), dp(16), dp(20), dp(8)]
            spacing: dp(4)
            size_hint_y: None
            height: dp(90)
            md_bg_color: "#FF6B6B"

            MDLabel:
                id: greeting_label
                text: "早上好 ☀️"
                font_style: "H4"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                size_hint_y: None
                height: dp(42)

            MDLabel:
                id: date_label
                text: "2026年5月29日"
                font_style: "Body1"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 0.8
                size_hint_y: None
                height: dp(20)

        ScrollView:
            id: scroll
            do_scroll_x: False
            bar_width: dp(4)

            BoxLayout:
                id: task_container
                orientation: "vertical"
                spacing: dp(6)
                padding: [dp(16), dp(12), dp(16), dp(80)]
                size_hint_y: None
                height: self.minimum_height

    FloatLayout:
        MDFloatingActionButton:
            id: fab
            icon: "plus"
            md_bg_color: "#FF6B6B"
            pos_hint: {"center_x": 0.85, "center_y": 0.08}
            on_release: app.show_add_dialog()


<FixedTasksScreen>:
    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "管理固定任务"
            md_bg_color: "#FF6B6B"
            specific_text_color: 1, 1, 1, 1
            elevation: 2
            left_action_items: [["arrow-left", lambda x: app.go_home()]]

        ScrollView:
            do_scroll_x: False
            bar_width: dp(4)

            BoxLayout:
                id: fixed_container
                orientation: "vertical"
                spacing: dp(6)
                padding: [dp(16), dp(12), dp(16), dp(80)]
                size_hint_y: None
                height: self.minimum_height

    FloatLayout:
        MDFloatingActionButton:
            id: fixed_fab
            icon: "plus"
            md_bg_color: "#FF6B6B"
            pos_hint: {"center_x": 0.85, "center_y": 0.08}
            on_release: app.show_add_fixed_dialog()
"""

# (KV is loaded in MustThingsApp.build())


# ── Task Card widget ─────────────────────────────────────────
class TaskCard(MDCard):
    def __init__(self, task_data, app, **kwargs):
        super().__init__(**kwargs)
        self.task_data = task_data
        self.app_ref = app
        self.size_hint_y = None
        self.height = dp(60)
        self.radius = dp(12)
        self.elevation = 1
        self.padding = dp(4)
        self.spacing = dp(8)
        self.line_color = (0, 0, 0, 0)   # no border

        self.md_bg_color = self._rgba(CARD_WHITE)

        layout = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=1,
        )

        # ── Status toggle icon ──
        status_btn = MDIconButton(
            icon="circle-outline",
            size_hint_x=None,
            width=dp(48),
            theme_icon_color="Custom",
            icon_color="#BDBDBD",
            on_release=self._on_toggle,
        )
        status_btn.size_hint_y = 1
        layout.add_widget(status_btn)

        # ── Title ──
        self.title_label = MDLabel(
            text=task_data["title"],
            size_hint_x=1,
            size_hint_y=1,
            valign="middle",
        )
        layout.add_widget(self.title_label)

        # ── Delete button (only for temp tasks) ──
        if not task_data["is_fixed"]:
            del_btn = MDIconButton(
                icon="delete-outline",
                theme_icon_color="Custom",
                icon_color=TEXT_GREY,
                size_hint_x=None,
                width=dp(40),
                on_release=self._on_delete,
            )
            del_btn.size_hint_y = 1
            layout.add_widget(del_btn)

        self.add_widget(layout)

    def _rgba(self, hex_color):
        h = hex_color.lstrip("#")
        return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)) + (1,)

    def _on_toggle(self, *args):
        database.toggle_task(self.task_data["id"])
        self.app_ref.refresh_home()

    def _on_delete(self, *args):
        database.delete_daily_task(self.task_data["id"])
        self.app_ref.refresh_home()


# ── Fixed Task Row ───────────────────────────────────────────
class FixedTaskRow(MDCard):
    def __init__(self, task_data, app, **kwargs):
        super().__init__(**kwargs)
        self.task_data = task_data
        self.app_ref = app
        self.size_hint_y = None
        self.height = dp(60)
        self.radius = dp(12)
        self.elevation = 1
        self.padding = dp(4)
        self.line_color = (0, 0, 0, 0)
        self.md_bg_color = self._rgba(CARD_WHITE)

        layout = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=1)

        pin_icon = MDIconButton(
            icon="pin",
            size_hint_x=None,
            width=dp(44),
            theme_icon_color="Custom",
            icon_color=PRIMARY,
            on_release=lambda: None,
        )
        pin_icon.size_hint_y = 1
        layout.add_widget(pin_icon)

        title = MDLabel(
            text=task_data["title"],
            size_hint_x=1,
            size_hint_y=1,
            valign="middle",
        )
        layout.add_widget(title)

        del_btn = MDIconButton(
            icon="delete-outline",
            theme_icon_color="Custom",
            icon_color=TEXT_GREY,
            size_hint_x=None,
            width=dp(44),
            on_release=self._on_delete,
        )
        del_btn.size_hint_y = 1
        layout.add_widget(del_btn)

        self.add_widget(layout)

    def _rgba(self, hex_color):
        h = hex_color.lstrip("#")
        return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)) + (1,)

    def _on_delete(self, *args):
        database.delete_fixed_task(self.task_data["id"])
        self.app_ref.refresh_fixed()
        self.app_ref.refresh_home()


# ── Screen classes ───────────────────────────────────────────
class HomeScreen(MDScreen):
    pass


class FixedTasksScreen(MDScreen):
    pass


# ── App ──────────────────────────────────────────────────────
class MustThingsApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        database.init_db()

    def build(self):
        self._register_cjk_fonts()
        self.theme_cls.primary_palette = "Red"
        self.theme_cls.primary_hue = "400"
        self.theme_cls.theme_style = "Light"
        return Builder.load_string(KV)

    def _register_cjk_fonts(self):
        """Replace Roboto with a system CJK font so Chinese renders correctly."""
        # Try Windows paths first, then Android paths
        candidates = [
            # Windows
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/Noto Sans SC (TrueType).otf",
            "C:/Windows/Fonts/simhei.ttf",
            # Android
            "/system/fonts/NotoSansSC-Regular.otf",
            "/system/fonts/DroidSansFallback.ttf",
            "/system/fonts/NotoSansCJK-Regular.ttc",
        ]
        cjk = next((p for p in candidates if os.path.exists(p)), None)
        if cjk is None:
            return

        base_dir = os.path.dirname(cjk)
        bold_candidates = [
            os.path.join(base_dir, "msyhbd.ttc"),
            os.path.join(base_dir, "Noto Sans SC Bold (TrueType).otf"),
            os.path.join(base_dir, "NotoSansSC-Bold.otf"),
        ]
        cjk_bold = next((p for p in bold_candidates if os.path.exists(p)), cjk)

        light_candidates = [
            os.path.join(base_dir, "msyhl.ttc"),
        ]
        cjk_light = next((p for p in light_candidates if os.path.exists(p)), cjk)

        LabelBase.register(name="Roboto", fn_regular=cjk, fn_bold=cjk_bold)
        LabelBase.register(name="RobotoLight", fn_regular=cjk_light)
        LabelBase.register(name="RobotoMedium", fn_regular=cjk, fn_bold=cjk_bold)
        LabelBase.register(name="Default", fn_regular=cjk, fn_bold=cjk_bold)
        print(f"✅ CJK font registered: {cjk}")

    def on_start(self):
        self.today_str = datetime.date.today().isoformat()
        self._update_header()
        self.refresh_home()
        self._schedule_daily_refresh()
        self._schedule_nightly_reminder()

    # ── Header ────────────────────────────────────────────────
    def _update_header(self):
        now = datetime.datetime.now()
        hour = now.hour
        if hour < 6:
            greeting = "夜深了"
        elif hour < 9:
            greeting = "早上好"
        elif hour < 12:
            greeting = "上午好"
        elif hour < 14:
            greeting = "中午好"
        elif hour < 18:
            greeting = "下午好"
        else:
            greeting = "晚上好"

        weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
        date_str = f"{now.year}年{now.month}月{now.day}日 周{weekday_names[now.weekday()]}"

        try:
            home = self.root.get_screen("home")
            home.ids.greeting_label.text = greeting
            home.ids.date_label.text = date_str
        except (AttributeError, KeyError):
            pass

    # ── Task list rendering ───────────────────────────────────
    def refresh_home(self):
        home = self.root.get_screen("home")
        container = home.ids.task_container
        container.clear_widgets()

        self.today_str = datetime.date.today().isoformat()
        all_tasks = database.get_daily_tasks(self.today_str)

        fixed = [t for t in all_tasks if t["is_fixed"] and not t["is_completed"]]
        temp = [t for t in all_tasks if not t["is_fixed"] and not t["is_completed"]]

        # ── Fixed section ──
        container.add_widget(self._section_header("固定任务"))
        for t in fixed:
            container.add_widget(TaskCard(t, self))

        # ── Temp section ──
        container.add_widget(self._section_header("今日额外"))
        if not temp:
            container.add_widget(
                MDLabel(
                    text="还没有任务，点 + 添加吧",
                    theme_text_color="Custom",
                    text_color=self._rgba_obj("#BDBDBD"),
                    italic=True,
                    size_hint_y=None,
                    height=dp(48),
                    padding=[dp(20), dp(12), 0, 0],
                )
            )
        else:
            for t in temp:
                container.add_widget(TaskCard(t, self))

    def _section_header(self, text):
        return MDLabel(
            text=text,
            font_style="H6",
            theme_text_color="Custom",
            text_color=self._rgba_obj(PRIMARY),
            bold=True,
            size_hint_y=None,
            height=dp(40),
            padding=[dp(16), dp(8), 0, 0],
        )

    def _rgba(self, hex_color):
        h = hex_color.lstrip("#")
        return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)) + (1,)

    def _rgba_obj(self, hex_color):
        """Return a list (not tuple) for Kivy color properties."""
        return list(self._rgba(hex_color))

    # ── Add temporary task dialog ─────────────────────────────
    def show_add_dialog(self):
        from kivy.uix.popup import Popup
        from kivy.uix.textinput import TextInput

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(20), dp(12), dp(20), dp(12)],
        )

        ti = TextInput(
            hint_text="输入任务内容…",
            multiline=False,
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
        )
        content.add_widget(ti)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12))
        cancel_btn = MDFlatButton(text="取消")
        add_btn = MDFlatButton(
            text="添加",
            theme_text_color="Custom",
            text_color=self._rgba_obj(PRIMARY),
        )
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(add_btn)
        content.add_widget(btn_layout)

        popup = Popup(
            title="添加新任务",
            content=content,
            size_hint=(0.85, None),
            height=dp(200),
            auto_dismiss=False,
        )

        cancel_btn.bind(on_release=lambda *_: popup.dismiss())

        def do_add(*args):
            title = ti.text.strip()
            if title:
                database.add_temporary_task(title, self.today_str)
                self.refresh_home()
                home = self.root.get_screen("home")
                Clock.schedule_once(
                    lambda dt: setattr(home.ids.scroll, "scroll_y", 0), 0.1
                )
            popup.dismiss()

        add_btn.bind(on_release=do_add)
        popup.open()

    # ── Fixed tasks management ────────────────────────────────
    def open_fixed_tasks(self):
        self.root.current = "fixed"
        self.refresh_fixed()

    def refresh_fixed(self):
        screen = self.root.get_screen("fixed")
        container = screen.ids.fixed_container
        container.clear_widgets()

        tasks = database.get_fixed_tasks()

        container.add_widget(
            MDLabel(
                text="每天自动出现的任务：",
                theme_text_color="Custom",
                text_color=self._rgba_obj("#757575"),
                size_hint_y=None,
                height=dp(36),
                padding=[dp(16), dp(8), 0, 0],
            )
        )

        if not tasks:
            container.add_widget(
                MDLabel(
                    text="还没有固定任务，点 + 添加",
                    theme_text_color="Custom",
                    text_color=self._rgba_obj("#BDBDBD"),
                    italic=True,
                    size_hint_y=None,
                    height=dp(48),
                    padding=[dp(20), dp(12), 0, 0],
                )
            )
        else:
            for t in tasks:
                container.add_widget(FixedTaskRow(t, self))

    def show_add_fixed_dialog(self):
        from kivy.uix.popup import Popup
        from kivy.uix.textinput import TextInput

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(20), dp(12), dp(20), dp(12)],
        )

        ti = TextInput(
            hint_text="输入固定任务内容…",
            multiline=False,
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
        )
        content.add_widget(ti)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12))
        cancel_btn = MDFlatButton(text="取消")
        add_btn = MDFlatButton(
            text="添加",
            theme_text_color="Custom",
            text_color=self._rgba_obj(PRIMARY),
        )
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(add_btn)
        content.add_widget(btn_layout)

        popup = Popup(
            title="添加固定任务",
            content=content,
            size_hint=(0.85, None),
            height=dp(200),
            auto_dismiss=False,
        )

        cancel_btn.bind(on_release=lambda *_: popup.dismiss())

        def do_add(*args):
            title = ti.text.strip()
            if title:
                database.add_fixed_task(title)
                self.refresh_fixed()
            popup.dismiss()

        add_btn.bind(on_release=do_add)
        popup.open()


    def go_home(self):
        self.root.current = "home"

    # ── Notifications ─────────────────────────────────────────
    def _schedule_nightly_reminder(self):
        """Schedule the 23:00 daily reminder."""
        now = datetime.datetime.now()
        target = now.replace(hour=23, minute=0, second=0, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        seconds = (target - now).total_seconds()

        Clock.schedule_once(lambda dt: self._send_reminder(), seconds)
        print(f"⏰ 提醒已设置在 {target.strftime('%H:%M')} (还有 {int(seconds//3600)} 小时 {int(seconds%3600//60)} 分钟)")

    def _send_reminder(self):
        """Check incomplete tasks and send desktop notification."""
        today = datetime.date.today().isoformat()
        incomplete = database.get_incomplete_tasks(today)
        if incomplete:
            title_list = "\n".join(f"• {t}" for t in incomplete[:8])
            remaining = len(incomplete) - 8
            if remaining > 0:
                title_list += f"\n…还有 {remaining} 项"

            try:
                from plyer import notification

                notification.notify(
                    title="🌙 睡前提醒",
                    message=f"今天还有 {len(incomplete)} 项任务未完成:\n{title_list}",
                    timeout=10,
                    app_name="MustThings",
                )
            except Exception as e:
                print(f"通知发送失败: {e}")
        else:
            print("🎉 所有任务都完成了！")

        # Reschedule for tomorrow
        self._schedule_nightly_reminder()

    def _schedule_daily_refresh(self):
        """Refresh UI at midnight so the date/tasks roll over."""
        now = datetime.datetime.now()
        target = now.replace(hour=0, minute=0, second=5, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        seconds = (target - now).total_seconds()
        Clock.schedule_once(lambda dt: self._on_midnight(), seconds)

    def _on_midnight(self):
        self._update_header()
        self.refresh_home()
        self._schedule_daily_refresh()


# ── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    MustThingsApp().run()
