"""
ui_theme.py - Theme & Custom Components for Rapihin V2
Ultra-dark matte obsidian with Cyber Lime / Neon Chartreuse accents.
"""

import ctypes
import os
import sys
from pathlib import Path
import customtkinter as ctk

FONT_FAMILY = "Plus Jakarta Sans"

def load_custom_fonts():
    if sys.platform != "win32":
        return
    base_dir = getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parent
    fonts_dir = Path(base_dir) / "assets" / "fonts"
    if not fonts_dir.exists():
        return

    FR_PRIVATE = 0x10
    gdi32 = ctypes.windll.gdi32
    for font_file in fonts_dir.glob("*.ttf"):
        try:
            gdi32.AddFontResourceExW(str(font_file.resolve()), FR_PRIVATE, 0)
        except Exception:
            pass


# Color Palette (Matte Charcoal & Cyber Lime)
BG_COLOR = "#0D0D0E"
CARD_BG = "#161618"
CARD_HEADER = "#1E1E22"
CARD_HOVER = "#242429"
BORDER_COLOR = "#222226"
BORDER_LIGHT = "#2F2F36"

TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8E8E93"
TEXT_MUTED = "#5A5A60"

# Accents
ACCENT_LIME = "#CCFF00"
ACCENT_LIME_GLOW = "#E2FF4D"
ACCENT_LIME_HOVER = "#B8E600"
ACCENT_MUTED_LIME = "#1E2606"

# Stabilo Highlight Colors
STABILO_YELLOW = "#FFE600"
STABILO_BG = "#2B2605"

SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
INFO = "#38BDF8"


def get_font(size=13, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


class GlowingProgressBar(ctk.CTkFrame):
    def __init__(self, master, height=22, corner_radius=11, **kwargs):
        super().__init__(
            master,
            height=height,
            corner_radius=corner_radius,
            fg_color="#1E1E22",
            border_width=1,
            border_color="#2A2A30",
            **kwargs
        )
        self.pack_propagate(False)
        self.progress_val = 0.0

        self.fill_bar = ctk.CTkFrame(
            self,
            corner_radius=corner_radius,
            fg_color=ACCENT_LIME,
            border_width=0
        )
        self.fill_bar.place(relx=0, rely=0, relwidth=0.0, relheight=1.0)

        self.knob = ctk.CTkLabel(
            self.fill_bar,
            text="⋮",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#121214",
            fg_color=ACCENT_LIME_GLOW,
            corner_radius=9,
            width=18,
            height=18
        )
        self.knob.place(relx=1.0, rely=0.5, anchor="e", x=-2)

    def set_progress(self, ratio: float):
        self.progress_val = max(0.0, min(1.0, ratio))
        self.fill_bar.place_configure(relwidth=self.progress_val)
        if self.progress_val < 0.04:
            self.knob.place_forget()
        else:
            self.knob.place(relx=1.0, rely=0.5, anchor="e", x=-2)


class CategoryChip(ctk.CTkFrame):
    def __init__(self, master, icon="📁", name="Docs", count=0, size_str="0 MB", **kwargs):
        super().__init__(
            master,
            fg_color="#1E1E22",
            corner_radius=12,
            border_width=1,
            border_color="#2A2A30",
            **kwargs
        )
        self.icon_lbl = ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=13),
            text_color=ACCENT_LIME
        )
        self.icon_lbl.pack(side="left", padx=(10, 4), pady=6)

        self.text_lbl = ctk.CTkLabel(
            self,
            text=f"{name}: {count} ({size_str})",
            font=get_font(11, "bold"),
            text_color=TEXT_PRIMARY
        )
        self.text_lbl.pack(side="left", padx=(2, 10), pady=6)


