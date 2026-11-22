"""
rapihin.py - Rapihin V2.0 Desktop Application
Theme: Sleek Dark Matte & Cyber Lime / Neon Chartreuse (Sales Target Aesthetic)
Features:
- Subfolder Dropdown Autodetection for Stabilo & Custom Rules (no manual typo)
- Custom Frameless Pop-up Modals matching dark matte theme
- Realistic Folder Messiness & Clutter Index calculation
- Stabilo (Protected Folder Exclusions)
- Custom Keyword Routing Rules
- Custom Borderless Frameless Window
- Instant Folder Quick-Inspect (JPG, PDF, EXE breakdown)
- Fast Tiered Hashing for Duplicates
- Bilingual Support (ID / EN)
- Donate Link (http://sandiana.my.id)
"""

import ctypes
import json
import os
import queue
import shutil
import sys
import threading
import webbrowser
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

# Drag & drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    BASES = (ctk.CTk, TkinterDnD.DnDWrapper)
except Exception:
    TkinterDnD = None
    DND_FILES = None
    BASES = (ctk.CTk,)

from PIL import Image

import core_engine as engine
import ui_theme as theme

APP_NAME = "rapihin"
APP_VERSION = engine.APP_VERSION
DONATE_URL = "http://sandiana.my.id"
REPO_URL = f"https://github.com/{engine.GITHUB_REPO}"

TR = {
    "id": {
        "title": "rapihin",
        "subtitle": "Smart Windows Desktop & File Organizer",
        "folder_card": "FOLDER TARGET",
        "placeholder": "Pilih atau seret folder ke sini...",
        "btn_browse": "Pilih Folder",
        "quick_inspect_title": "ANALISIS AWAL ISI FOLDER",
        "inspect_clean": "Status Folder: Sangat Rapi",
        "inspect_messy": "Status: Sangat Berantakan ({count} jenis file campur aduk)",
        "card_clutter_title": "INDEKS KERAPIAN FOLDER",
        "neat_perfect": "Folder Bersih & Teratur",
        "neat_messy": "Butuh Dirapikan Segera",
        "stabilo_title": "STABILO FOLDER (FOLDER PENTING & KEBAL)",
        "stabilo_hint": "Folder yang distabilo TIDAK AKAN disentuh, dipindah, atau diotak-atik sama sekali.",
        "btn_add_stabilo": "+ Stabilo Folder",
        "custom_rules_title": "ATURAN KHUSUS KATA KUNCI (CUSTOM ROUTING)",
        "custom_rules_hint": "Contoh: File ada kata 'skripsi' otomatis masuk folder 'Penting_Skripsi'.",
        "btn_add_rule": "+ Tambah Aturan",
        "options_title": "PENGATURAN PINTAR",
        "opt_type": "Kelompokkan per Kategori File",
        "opt_exif": "Gunakan Tanggal Foto EXIF / Artis Audio",
        "opt_date": "Struktur Folder Tanggal",
        "opt_dup": "Deteksi Duplikat Cepat (Tiered Hash)",
        "opt_recycle": "Kirim Duplikat ke Recycle Bin Windows",
        "opt_sub": "Pindai Termasuk Subfolder",
        "opt_clean": "Hapus Folder Kosong Otomatis",
        "opt_context": "Integrasi Klik Kanan Windows ('Rapihin')",
        "opt_junk": "Deteksi Versi Installer Lama & File 0-Byte",
        "btn_preview": "Pratinjau Hasil",
        "btn_run": "Rapihin Sekarang",
        "btn_undo": "Undo Terakhir",
        "status_ready": "Pilih folder untuk melihat analisis awal.",
        "status_scanning": "Memindai file & menganalisis isi folder...",
        "status_running": "Mengeksekusi penataan file...",
        "update_available": "✦ Update Baru {ver} Tersedia! Klik untuk download",
    },
    "en": {
        "title": "rapihin",
        "subtitle": "Smart Windows Desktop & File Organizer",
        "folder_card": "TARGET FOLDER",
        "placeholder": "Select or drag a folder here...",
        "btn_browse": "Browse Folder",
        "quick_inspect_title": "INITIAL FOLDER BREAKDOWN",
        "inspect_clean": "Folder Status: Very Neat",
        "inspect_messy": "Status: Highly Cluttered ({count} mixed file types)",
        "card_clutter_title": "FOLDER TIDINESS SCORE",
        "neat_perfect": "Clean & Organized",
        "neat_messy": "Needs Urgent Cleanup",
        "stabilo_title": "STABILO FOLDERS (PROTECTED & IMMUNE)",
        "stabilo_hint": "Folders highlighted with Stabilo will NEVER be touched or moved.",
        "btn_add_stabilo": "+ Highlight Folder",
        "custom_rules_title": "CUSTOM KEYWORD ROUTING (SAFE FILTER)",
        "custom_rules_hint": "Example: File with keyword 'invoice' automatically goes to 'Finance/Invoices'.",
        "btn_add_rule": "+ Add Rule",
        "options_title": "SMART CONFIGURATION",
        "opt_type": "Organize by File Category",
        "opt_exif": "Use Camera EXIF Date / Audio Artist",
        "opt_date": "Date Folder Structure",
        "opt_dup": "Fast Duplicate Detection (Tiered Hash)",
        "opt_recycle": "Send Duplicates to Windows Recycle Bin",
        "opt_sub": "Include Subfolders in Scan",
        "opt_clean": "Clean Empty Folders Automatically",
        "opt_context": "Windows Right-Click Context Menu",
        "opt_junk": "Clean Old Installer Versions & 0-Byte Files",
        "btn_preview": "Preview Changes",
        "btn_run": "Organize Now",
        "btn_undo": "Undo Last",
        "status_ready": "Select a folder to view initial inspection.",
        "status_scanning": "Scanning files and parsing folder content...",
        "status_running": "Executing organization plan...",
        "update_available": "✦ New Update {ver} Available! Click to download",
    }
}

CAT_ICONS = {
    "images": "🖼️",
    "video": "🎬",
    "docs": "📄",
    "audio": "🎵",
    "archives": "📦",
    "installers": "⚙️",
    "code": "💻",
    "other": "📁"
}


def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parent
    return Path(base) / relative_path


def get_settings_file():
    appdata = Path(os.environ.get("APPDATA") or Path.home()) / APP_NAME
    appdata.mkdir(parents=True, exist_ok=True)
    return appdata / "settings.json"


# --- Custom Frameless Dialogs for Stabilo & Rules ---