class StabiloChip(ctk.CTkFrame):
    def __init__(self, master, folder_name="Folder", on_remove=None, **kwargs):
        super().__init__(
            master,
            fg_color=STABILO_BG,
            corner_radius=10,
            border_width=1,
            border_color=STABILO_YELLOW,
            **kwargs
        )
        lbl_icon = ctk.CTkLabel(self, text="🛡️", font=ctk.CTkFont(size=11))
        lbl_icon.pack(side="left", padx=(8, 2), pady=4)

        lbl = ctk.CTkLabel(
            self,
            text=folder_name,
            font=get_font(11, "bold"),
            text_color=STABILO_YELLOW
        )
        lbl.pack(side="left", padx=4, pady=4)

        if on_remove:
            btn_del = ctk.CTkButton(
                self,
                text="✕",
                width=18,
                height=18,
                corner_radius=9,
                fg_color="transparent",
                hover_color="#443905",
                text_color=STABILO_YELLOW,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=on_remove
            )
            btn_del.pack(side="left", padx=(2, 6), pady=4)


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title="AVERAGE SALE VALUE", value="0", subtitle="", icon_text="✦", is_highlight=False, **kwargs):
        border_col = BORDER_LIGHT if not is_highlight else ACCENT_LIME
        super().__init__(
            master,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=border_col,
            **kwargs
        )

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(12, 4))

        self.lbl_icon = ctk.CTkLabel(
            header_frame,
            text=icon_text,
            font=get_font(12, "bold"),
            text_color=ACCENT_LIME if is_highlight else TEXT_MUTED
        )
        self.lbl_icon.pack(side="left")

        self.lbl_title = ctk.CTkLabel(
            header_frame,
            text=title.upper(),
            font=get_font(11, "bold"),
            text_color=TEXT_SECONDARY
        )
        self.lbl_title.pack(side="left", padx=6)

        self.lbl_val = ctk.CTkLabel(
            self,
            text=value,
            font=get_font(22, "bold"),
            text_color=ACCENT_LIME if is_highlight else TEXT_PRIMARY,
            anchor="w"
        )
        self.lbl_val.pack(fill="x", padx=16, pady=(2, 2))

        self.lbl_sub = ctk.CTkLabel(
            self,
            text=subtitle,
            font=get_font(11, "normal"),
            text_color=TEXT_MUTED,
            anchor="w"
        )
        self.lbl_sub.pack(fill="x", padx=16, pady=(0, 12))

    def update_data(self, value=None, subtitle=None, text_color=None):
        if value is not None:
            self.lbl_val.configure(text=str(value))
        if subtitle is not None:
            self.lbl_sub.configure(text=str(subtitle))
        if text_color is not None:
            self.lbl_val.configure(text_color=text_color)


# --- Custom Frameless Modal Dialog Base ---

class CustomModalDialog(ctk.CTkToplevel):
    """
    Clean borderless dialog with subtle dark charcoal border matching main app.
    Zero awkward corner gaps.
    """
    def __init__(self, parent, title="Dialog", width=460, height=270):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self._drag_x = 0
        self._drag_y = 0

        self.overrideredirect(True)
        self.configure(fg_color=CARD_BG)

        # Center on parent window
        parent.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - width) // 2
        py = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"{width}x{height}+{max(0, px)}+{max(0, py)}")

        # Clean outer container with soft dark matte border (no green bleed)
        self.outer_card = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=16,
            border_width=1,
            border_color=BORDER_LIGHT
        )
        self.outer_card.pack(fill="both", expand=True)

        # Header with matching corner radius
        header = ctk.CTkFrame(self.outer_card, fg_color=CARD_HEADER, height=42, corner_radius=14)
        header.pack(fill="x", padx=3, pady=(3, 0))
        header.pack_propagate(False)
        header.bind("<ButtonPress-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)

        self.lbl_title = ctk.CTkLabel(
            header,
            text=title,
            font=get_font(12, "bold"),
            text_color=TEXT_PRIMARY
        )
        self.lbl_title.pack(side="left", padx=14)
        self.lbl_title.bind("<ButtonPress-1>", self._start_drag)
        self.lbl_title.bind("<B1-Motion>", self._on_drag)

        btn_close = ctk.CTkButton(
            header,
            text="✕",
            width=28,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            hover_color=DANGER,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._cancel
        )
        btn_close.pack(side="right", padx=8)

        # Body
        self.body = ctk.CTkFrame(self.outer_card, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=20, pady=12)

        self.transient(parent)
        self.grab_set()

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")

    def _cancel(self):
        self.result = None
        self.destroy()