class StabiloDialog(theme.CustomModalDialog):
    """Custom frameless popup that lets user pick an existing subfolder directly or type a new one"""
    def __init__(self, parent, subfolders):
        super().__init__(parent, title="🛡️ Stabilo Folder Penting", width=460, height=270)
        self.subfolders = subfolders

        lbl_desc = ctk.CTkLabel(
            self.body,
            text="Pilih subfolder yang ada di target, atau buat nama baru:",
            font=theme.get_font(12, "normal"),
            text_color=theme.TEXT_SECONDARY
        )
        lbl_desc.pack(anchor="w", pady=(0, 8))

        # Dropdown options
        options = ["(Pilih dari subfolder yang ada...)"] + sorted(self.subfolders)
        self.combo_var = ctk.StringVar(value=options[0])

        self.combo = ctk.CTkComboBox(
            self.body,
            values=options,
            variable=self.combo_var,
            font=theme.get_font(12, "normal"),
            height=38,
            corner_radius=10,
            fg_color="#0F0F11",
            border_color=theme.BORDER_LIGHT,
            button_color=theme.ACCENT_MUTED_LIME,
            button_hover_color=theme.ACCENT_LIME,
            dropdown_fg_color="#18181C",
            dropdown_hover_color="#25252C",
            dropdown_text_color=theme.TEXT_PRIMARY,
            command=self._on_combo_select
        )
        self.combo.pack(fill="x", pady=(0, 10))

        # Manual entry field (auto-populated by dropdown)
        self.entry_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(
            self.body,
            textvariable=self.entry_var,
            placeholder_text="Atau ketik nama folder di sini...",
            font=theme.get_font(12, "normal"),
            height=38,
            corner_radius=10,
            fg_color="#0F0F11",
            border_color=theme.BORDER_LIGHT,
            text_color=theme.TEXT_PRIMARY
        )
        self.entry.pack(fill="x", pady=(0, 16))

        # Action Buttons
        btn_box = ctk.CTkFrame(self.body, fg_color="transparent")
        btn_box.pack(fill="x")

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Batal",
            font=theme.get_font(12, "bold"),
            height=36,
            corner_radius=10,
            fg_color="#24242A",
            hover_color="#2F2F36",
            text_color=theme.TEXT_SECONDARY,
            command=self._cancel
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_save = ctk.CTkButton(
            btn_box,
            text="Simpan & Lindungi",
            font=theme.get_font(12, "bold"),
            height=36,
            corner_radius=10,
            fg_color=theme.ACCENT_LIME,
            hover_color=theme.ACCENT_LIME_HOVER,
            text_color="#121214",
            command=self._on_save
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _on_combo_select(self, choice):
        if not choice.startswith("("):
            self.entry_var.set(choice)

    def _on_save(self):
        val = self.entry_var.get().strip()
        if val:
            self.result = val
            self.destroy()


class CustomRuleDialog(theme.CustomModalDialog):
    """Custom frameless popup for adding a keyword routing rule with subfolder picker"""
    def __init__(self, parent, subfolders):
        super().__init__(parent, title="🔍 Aturan Kata Kunci Khusus", width=480, height=340)
        self.subfolders = subfolders

        # Keyword
        lbl_kw = ctk.CTkLabel(
            self.body,
            text="1. Kata kunci dalam nama file (misal: 'skripsi', 'invoice'):",
            font=theme.get_font(11, "bold"),
            text_color=theme.ACCENT_LIME
        )
        lbl_kw.pack(anchor="w", pady=(0, 4))

        self.kw_entry = ctk.CTkEntry(
            self.body,
            placeholder_text="Contoh: skripsi",
            font=theme.get_font(12, "normal"),
            height=36,
            corner_radius=10,
            fg_color="#0F0F11",
            border_color=theme.BORDER_LIGHT,
            text_color=theme.TEXT_PRIMARY
        )
        self.kw_entry.pack(fill="x", pady=(0, 10))

        # Target Folder
        lbl_dest = ctk.CTkLabel(
            self.body,
            text="2. Pilih folder tujuan dari subfolder yang ada, atau buat baru:",
            font=theme.get_font(11, "bold"),
            text_color=theme.TEXT_PRIMARY
        )
        lbl_dest.pack(anchor="w", pady=(0, 4))

        options = ["(Pilih dari subfolder yang ada...)"] + sorted(self.subfolders)
        self.combo_var = ctk.StringVar(value=options[0])

        self.combo = ctk.CTkComboBox(
            self.body,
            values=options,
            variable=self.combo_var,
            font=theme.get_font(12, "normal"),
            height=36,
            corner_radius=10,
            fg_color="#0F0F11",
            border_color=theme.BORDER_LIGHT,
            button_color=theme.ACCENT_MUTED_LIME,
            button_hover_color=theme.ACCENT_LIME,
            dropdown_fg_color="#18181C",
            dropdown_hover_color="#25252C",
            dropdown_text_color=theme.TEXT_PRIMARY,
            command=self._on_combo_select
        )
        self.combo.pack(fill="x", pady=(0, 8))

        self.dest_entry = ctk.CTkEntry(
            self.body,
            placeholder_text="Contoh: Dokumen/Penting_Skripsi",
            font=theme.get_font(12, "normal"),
            height=36,
            corner_radius=10,
            fg_color="#0F0F11",
            border_color=theme.BORDER_LIGHT,
            text_color=theme.TEXT_PRIMARY
        )
        self.dest_entry.pack(fill="x", pady=(0, 16))

        # Action Buttons
        btn_box = ctk.CTkFrame(self.body, fg_color="transparent")
        btn_box.pack(fill="x")

        btn_cancel = ctk.CTkButton(
            btn_box,
            text="Batal",
            font=theme.get_font(12, "bold"),
            height=36,
            corner_radius=10,
            fg_color="#24242A",
            hover_color="#2F2F36",
            text_color=theme.TEXT_SECONDARY,
            command=self._cancel
        )
        btn_cancel.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_save = ctk.CTkButton(
            btn_box,
            text="Simpan Aturan",
            font=theme.get_font(12, "bold"),
            height=36,
            corner_radius=10,
            fg_color=theme.ACCENT_LIME,
            hover_color=theme.ACCENT_LIME_HOVER,
            text_color="#121214",
            command=self._on_save
        )
        btn_save.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _on_combo_select(self, choice):
        if not choice.startswith("("):
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, choice)

    def _on_save(self):
        kw = self.kw_entry.get().strip().lower()
        dest = self.dest_entry.get().strip()
        if kw and dest:
            self.result = {"keyword": kw, "folder": dest}
            self.destroy()


class RapihinApp(*BASES):
    def __init__(self):
        super().__init__()
        theme.load_custom_fonts()

        self.dnd_available = False
        if TkinterDnD is not None:
            try:
                self.TkdndVersion = TkinterDnD._require(self)
                self.dnd_available = True
            except Exception:
                self.dnd_available = False

        ctk.set_appearance_mode("dark")
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("920x890")
        self.minsize(860, 820)
        self.configure(fg_color=theme.BG_COLOR)

        self.overrideredirect(True)
        self._set_window_icon()

        # Settings & State
        self.cfg = self._load_settings()
        self.lang = self.cfg.get("lang", "id")
        self.folder_var = ctk.StringVar(value=self.cfg.get("folder", ""))
        self.date_mode = ctk.StringVar(value=self.cfg.get("date_mode", "month"))

        # Stabilo & Custom Rules
        self.stabilo_folders = set(self.cfg.get("stabilo_folders", ["Penting", "Arsip_Pribadi"]))
        self.custom_rules = self.cfg.get("custom_rules", [
            {"keyword": "skripsi", "folder": "Dokumen/Penting_Skripsi"},
            {"keyword": "invoice", "folder": "Dokumen/Keuangan_Invoice"},
            {"keyword": "rahasia", "folder": "Dokumen/Pribadi_Aman"}
        ])

        # Subfolders detected in current target folder
        self.current_subfolders = []

        # Feature Toggles
        self.sw_type = ctk.BooleanVar(value=self.cfg.get("sw_type", True))
        self.sw_exif = ctk.BooleanVar(value=self.cfg.get("sw_exif", True))
        self.sw_dup = ctk.BooleanVar(value=self.cfg.get("sw_dup", True))
        self.sw_recycle = ctk.BooleanVar(value=self.cfg.get("sw_recycle", False))
        self.sw_sub = ctk.BooleanVar(value=self.cfg.get("sw_sub", False))
        self.sw_clean = ctk.BooleanVar(value=self.cfg.get("sw_clean", True))
        self.sw_junk = ctk.BooleanVar(value=self.cfg.get("sw_junk", True))
        self.sw_context = ctk.BooleanVar(value=self.cfg.get("sw_context", False))

        self.worker_busy = False
        self.current_preview_plan = None
        self.update_info = None

        self._drag_start_x = 0
        self._drag_start_y = 0

        self._build_ui()
        self._check_for_updates_background()

        if len(sys.argv) > 1:
            arg_path = Path(sys.argv[1])
            if arg_path.is_dir():
                self.folder_var.set(str(arg_path))
                self._quick_inspect_folder(arg_path)
        elif self.folder_var.get() and Path(self.folder_var.get()).is_dir():
            self._quick_inspect_folder(Path(self.folder_var.get()))

    def _set_window_icon(self):
        try:
            icon_ico = resource_path("rapihin.ico")
            if icon_ico.exists():
                self.iconbitmap(str(icon_ico))
        except Exception:
            pass

    def _load_settings(self):
        s_file = get_settings_file()
        if s_file.exists():
            try:
                with open(s_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_settings(self):
        s_file = get_settings_file()
        data = {
            "lang": self.lang,
            "folder": self.folder_var.get(),
            "date_mode": self.date_mode.get(),
            "stabilo_folders": list(self.stabilo_folders),
            "custom_rules": self.custom_rules,
            "sw_type": self.sw_type.get(),
            "sw_exif": self.sw_exif.get(),
            "sw_dup": self.sw_dup.get(),
            "sw_recycle": self.sw_recycle.get(),
            "sw_sub": self.sw_sub.get(),
            "sw_clean": self.sw_clean.get(),
            "sw_junk": self.sw_junk.get(),
            "sw_context": self.sw_context.get(),
        }
        try:
            with open(s_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def t(self, key):
        return TR.get(self.lang, TR["id"]).get(key, key)

    def _get_target_subfolders(self):
        """Returns detected subfolder names in current selected folder"""
        folder_str = self.folder_var.get().strip()
        sub_list = []
        if folder_str:
            p = Path(folder_str)
            if p.exists() and p.is_dir():
                try:
                    for d in p.iterdir():
                        if d.is_dir() and not d.name.startswith(".") and d.name not in engine.SKIP_DIRS:
                            sub_list.append(d.name)
                except Exception:
                    pass
        return sub_list

    # --- UI Construction ---

    def _build_ui(self):
        self.root_frame = ctk.CTkFrame(
            self,
            fg_color=theme.BG_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=theme.BORDER_LIGHT
        )
        self.root_frame.pack(fill="both", expand=True)

        self._build_custom_titlebar(self.root_frame)

        self.scroll_container = ctk.CTkScrollableFrame(
            self.root_frame,
            fg_color="transparent",
            scrollbar_button_color=theme.BORDER_COLOR,
            scrollbar_button_hover_color=theme.ACCENT_LIME
        )
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Update Banner
        self.update_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=theme.ACCENT_MUTED_LIME,
            border_width=1,
            border_color=theme.ACCENT_LIME,
            corner_radius=12
        )
        self.lbl_update = ctk.CTkLabel(
            self.update_card,
            text="",
            font=theme.get_font(12, "bold"),
            text_color=theme.ACCENT_LIME,
            cursor="hand2"
        )
        self.lbl_update.pack(padx=16, pady=8)
        self.lbl_update.bind("<Button-1>", lambda e: self._open_update_link())

        self._build_folder_card(self.scroll_container)
        self._build_inspect_card(self.scroll_container)
        self._build_progress_capsule(self.scroll_container)
        self._build_metric_grid(self.scroll_container)
        self._build_stabilo_card(self.scroll_container)
        self._build_rules_card(self.scroll_container)
        self._build_options_card(self.scroll_container)
        self._build_actions_and_log(self.scroll_container)

    def _build_custom_titlebar(self, parent):
        titlebar = ctk.CTkFrame(parent, fg_color=theme.CARD_HEADER, height=44, corner_radius=14)
        titlebar.pack(fill="x", padx=6, pady=6)
        titlebar.pack_propagate(False)

        titlebar.bind("<ButtonPress-1>", self._on_drag_start)
        titlebar.bind("<B1-Motion>", self._on_drag_motion)

        left_box = ctk.CTkFrame(titlebar, fg_color="transparent")
        left_box.pack(side="left", padx=12)
        left_box.bind("<ButtonPress-1>", self._on_drag_start)
        left_box.bind("<B1-Motion>", self._on_drag_motion)

        icon_png = resource_path("assets/icon.png")
        if icon_png.exists():
            try:
                pil_img = Image.open(icon_png)
                ctk_icon = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(24, 24))
                lbl_icon = ctk.CTkLabel(left_box, image=ctk_icon, text="")
                lbl_icon.pack(side="left", padx=(0, 8))
            except Exception:
                pass

        self.lbl_logo = ctk.CTkLabel(
            left_box,
            text=APP_NAME.lower(),
            font=theme.get_font(18, "bold"),
            text_color=theme.TEXT_PRIMARY
        )
        self.lbl_logo.pack(side="left")

        lbl_dot = ctk.CTkLabel(
            left_box,
            text=".",
            font=theme.get_font(22, "bold"),
            text_color=theme.ACCENT_LIME
        )
        lbl_dot.pack(side="left")

        right_box = ctk.CTkFrame(titlebar, fg_color="transparent")
        right_box.pack(side="right", padx=6)

        self.btn_lang = ctk.CTkButton(
            right_box,
            text=self.lang.upper(),
            width=40,
            height=26,
            corner_radius=8,
            fg_color="#24242A",
            border_width=1,
            border_color="#303038",
            text_color=theme.TEXT_PRIMARY,
            hover_color=theme.CARD_HOVER,
            font=theme.get_font(11, "bold"),
            command=self._toggle_language
        )
        self.btn_lang.pack(side="left", padx=3)

        btn_donate = ctk.CTkButton(
            right_box,
            text="☕ Donate",
            width=70,
            height=26,
            corner_radius=8,
            fg_color=theme.ACCENT_MUTED_LIME,
            border_width=1,
            border_color=theme.ACCENT_LIME,
            text_color=theme.ACCENT_LIME,
            hover_color="#2A3508",
            font=theme.get_font(11, "bold"),
            command=lambda: webbrowser.open(DONATE_URL)
        )
        btn_donate.pack(side="left", padx=3)

        btn_github = ctk.CTkButton(
            right_box,
            text="GitHub",
            width=60,
            height=26,
            corner_radius=8,
            fg_color="#24242A",
            border_width=1,
            border_color="#303038",
            text_color=theme.TEXT_SECONDARY,
            hover_color=theme.CARD_HOVER,
            font=theme.get_font(11, "normal"),
            command=lambda: webbrowser.open(REPO_URL)
        )
        btn_github.pack(side="left", padx=3)

        btn_min = ctk.CTkButton(
            right_box,
            text="—",
            width=30,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            text_color=theme.TEXT_SECONDARY,
            hover_color="#24242A",
            font=theme.get_font(11, "bold"),
            command=self._minimize_window
        )
        btn_min.pack(side="left", padx=2)

        btn_close = ctk.CTkButton(
            right_box,
            text="✕",
            width=30,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            text_color=theme.TEXT_SECONDARY,
            hover_color="#EF4444",
            font=theme.get_font(11, "bold"),
            command=self._close_window
        )
        btn_close.pack(side="left", padx=2)

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        deltax = event.x - self._drag_start_x
        deltay = event.y - self._drag_start_y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def _minimize_window(self):
        self.withdraw()
        self.overrideredirect(False)
        self.iconify()
        self.bind("<FocusIn>", self._on_restore)

    def _on_restore(self, event):
        self.unbind("<FocusIn>")
        self.overrideredirect(True)
        self.deiconify()

    def _close_window(self):
        self._save_settings()
        self.destroy()

    def _build_folder_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=theme.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=theme.BORDER_COLOR
        )
        card.pack(fill="x", pady=(8, 12), ipady=4)

        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(12, 6))

        self.lbl_target_title = ctk.CTkLabel(
            header_row,
            text=self.t("folder_card"),
            font=theme.get_font(11, "bold"),
            text_color=theme.TEXT_MUTED
        )
        self.lbl_target_title.pack(side="left")

        input_row = ctk.CTkFrame(card, fg_color="transparent")
        input_row.pack(fill="x", padx=16, pady=(0, 12))

        self.entry_folder = ctk.CTkEntry(
            input_row,
            textvariable=self.folder_var,
            placeholder_text=self.t("placeholder"),
            font=theme.get_font(13, "normal"),
            height=44,
            corner_radius=12,
            fg_color="#0F0F11",
            border_color=theme.BORDER_COLOR,
            text_color=theme.TEXT_PRIMARY
        )
        self.entry_folder.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse = ctk.CTkButton(
            input_row,
            text=self.t("btn_browse"),
            font=theme.get_font(13, "bold"),
            height=44,
            corner_radius=12,
            fg_color=theme.ACCENT_LIME,
            hover_color=theme.ACCENT_LIME_HOVER,
            text_color="#121214",
            command=self._browse_folder
        )
        self.btn_browse.pack(side="right")

        if self.dnd_available:
            try:
                self.entry_folder.drop_target_register(DND_FILES)
                self.entry_folder.dnd_bind("<<Drop>>", self._on_dnd_drop)
                card.drop_target_register(DND_FILES)
                card.dnd_bind("<<Drop>>", self._on_dnd_drop)
            except Exception:
                pass

    def _build_inspect_card(self, parent):
        self.inspect_card = ctk.CTkFrame(
            parent,
            fg_color=theme.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=theme.BORDER_COLOR
        )
        self.inspect_card.pack(fill="x", pady=(0, 12), ipady=6)

        head_row = ctk.CTkFrame(self.inspect_card, fg_color="transparent")
        head_row.pack(fill="x", padx=20, pady=(12, 6))

        self.lbl_inspect_title = ctk.CTkLabel(
            head_row,
            text=self.t("quick_inspect_title"),
            font=theme.get_font(11, "bold"),
            text_color=theme.TEXT_MUTED
        )
        self.lbl_inspect_title.pack(side="left")

        self.lbl_inspect_status = ctk.CTkLabel(
            head_row,
            text="Belum ada folder dipilih",
            font=theme.get_font(11, "bold"),
            text_color=theme.TEXT_SECONDARY
        )
        self.lbl_inspect_status.pack(side="right")

        self.chips_frame = ctk.CTkFrame(self.inspect_card, fg_color="transparent")
        self.chips_frame.pack(fill="x", padx=16, pady=(4, 10))

        self.lbl_no_folder = ctk.CTkLabel(
            self.chips_frame,
            text="Pilih folder di atas untuk melihat ringkasan jenis file.",
            font=theme.get_font(12, "normal"),
            text_color=theme.TEXT_MUTED
        )
        self.lbl_no_folder.pack(anchor="w", padx=4, pady=4)

    def _build_progress_capsule(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=theme.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=theme.BORDER_COLOR
        )
        card.pack(fill="x", pady=(0, 12), ipady=6)

        head_row = ctk.CTkFrame(card, fg_color="transparent")
        head_row.pack(fill="x", padx=20, pady=(12, 6))

        self.lbl_status = ctk.CTkLabel(
            head_row,
            text=self.t("status_ready"),
            font=theme.get_font(12, "bold"),
            text_color=theme.TEXT_PRIMARY
        )
        self.lbl_status.pack(side="left")

        self.lbl_percent = ctk.CTkLabel(
            head_row,
            text="0%",
            font=theme.get_font(14, "bold"),
            text_color=theme.ACCENT_LIME
        )
        self.lbl_percent.pack(side="right")

        self.progress_bar = theme.GlowingProgressBar(card, height=22, corner_radius=11)
        self.progress_bar.pack(fill="x", padx=20, pady=(4, 12))
        self.progress_bar.set_progress(0.0)

    def _build_metric_grid(self, parent):
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 12))
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat_cards")

        self.card_total = theme.MetricCard(
            grid,
            title="TOTAL FILE",
            value="0",
            subtitle="File terdeteksi",
            icon_text="📂"
        )
        self.card_total.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.card_savings = theme.MetricCard(
            grid,
            title="DUPLIKAT BISA DIHEMAT",
            value="0 MB",
            subtitle="0 file duplikat",
            icon_text="⚡",
            is_highlight=True
        )
        self.card_savings.grid(row=0, column=1, padx=3, sticky="ew")

        self.card_neat = theme.MetricCard(
            grid,
            title=self.t("card_clutter_title"),
            value="--",
            subtitle="Pilih folder dulu",
            icon_text="✨"
        )
        self.card_neat.grid(row=0, column=2, padx=(6, 0), sticky="ew")

    def _build_stabilo_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=theme.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=theme.BORDER_COLOR
        )
        card.pack(fill="x", pady=(0, 12), ipady=6)

        head_row = ctk.CTkFrame(card, fg_color="transparent")
        head_row.pack(fill="x", padx=20, pady=(12, 4))

        self.lbl_stabilo_title = ctk.CTkLabel(
            head_row,
            text=self.t("stabilo_title"),
            font=theme.get_font(11, "bold"),
            text_color=theme.STABILO_YELLOW
        )
        self.lbl_stabilo_title.pack(side="left")

        btn_add = ctk.CTkButton(
            head_row,
            text=self.t("btn_add_stabilo"),
            font=theme.get_font(11, "bold"),
            height=26,
            corner_radius=8,
            fg_color=theme.STABILO_BG,
            border_width=1,
            border_color=theme.STABILO_YELLOW,
            text_color=theme.STABILO_YELLOW,
            hover_color="#3D3507",
            command=self._dialog_add_stabilo
        )
        btn_add.pack(side="right")

        self.lbl_stabilo_hint = ctk.CTkLabel(
            card,
            text=self.t("stabilo_hint"),
            font=theme.get_font(11, "normal"),
            text_color=theme.TEXT_MUTED
        )
        self.lbl_stabilo_hint.pack(anchor="w", padx=20, pady=(0, 8))

        self.stabilo_container = ctk.CTkFrame(card, fg_color="transparent")
        self.stabilo_container.pack(fill="x", padx=16, pady=(0, 8))
        self._render_stabilo_chips()

    def _render_stabilo_chips(self):
        for w in self.stabilo_container.winfo_children():
            w.destroy()

        if not self.stabilo_folders:
            lbl = ctk.CTkLabel(
                self.stabilo_container,
                text="Belum ada folder yang distabilo. Tambahkan folder penting agar aman 100%.",
                font=theme.get_font(11, "normal"),
                text_color=theme.TEXT_MUTED
            )
            lbl.pack(anchor="w", padx=4, pady=2)
            return

        row = ctk.CTkFrame(self.stabilo_container, fg_color="transparent")
        row.pack(fill="x")
        for f_name in sorted(self.stabilo_folders):
            chip = theme.StabiloChip(
                row,
                folder_name=f_name,
                on_remove=lambda name=f_name: self._remove_stabilo(name)
            )
            chip.pack(side="left", padx=4, pady=3)

    def _dialog_add_stabilo(self):
        subfolders = self._get_target_subfolders()
        dlg = StabiloDialog(self, subfolders=subfolders)
        self.wait_window(dlg)
        if dlg.result:
            self.stabilo_folders.add(dlg.result)
            self._render_stabilo_chips()
            self._save_settings()

    def _remove_stabilo(self, name):
        if name in self.stabilo_folders:
            self.stabilo_folders.remove(name)
            self._render_stabilo_chips()
            self._save_settings()

    def _build_rules_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=theme.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=theme.BORDER_COLOR
        )
        card.pack(fill="x", pady=(0, 12), ipady=6)

        head_row = ctk.CTkFrame(card, fg_color="transparent")
        head_row.pack(fill="x", padx=20, pady=(12, 4))

        self.lbl_rules_title = ctk.CTkLabel(
            head_row,
            text=self.t("custom_rules_title"),
            font=theme.get_font(11, "bold"),
            text_color=theme.ACCENT_LIME
        )
        self.lbl_rules_title.pack(side="left")

        btn_add = ctk.CTkButton(
            head_row,
            text=self.t("btn_add_rule"),
            font=theme.get_font(11, "bold"),
            height=26,
            corner_radius=8,
            fg_color=theme.ACCENT_MUTED_LIME,
            border_width=1,
            border_color=theme.ACCENT_LIME,
            text_color=theme.ACCENT_LIME,
            hover_color="#243006",
            command=self._dialog_add_rule
        )
        btn_add.pack(side="right")

        self.lbl_rules_hint = ctk.CTkLabel(
            card,
            text=self.t("custom_rules_hint"),
            font=theme.get_font(11, "normal"),
            text_color=theme.TEXT_MUTED
        )
        self.lbl_rules_hint.pack(anchor="w", padx=20, pady=(0, 8))

        self.rules_container = ctk.CTkFrame(card, fg_color="transparent")
        self.rules_container.pack(fill="x", padx=16, pady=(0, 8))
        self._render_custom_rules()

    def _render_custom_rules(self):
        for w in self.rules_container.winfo_children():
            w.destroy()

        if not self.custom_rules:
            lbl = ctk.CTkLabel(
                self.rules_container,
                text="Belum ada aturan kata kunci khusus.",
                font=theme.get_font(11, "normal"),
                text_color=theme.TEXT_MUTED
            )
            lbl.pack(anchor="w", padx=4, pady=2)
            return

        for idx, rule in enumerate(self.custom_rules):
            r_box = ctk.CTkFrame(
                self.rules_container,
                fg_color="#1D1D22",
                corner_radius=10,
                border_width=1,
                border_color="#2A2A32"
            )
            r_box.pack(fill="x", pady=3)

            lbl_kw = ctk.CTkLabel(
                r_box,
                text=f"🔍 Kata kunci: '{rule['keyword']}'",
                font=theme.get_font(11, "bold"),
                text_color=theme.ACCENT_LIME
            )
            lbl_kw.pack(side="left", padx=12, pady=6)

            lbl_target = ctk.CTkLabel(
                r_box,
                text=f"➔ Folder tujuan: {rule['folder']}",
                font=theme.get_font(11, "normal"),
                text_color=theme.TEXT_PRIMARY
            )
            lbl_target.pack(side="left", padx=10, pady=6)

            btn_del = ctk.CTkButton(
                r_box,
                text="✕",
                width=20,
                height=20,
                corner_radius=10,
                fg_color="transparent",
                hover_color="#3A1D1D",
                text_color=theme.DANGER,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda i=idx: self._remove_rule(i)
            )
            btn_del.pack(side="right", padx=8, pady=6)

    def _dialog_add_rule(self):
        subfolders = self._get_target_subfolders()
        dlg = CustomRuleDialog(self, subfolders=subfolders)
        self.wait_window(dlg)
        if dlg.result:
            self.custom_rules.append(dlg.result)
            self._render_custom_rules()
            self._save_settings()

    def _remove_rule(self, idx):
        if 0 <= idx < len(self.custom_rules):
            self.custom_rules.pop(idx)
            self._render_custom_rules()
            self._save_settings()

    def _build_options_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=theme.CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=theme.BORDER_COLOR
        )
        card.pack(fill="x", pady=(0, 12), ipady=6)

        self.lbl_opts_title = ctk.CTkLabel(
            card,
            text=self.t("options_title"),
            font=theme.get_font(11, "bold"),
            text_color=theme.TEXT_MUTED
        )
        self.lbl_opts_title.pack(anchor="w", padx=20, pady=(12, 10))

        opts_grid = ctk.CTkFrame(card, fg_color="transparent")
        opts_grid.pack(fill="x", padx=16, pady=(0, 10))
        opts_grid.grid_columnconfigure((0, 1), weight=1)

        self.chk_list = []
        switches = [
            ("opt_type", self.sw_type, 0, 0),
            ("opt_exif", self.sw_exif, 0, 1),
            ("opt_dup", self.sw_dup, 1, 0),
            ("opt_recycle", self.sw_recycle, 1, 1),
            ("opt_sub", self.sw_sub, 2, 0),
            ("opt_clean", self.sw_clean, 2, 1),
            ("opt_junk", self.sw_junk, 3, 0),
            ("opt_context", self.sw_context, 3, 1),
        ]

        for key, var, r, c in switches:
            chk = ctk.CTkCheckBox(
                opts_grid,
                text=self.t(key),
                variable=var,
                font=theme.get_font(12, "normal"),
                text_color=theme.TEXT_PRIMARY,
                fg_color=theme.ACCENT_LIME,
                checkmark_color="#121214",
                hover_color=theme.ACCENT_LIME_HOVER,
                border_color=theme.BORDER_LIGHT,
                corner_radius=6,
                command=self._on_option_changed
            )
            chk.grid(row=r, column=c, padx=10, pady=6, sticky="w")
            self.chk_list.append((key, chk))

        date_frame = ctk.CTkFrame(card, fg_color="transparent")
        date_frame.pack(fill="x", padx=26, pady=(6, 12))

        self.lbl_date = ctk.CTkLabel(
            date_frame,
            text=f"{self.t('opt_date')}:",
            font=theme.get_font(12, "bold"),
            text_color=theme.TEXT_SECONDARY
        )
        self.lbl_date.pack(side="left", padx=(0, 10))

        date_choices = ["none", "year", "month"]
        for opt in date_choices:
            rb = ctk.CTkRadioButton(
                date_frame,
                text=opt.capitalize(),
                variable=self.date_mode,
                value=opt,
                font=theme.get_font(12, "normal"),
                text_color=theme.TEXT_PRIMARY,
                fg_color=theme.ACCENT_LIME,
                border_color=theme.BORDER_LIGHT
            )
            rb.pack(side="left", padx=10)

    def _build_actions_and_log(self, parent):
        actions_box = ctk.CTkFrame(parent, fg_color="transparent")
        actions_box.pack(fill="x", pady=(0, 12))

        self.btn_preview = ctk.CTkButton(
            actions_box,
            text=self.t("btn_preview"),
            font=theme.get_font(13, "bold"),
            height=46,
            corner_radius=12,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.BORDER_LIGHT,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
            command=self._on_click_preview
        )
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_run = ctk.CTkButton(
            actions_box,
            text=self.t("btn_run"),
            font=theme.get_font(14, "bold"),
            height=46,
            corner_radius=12,
            fg_color=theme.ACCENT_LIME,
            hover_color=theme.ACCENT_LIME_HOVER,
            text_color="#121214",
            command=self._on_click_run
        )
        self.btn_run.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_undo = ctk.CTkButton(
            actions_box,
            text=self.t("btn_undo"),
            font=theme.get_font(13, "bold"),
            height=46,
            corner_radius=12,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.BORDER_LIGHT,
            hover_color=theme.CARD_HOVER,
            text_color=theme.TEXT_SECONDARY,
            command=self._on_click_undo
        )
        self.btn_undo.pack(side="right", padx=(6, 0))

        self.log_box = ctk.CTkTextbox(
            parent,
            height=160,
            corner_radius=16,
            fg_color=theme.CARD_BG,
            border_width=1,
            border_color=theme.BORDER_COLOR,
            text_color=theme.TEXT_PRIMARY,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.log_box.pack(fill="both", expand=True, pady=(0, 8))
        self._log_append("✦ Rapihin v2.0 Siap - Pilih folder untuk melihat pratinjau instan.")

    # --- Quick Inspect Initial Folder State ---

    def _quick_inspect_folder(self, folder_path):
        if not folder_path.exists() or not folder_path.is_dir():
            return

        for w in self.chips_frame.winfo_children():
            w.destroy()

        cat_counts = defaultdict(int)
        cat_sizes = defaultdict(int)
        ext_counter = Counter()
        total_files = 0

        try:
            for item in folder_path.iterdir():
                if item.is_file() and item.name not in engine.SKIP_FILES and not item.name.startswith("."):
                    total_files += 1
                    ext = item.suffix.lower().lstrip(".")
                    cat = engine.get_category(ext)
                    cat_counts[cat] += 1
                    try:
                        sz = item.stat().st_size
                        cat_sizes[cat] += sz
                    except OSError:
                        pass
                    if ext:
                        ext_counter[ext] += 1
        except Exception as e:
            self._log_append(f"Gagal membaca folder: {e}")
            return

        self.card_total.update_data(value=str(total_files))

        if total_files == 0:
            self.lbl_inspect_status.configure(text="Folder Kosong", text_color=theme.TEXT_MUTED)
            self.card_neat.update_data(value="100%", subtitle=self.t("neat_perfect"), text_color=theme.SUCCESS)
            lbl = ctk.CTkLabel(
                self.chips_frame,
                text="Tidak ada file yang perlu dirapikan di dalam folder ini.",
                font=theme.get_font(12, "normal"),
                text_color=theme.TEXT_MUTED
            )
            lbl.pack(anchor="w", padx=4, pady=4)
            return

        types_count = len(cat_counts)
        if types_count >= 5:
            tidiness_score = max(8, 30 - types_count * 3)
            sub_text = self.t("neat_messy")
            color = theme.DANGER
        elif types_count >= 2:
            tidiness_score = max(20, 50 - types_count * 6)
            sub_text = self.t("neat_messy")
            color = theme.WARNING
        else:
            tidiness_score = 65
            sub_text = "Sebagian rapi"
            color = theme.ACCENT_LIME

        self.card_neat.update_data(
            value=f"{tidiness_score}%",
            subtitle=sub_text,
            text_color=color
        )

        self.lbl_inspect_status.configure(
            text=self.t("inspect_messy").format(count=types_count),
            text_color=theme.WARNING
        )

        row_frame = ctk.CTkFrame(self.chips_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
            cat_name = engine.CAT_NAMES[self.lang].get(cat, cat.capitalize())
            icon = CAT_ICONS.get(cat, "📁")
            size_str = engine.fmt_size(cat_sizes[cat])
            chip = theme.CategoryChip(row_frame, icon=icon, name=cat_name, count=count, size_str=size_str)
            chip.pack(side="left", padx=4, pady=4)

        top_exts = ", ".join([f".{ext} ({cnt})" for ext, cnt in ext_counter.most_common(4)])
        self._log_append(f"Folder: {folder_path.name} | Total: {total_files} file | Format: {top_exts}")

    # --- Handlers ---

    def _log_append(self, text, clear=False):
        if clear:
            self.log_box.delete("1.0", "end")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def _browse_folder(self):
        sel = filedialog.askdirectory(initialdir=self.folder_var.get() or os.path.expanduser("~"))
        if sel:
            p = Path(sel)
            self.folder_var.set(str(p))
            self._quick_inspect_folder(p)

    def _on_dnd_drop(self, event):
        val = event.data.strip("{}")
        if os.path.isdir(val):
            p = Path(val)
            self.folder_var.set(str(p))
            self._quick_inspect_folder(p)

    def _toggle_language(self):
        self.lang = "en" if self.lang == "id" else "id"
        self.btn_lang.configure(text=self.lang.upper())
        self.lbl_target_title.configure(text=self.t("folder_card"))
        self.entry_folder.configure(placeholder_text=self.t("placeholder"))
        self.btn_browse.configure(text=self.t("btn_browse"))
        self.lbl_inspect_title.configure(text=self.t("quick_inspect_title"))
        self.lbl_stabilo_title.configure(text=self.t("stabilo_title"))
        self.lbl_stabilo_hint.configure(text=self.t("stabilo_hint"))
        self.lbl_rules_title.configure(text=self.t("custom_rules_title"))
        self.lbl_rules_hint.configure(text=self.t("custom_rules_hint"))
        self.lbl_opts_title.configure(text=self.t("options_title"))
        self.lbl_date.configure(text=f"{self.t('opt_date')}:")
        self.btn_preview.configure(text=self.t("btn_preview"))
        self.btn_run.configure(text=self.t("btn_run"))
        self.btn_undo.configure(text=self.t("btn_undo"))
        self.lbl_status.configure(text=self.t("status_ready"))

        for key, chk in self.chk_list:
            chk.configure(text=self.t(key))

        if self.folder_var.get() and Path(self.folder_var.get()).is_dir():
            self._quick_inspect_folder(Path(self.folder_var.get()))

    def _on_option_changed(self):
        if self.sw_context.get():
            ok, msg = engine.set_context_menu(enable=True)
            if not ok:
                messagebox.showwarning("Context Menu", msg)
                self.sw_context.set(False)
        else:
            engine.set_context_menu(enable=False)

    def _check_for_updates_background(self):
        def worker():
            has_update, latest_ver, url, notes = engine.check_github_update()
            if has_update:
                self.update_info = {"ver": latest_ver, "url": url}
                self.after(0, self._show_update_banner, latest_ver)
        threading.Thread(target=worker, daemon=True).start()

    def _show_update_banner(self, ver):
        self.lbl_update.configure(text=self.t("update_available").format(ver=ver))
        self.update_card.pack(fill="x", pady=(0, 12), before=self.entry_folder.master.master)

    def _open_update_link(self):
        if self.update_info and self.update_info.get("url"):
            webbrowser.open(self.update_info["url"])

    # --- Scanning & Preview Logic ---

    def _on_click_preview(self):
        folder = Path(self.folder_var.get().strip())
        if not folder.exists() or not folder.is_dir():
            messagebox.showwarning("Error", "Pilih folder yang valid terlebih dahulu!")
            return
        if engine.is_sensitive_folder(folder):
            messagebox.showerror("Error", "Folder ini adalah folder sistem sensitif. Pilih folder lain demi keamanan.")
            return

        self._set_ui_busy(True)
        self.lbl_status.configure(text=self.t("status_scanning"))
        self.progress_bar.set_progress(0.2)
        self.lbl_percent.configure(text="20%")
        self._log_append(f"\n[MEMINDAI LENGKAP] {folder} ...", clear=True)

        def worker():
            plan = self._calculate_plan(folder)
            self.after(0, lambda: self._apply_preview_results(plan))

        threading.Thread(target=worker, daemon=True).start()

    def _calculate_plan(self, root_dir):
        recursive = self.sw_sub.get()
        all_files = []
        stabilo_set = {s.lower() for s in self.stabilo_folders}

        if not recursive:
            for item in root_dir.iterdir():
                if item.is_file() and item.name not in engine.SKIP_FILES and not item.name.startswith("."):
                    all_files.append(item)
        else:
            for dp, dns, fns in os.walk(root_dir):
                dns[:] = [
                    d for d in dns
                    if not d.startswith(".")
                    and d not in engine.SKIP_DIRS
                    and d.lower() not in stabilo_set
                ]
                for fn in fns:
                    if fn not in engine.SKIP_FILES and not fn.startswith("."):
                        all_files.append(Path(dp) / fn)

        duplicates = {}
        saved_bytes = 0
        if self.sw_dup.get() and all_files:
            duplicates, saved_bytes = engine.find_duplicates_tiered(all_files)

        junk_report = {"zero_byte": [], "broken_lnk": [], "old_installers": []}
        if self.sw_junk.get() and all_files:
            junk_report = engine.detect_junk_and_old_installers(all_files)

        moves = []
        dup_moves = []
        custom_routed_moves = []
        date_mode = self.date_mode.get()
        use_exif = self.sw_exif.get()
        use_type = self.sw_type.get()

        dup_folder = root_dir / engine.CAT_NAMES[self.lang].get("other", "_Duplikat")
        dup_paths_set = set()
        for original, dup_list in duplicates.items():
            for d in dup_list:
                dup_paths_set.add(d)
                dup_moves.append((d, dup_folder / d.name))

        for f in all_files:
            if f in dup_paths_set:
                continue

            matched_folder = engine.match_custom_rules(f, self.custom_rules)
            if matched_folder:
                target_dir = root_dir / matched_folder
                target_path = target_dir / f.name
                if target_path != f:
                    moves.append((f, target_path))
                    custom_routed_moves.append((f, target_path))
                continue

            target_dir = root_dir
            cat = engine.get_category(f.suffix)

            if use_type:
                target_dir = target_dir / engine.CAT_NAMES[self.lang].get(cat, cat.capitalize())

            dt = None
            if cat == "images" and use_exif:
                dt = engine.get_photo_date(f)
            elif cat == "audio" and use_exif:
                artist, album = engine.get_audio_info(f)
                if artist:
                    target_dir = target_dir / artist

            if dt is None:
                st = f.stat()
                dt = datetime.fromtimestamp(st.st_mtime)

            if date_mode == "year":
                target_dir = target_dir / f"{dt:%Y}"
            elif date_mode == "month":
                target_dir = target_dir / f"{dt:%Y-%m}"

            target_path = target_dir / f.name
            if target_path != f:
                moves.append((f, target_path))

        return {
            "root": root_dir,
            "all_files_count": len(all_files),
            "moves": moves,
            "custom_routed": custom_routed_moves,
            "duplicates": duplicates,
            "dup_moves": dup_moves,
            "saved_bytes": saved_bytes,
            "junk": junk_report
        }

    def _apply_preview_results(self, plan):
        self._set_ui_busy(False)
        self.current_preview_plan = plan
        self.progress_bar.set_progress(1.0)
        self.lbl_percent.configure(text="100%")
        self.lbl_status.configure(text="Pratinjau siap ditinjau.")

        self.card_total.update_data(value=str(plan["all_files_count"]))
        self.card_savings.update_data(
            value=engine.fmt_size(plan["saved_bytes"]),
            subtitle=f"{len(plan['dup_moves'])} duplikat"
        )

        self._log_append("=" * 55)
        self._log_append(f"TOTAL FILE DITEMUKAN   : {plan['all_files_count']}")
        self._log_append(f"AKAN DIRAPIKAN         : {len(plan['moves'])} file")
        if plan["custom_routed"]:
            self._log_append(f"ATURAN KATA KUNCI (SAFE): {len(plan['custom_routed'])} file masuk folder khusus")
        self._log_append(f"DUPLIKAT DIHEMAT       : {len(plan['dup_moves'])} file ({engine.fmt_size(plan['saved_bytes'])})")

        old_inst = plan["junk"]["old_installers"]
        if old_inst:
            self._log_append(f"INSTALLER LAMA DITEMUKAN: {len(old_inst)} file")

        self._log_append("=" * 55)
        for src, dst in plan["custom_routed"][:5]:
            self._log_append(f"  ⭐ [KHUSUS] {src.name}  =>  {dst.parent.relative_to(plan['root'])}\\")

        for src, dst in plan["moves"][:6]:
            if (src, dst) not in plan["custom_routed"]:
                self._log_append(f"  → {src.name}  =>  {dst.parent.relative_to(plan['root'])}\\")
        if len(plan["moves"]) > 10:
            self._log_append(f"  ... dan {len(plan['moves']) - 10} file lainnya.")

        self._log_append("\nSiap? Klik 'Rapihin Sekarang' untuk menata file!")

    # --- Execution & Undo ---

    def _on_click_run(self):
        if not self.current_preview_plan or not self.current_preview_plan.get("root"):
            self._on_click_preview()
            return

        plan = self.current_preview_plan
        total_actions = len(plan["moves"]) + len(plan["dup_moves"])
        if total_actions == 0:
            messagebox.showinfo("Rapihin", "Semua file di folder ini sudah rapi!")
            return

        confirm = messagebox.askyesno(
            "Konfirmasi",
            f"Rapihkan {len(plan['moves'])} file dan tangani {len(plan['dup_moves'])} duplikat?\n"
            f"(Bisa di-undo kapan saja lewat tombol Undo)"
        )
        if not confirm:
            return

        self._set_ui_busy(True)
        self.lbl_status.configure(text=self.t("status_running"))
        self.progress_bar.set_progress(0.1)

        def worker():
            executed_moves = []
            root = plan["root"]
            use_recycle = self.sw_recycle.get()

            for dup_src, dup_target in plan["dup_moves"]:
                if use_recycle:
                    ok, _ = engine.safe_recycle(dup_src)
                    if ok:
                        continue
                try:
                    dup_target.parent.mkdir(parents=True, exist_ok=True)
                    final_dst = engine.get_unique_target(dup_target)
                    shutil.move(str(dup_src), str(final_dst))
                    executed_moves.append({"src": str(dup_src), "dst": str(final_dst)})
                except Exception:
                    pass

            moved_count = 0
            for src, dst in plan["moves"]:
                try:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    final_dst = engine.get_unique_target(dst)
                    shutil.move(str(src), str(final_dst))
                    executed_moves.append({"src": str(src), "dst": str(final_dst)})
                    moved_count += 1
                except Exception:
                    pass

            if executed_moves:
                undo_path = root / engine.UNDO_FILE
                try:
                    with open(undo_path, "w", encoding="utf-8") as f:
                        json.dump(executed_moves, f, indent=2)
                except Exception:
                    pass

            cleaned_dirs = 0
            if self.sw_clean.get():
                stabilo_set = {s.lower() for s in self.stabilo_folders}
                for dp, dns, fns in os.walk(root, topdown=False):
                    p = Path(dp)
                    if p != root and not any(p.iterdir()) and p.name.lower() not in stabilo_set:
                        try:
                            p.rmdir()
                            cleaned_dirs += 1
                        except OSError:
                            pass

            self.after(0, lambda: self._on_run_complete(moved_count, len(plan["dup_moves"]), cleaned_dirs))

        threading.Thread(target=worker, daemon=True).start()

    def _on_run_complete(self, moved, dups, cleaned):
        self._set_ui_busy(False)
        self.progress_bar.set_progress(1.0)
        self.lbl_percent.configure(text="100%")
        self.card_neat.update_data(value="100%", subtitle="Selesai dirapikan!", text_color=theme.SUCCESS)
        self.lbl_status.configure(text="✓ Berhasil dirapikan!")

        self._log_append("\n[SELESAI EKSEKUSI]")
        self._log_append(f"✓ {moved} file berhasil ditata rapi.")
        if dups > 0:
            self._log_append(f"✓ {dups} duplikat dipindahkan.")
        if cleaned > 0:
            self._log_append(f"✓ {cleaned} folder kosong dibersihkan.")
        self._log_append("Kapan saja merasa kurang cocok, klik tombol Undo.")

        folder = Path(self.folder_var.get().strip())
        if folder.exists():
            self._quick_inspect_folder(folder)

        messagebox.showinfo("Sukses", f"Berhasil merapikan {moved} file!")

    def _on_click_undo(self):
        folder = Path(self.folder_var.get().strip())
        undo_file = folder / engine.UNDO_FILE
        if not undo_file.exists():
            messagebox.showinfo("Undo", "Tidak ditemukan riwayat rapihin di folder ini.")
            return

        confirm = messagebox.askyesno("Undo", "Kembalikan semua file ke lokasi asalnya?")
        if not confirm:
            return

        try:
            with open(undo_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            restored = 0
            for item in reversed(records):
                src = Path(item["src"])
                dst = Path(item["dst"])
                if dst.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dst), str(src))
                    restored += 1

            undo_file.unlink(missing_ok=True)
            self._log_append(f"\n↩ Undo berhasil: {restored} file dikembalikan ke tempat semula.")
            messagebox.showinfo("Undo", f"{restored} file berhasil dikembalikan.")
            self.lbl_status.configure(text="Riwayat telah di-undo.")
            self._quick_inspect_folder(folder)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal melakukan undo: {e}")

    def _set_ui_busy(self, busy):
        self.worker_busy = busy
        state = "disabled" if busy else "normal"
        self.btn_preview.configure(state=state)
        self.btn_run.configure(state=state)
        self.btn_undo.configure(state=state)


def main():
    app = RapihinApp()
    app.mainloop()


if __name__ == "__main__":
    main()
