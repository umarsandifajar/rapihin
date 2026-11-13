import ctypes
import hashlib
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

try:  # drag & drop itu opsional, kalau gagal aplikasi tetap jalan
    from tkinterdnd2 import DND_FILES, TkinterDnD
    BASES = (ctk.CTk, TkinterDnD.DnDWrapper)
except Exception:
    TkinterDnD = None
    DND_FILES = None
    BASES = (ctk.CTk,)

APP_NAME = "rapihin"
APP_VERSION = "1.1.0"
DONATE_URL = "https://umarsandifajar.github.io/bio-sandiana/"

KATEGORI = {
    "images": {"jpg", "jpeg", "png", "webp", "gif", "bmp", "svg", "heic", "tiff", "ico"},
    "video": {"mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v"},
    "docs": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "odt", "rtf"},
    "audio": {"mp3", "wav", "flac", "m4a", "aac", "ogg"},
    "archives": {"zip", "rar", "7z", "tar", "gz"},
    "installers": {"exe", "msi"},
}
CAT_NAMES = {
    "id": {"images": "Gambar", "video": "Video", "docs": "Dokumen", "audio": "Audio",
           "archives": "Arsip", "installers": "Installer", "other": "Lainnya"},
    "en": {"images": "Images", "video": "Videos", "docs": "Documents", "audio": "Audio",
           "archives": "Archives", "installers": "Installers", "other": "Others"},
}
DUP_NAMES = {"id": "_Duplikat", "en": "_Duplicates"}
DATE_KEYS = ["none", "year", "month"]
SRC_KEYS = ["mtime", "ctime"]

UNDO_FILE = ".rapihin_undo.json"
SKIP_FILES = {"desktop.ini", "thumbs.db", UNDO_FILE}
SKIP_DIRS = {"_Duplikat", "_Duplicates", "node_modules", "$RECYCLE.BIN", "System Volume Information"}

# Palet soft dark
BG = "#13141A"
CARD = "#1B1D26"
CARD2 = "#242736"
BORDER = "#2B2F40"
TEXT = "#E6E8F0"
MUTED = "#8B90A5"
ACCENT = "#6F75E8"
ACCENT_HOVER = "#5E64D6"
SOFT_HOVER = "#2E3245"

TR = {
    "id": {
        "subtitle": "Rapihin folder berantakan: pilah per jenis & tanggal, buang duplikat.",
        "folder": "Folder",
        "placeholder": "Seret & lepas folder ke sini, atau klik Pilih folder",
        "pick": "Pilih folder",
        "options": "Opsi",
        "sw_type": "Pisahin per jenis file",
        "sw_sub": "Ikut proses subfolder",
        "sw_dup": "Deteksi file duplikat",
        "sw_clean": "Bersihin folder kosong",
        "grp_date": "Kelompokkan tanggal",
        "src_date": "Sumber tanggal",
        "d_none": "Tanpa tanggal", "d_year": "Per tahun", "d_month": "Per bulan",
        "s_mod": "Tanggal diubah", "s_cre": "Tanggal dibuat",
        "btn_preview": "Preview", "btn_run": "Rapihin sekarang", "btn_undo": "Undo",
        "intro": "Pilih folder, lalu klik Preview buat lihat hasilnya dulu sebelum ada yang dipindah.",
        "warn_invalid": "Pilih folder yang valid dulu ya.",
        "warn_sensitive": "Folder ini terlalu sensitif (root drive / folder sistem). Pilih folder lain.",
        "no_undo": "Nggak ada riwayat yang bisa di-undo di folder ini.",
        "scan": "Memindai file...",
        "found": "Ketemu {n} file.",
        "check_dup": "Ngecek duplikat di {n} file kandidat...",
        "preview_head": "\nPREVIEW: {m} file akan dipindah, {d} duplikat.\n",
        "nothing": "Nggak ada yang perlu dirapihin dengan opsi ini.",
        "more_folders": "  ... dan {n} folder lain",
        "dup_line": "\nDuplikat: {n} file ({size} bisa dihemat), dipindah ke {dir}\\",
        "more_items": "  ... dan {n} lainnya",
        "preview_hint": "\nBelum ada yang dipindah. Klik 'Rapihin sekarang' kalau udah oke.",
        "nothing_info": "Nggak ada file yang perlu dirapihin.",
        "confirm_move": "Pindahin {n} file",
        "confirm_dups": " dan {d} file duplikat (ke folder {dir})",
        "confirm_tail": "?\n\nBisa dibalikin lewat tombol Undo.",
        "starting": "Mulai merapikan...\n",
        "fail": "Gagal: {name} ({err})",
        "done_line": "Selesai! {n} file dipindah, {g} gagal.",
        "clean_n": "{n} folder kosong dibersihin.",
        "undo_hint": "Hasilnya kurang pas? Klik Undo buat balikin semua.",
        "undoing": "Mengembalikan file...\n",
        "undone": "{n} file dikembalikan ke tempat semula.",
        "err": "Error: {e}",
        "sum_title": "\nRingkasan",
        "sum_total": "  Total dipindah : {n} file ({size})",
        "sum_dups": "  Duplikat       : {n} file ({size} dihemat)",
        "status_done": "✓ {n} file dirapihin ({size})",
        "status_dups": "  ·  {d} duplikat ({size})",
        "status_undo": "↩ {n} file dikembalikan",
    },
    "en": {
        "subtitle": "Tidy up messy folders: sort by type & date, remove duplicates.",
        "folder": "Folder",
        "placeholder": "Drag & drop a folder here, or click Choose folder",
        "pick": "Choose folder",
        "options": "Options",
        "sw_type": "Sort by file type",
        "sw_sub": "Include subfolders",
        "sw_dup": "Detect duplicate files",
        "sw_clean": "Remove empty folders",
        "grp_date": "Group by date",
        "src_date": "Date source",
        "d_none": "No date", "d_year": "By year", "d_month": "By month",
        "s_mod": "Date modified", "s_cre": "Date created",
        "btn_preview": "Preview", "btn_run": "Organize now", "btn_undo": "Undo",
        "intro": "Choose a folder, then click Preview to see the result before anything is moved.",
        "warn_invalid": "Please choose a valid folder first.",
        "warn_sensitive": "This folder is too sensitive (drive root / system folder). Choose another one.",
        "no_undo": "There is nothing to undo in this folder.",
        "scan": "Scanning files...",
        "found": "Found {n} files.",
        "check_dup": "Checking {n} candidate files for duplicates...",
        "preview_head": "\nPREVIEW: {m} files will be moved, {d} duplicates.\n",
        "nothing": "Nothing to organize with these options.",
        "more_folders": "  ... and {n} more folders",
        "dup_line": "\nDuplicates: {n} files ({size} can be saved), moved to {dir}\\",
        "more_items": "  ... and {n} more",
        "preview_hint": "\nNothing has been moved yet. Click 'Organize now' when you're happy with it.",
        "nothing_info": "There are no files to organize.",
        "confirm_move": "Move {n} files",
        "confirm_dups": " and {d} duplicate files (to the {dir} folder)",
        "confirm_tail": "?\n\nYou can restore them with the Undo button.",
        "starting": "Organizing...\n",
        "fail": "Failed: {name} ({err})",
        "done_line": "Done! {n} files moved, {g} failed.",
        "clean_n": "{n} empty folders removed.",
        "undo_hint": "Not what you wanted? Click Undo to restore everything.",
        "undoing": "Restoring files...\n",
        "undone": "{n} files restored to their original place.",
        "err": "Error: {e}",
        "sum_title": "\nSummary",
        "sum_total": "  Total moved : {n} files ({size})",
        "sum_dups": "  Duplicates  : {n} files ({size} saved)",
        "status_done": "✓ {n} files organized ({size})",
        "status_dups": "  ·  {d} duplicates ({size})",
        "status_undo": "↩ {n} files restored",
    },
}


# ---------- Logika ----------
def resource(nama):
    base = getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parent
    return Path(base) / nama


def bahasa_sistem():
    try:
        return "id" if (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0xFF) == 0x21 else "en"
    except Exception:
        return "en"


def settings_path():
    return Path(os.environ.get("APPDATA") or Path.home()) / APP_NAME / "settings.json"


def cari_kategori(ext):
    for key, exts in KATEGORI.items():
        if ext in exts:
            return key
    return "other"


def target_unik(path):
    if not path.exists():
        return path
    i = 1
    while True:
        baru = path.with_name(f"{path.stem}_{i}{path.suffix}")
        if not baru.exists():
            return baru
        i += 1


def fmt_size(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def hash_file(p):
    h = hashlib.blake2b(digest_size=16)
    with open(p, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def nama_ok(nama):
    return not nama.startswith(".") and nama.lower() not in SKIP_FILES


def scan(root, rekursif):
    hasil = []
    if not rekursif:
        for f in root.iterdir():
            if f.is_file() and nama_ok(f.name):
                hasil.append(f)
        return hasil
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not d.startswith(".") and d not in SKIP_DIRS]
        for fn in fns:
            if nama_ok(fn):
                hasil.append(Path(dp) / fn)
    return hasil


def tujuan_dir(f, root, o):
    t = root
    if o["type"]:
        t = t / CAT_NAMES[o["lang"]][cari_kategori(f.suffix.lstrip(".").lower())]
    if o["date"] != "none":
        st = f.stat()
        ts = st.st_mtime if o["src"] == "mtime" else st.st_ctime
        d = datetime.fromtimestamp(ts)
        t = t / (f"{d:%Y}" if o["date"] == "year" else f"{d:%Y-%m}")
    return t


def folder_berbahaya(p):
    if p.parent == p:
        return True
    bahaya = {"windows", "program files", "program files (x86)", "programdata"}
    return any(x.lower() in bahaya for x in p.parts)


def bersihin_kosong(dirs, root):
    n = 0
    for d in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
        p = d
        while p != root and root in p.parents:
            try:
                p.rmdir()
                n += 1
            except OSError:
                break
            p = p.parent
    return n


# ---------- Aplikasi ----------
class App(*BASES):
    def __init__(self):
        super().__init__()
        self.dnd_aktif = False
        if TkinterDnD is not None:
            try:
                self.TkdndVersion = TkinterDnD._require(self)
                self.dnd_aktif = True
            except Exception:
                self.dnd_aktif = False

        ctk.set_appearance_mode("dark")
        self.title(APP_NAME)
        self.geometry("860x860")
        self.minsize(780, 800)
        self.configure(fg_color=BG)
        self.after(250, self._pasang_ikon)

        cfg = self._muat_settings()
        self.lang = cfg.get("lang") or bahasa_sistem()
        self.date_key = cfg.get("date") if cfg.get("date") in DATE_KEYS else "month"
        self.src_key = cfg.get("src") if cfg.get("src") in SRC_KEYS else "mtime"

        self.q = queue.Queue()
        self.sibuk = False
        self.pending = None
        self.btns = []

        self.folder = ctk.StringVar(value=cfg.get("folder", ""))
        self.v_type = ctk.BooleanVar(value=cfg.get("type", True))
        self.v_sub = ctk.BooleanVar(value=cfg.get("sub", False))
        self.v_dup = ctk.BooleanVar(value=cfg.get("dup", False))
        self.v_clean = ctk.BooleanVar(value=cfg.get("clean", True))

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._tutup)
        if self.dnd_aktif:
            try:
                self.drop_target_register(DND_FILES)
                self.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                self.dnd_aktif = False
        self.after(60, self._poll)

    # ----- Pengaturan -----
    def _muat_settings(self):
        try:
            return json.loads(settings_path().read_text(encoding="utf-8"))
        except Exception:
            return {}

    def simpan_settings(self):
        data = {
            "folder": self.folder.get(), "lang": self.lang, "date": self.date_key, "src": self.src_key,
            "type": self.v_type.get(), "sub": self.v_sub.get(), "dup": self.v_dup.get(),
            "clean": self.v_clean.get(),
        }
        try:
            p = settings_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _tutup(self):
        self.simpan_settings()
        self.destroy()

    def _pasang_ikon(self):
        try:
            self.iconbitmap(str(resource("rapihin.ico")))
        except Exception:
            pass

    def tr(self, key, **kw):
        s = TR[self.lang].get(key) or TR["id"][key]
        return s.format(**kw) if kw else s

    # ----- UI -----
    def _card(self, parent):
        return ctk.CTkFrame(parent, corner_radius=18, fg_color=CARD, border_width=1, border_color=BORDER)

    def _judul(self, parent, teks):
        return ctk.CTkLabel(parent, text=teks, font=("Segoe UI Semibold", 13), text_color=TEXT)

    def _switch(self, parent, teks, var):
        return ctk.CTkSwitch(
            parent, text=teks, variable=var, font=("Segoe UI", 13), text_color=TEXT,
            progress_color=ACCENT, fg_color="#363A4D", button_color="#E6E8F0", button_hover_color="#FFFFFF",
            command=self.simpan_settings,
        )

    def _segmen(self, parent, values, command):
        return ctk.CTkSegmentedButton(
            parent, values=values, command=command, height=34, corner_radius=12,
            fg_color=CARD2, unselected_color=CARD2, unselected_hover_color=SOFT_HOVER,
            selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
            text_color=TEXT, font=("Segoe UI", 12),
        )

    def _tombol(self, parent, teks, cmd, primer=False):
        b = ctk.CTkButton(
            parent, text=teks, command=cmd, height=44, corner_radius=14,
            font=("Segoe UI Semibold", 13), text_color=TEXT,
            fg_color=ACCENT if primer else CARD2,
            hover_color=ACCENT_HOVER if primer else SOFT_HOVER,
            border_width=0 if primer else 1, border_color=BORDER,
        )
        self.btns.append(b)
        return b

    def _build(self):
        self.btns = []
        self.wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap = self.wrap
        wrap.pack(fill="both", expand=True, padx=28, pady=(22, 14))

        # Header
        head = ctk.CTkFrame(wrap, fg_color="transparent")
        head.pack(fill="x", pady=(0, 16))
        kiri = ctk.CTkFrame(head, fg_color="transparent")
        kiri.pack(side="left")
        ctk.CTkLabel(kiri, text=APP_NAME, font=("Segoe UI Semibold", 32), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(kiri, text=self.tr("subtitle"), font=("Segoe UI", 13), text_color=MUTED).pack(anchor="w")
        bhs = self._segmen(head, ["ID", "EN"], self._ganti_bahasa)
        bhs.configure(width=90, height=30)
        bhs.set(self.lang.upper())
        bhs.pack(side="right", anchor="n")

        # Folder
        c1 = self._card(wrap)
        c1.pack(fill="x", pady=(0, 12))
        self._judul(c1, self.tr("folder")).pack(anchor="w", padx=18, pady=(14, 6))
        row = ctk.CTkFrame(c1, fg_color="transparent")
        row.pack(fill="x", padx=18)
        ctk.CTkEntry(
            row, textvariable=self.folder, height=40, corner_radius=12, fg_color=CARD2,
            border_color=BORDER, text_color=TEXT, placeholder_text_color=MUTED,
            placeholder_text=self.tr("placeholder"), font=("Segoe UI", 12),
        ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            row, text=self.tr("pick"), width=120, height=40, corner_radius=12, fg_color=ACCENT,
            hover_color=ACCENT_HOVER, font=("Segoe UI Semibold", 12), command=self._browse,
        ).pack(side="left", padx=(10, 0))
        pin = ctk.CTkFrame(c1, fg_color="transparent")
        pin.pack(fill="x", padx=18, pady=(10, 16))
        for nama in ("Downloads", "Desktop", "Documents"):
            ctk.CTkButton(
                pin, text=nama, width=96, height=28, corner_radius=10, fg_color=CARD2,
                hover_color=SOFT_HOVER, text_color=MUTED, font=("Segoe UI", 11),
                command=lambda n=nama: self._pintas(n),
            ).pack(side="left", padx=(0, 8))

        # Opsi
        c2 = self._card(wrap)
        c2.pack(fill="x", pady=(0, 12))
        self._judul(c2, self.tr("options")).pack(anchor="w", padx=18, pady=(14, 8))
        grid = ctk.CTkFrame(c2, fg_color="transparent")
        grid.pack(fill="x", padx=18)
        grid.columnconfigure((0, 1), weight=1)
        self._switch(grid, self.tr("sw_type"), self.v_type).grid(row=0, column=0, sticky="w", pady=5)
        self._switch(grid, self.tr("sw_sub"), self.v_sub).grid(row=0, column=1, sticky="w", pady=5)
        self._switch(grid, self.tr("sw_dup"), self.v_dup).grid(row=1, column=0, sticky="w", pady=5)
        self._switch(grid, self.tr("sw_clean"), self.v_clean).grid(row=1, column=1, sticky="w", pady=5)

        seg = ctk.CTkFrame(c2, fg_color="transparent")
        seg.pack(fill="x", padx=18, pady=(10, 16))
        seg.columnconfigure((0, 1), weight=1, uniform="a")
        left = ctk.CTkFrame(seg, fg_color="transparent")
        left.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        right = ctk.CTkFrame(seg, fg_color="transparent")
        right.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.dvals = [self.tr("d_none"), self.tr("d_year"), self.tr("d_month")]
        self.svals = [self.tr("s_mod"), self.tr("s_cre")]
        ctk.CTkLabel(left, text=self.tr("grp_date"), font=("Segoe UI", 12), text_color=MUTED).pack(anchor="w", pady=(0, 4))
        sd = self._segmen(left, self.dvals, self._on_date)
        sd.set(self.dvals[DATE_KEYS.index(self.date_key)])
        sd.pack(fill="x")
        ctk.CTkLabel(right, text=self.tr("src_date"), font=("Segoe UI", 12), text_color=MUTED).pack(anchor="w", pady=(0, 4))
        ss = self._segmen(right, self.svals, self._on_src)
        ss.set(self.svals[SRC_KEYS.index(self.src_key)])
        ss.pack(fill="x")

        # Tombol aksi
        bar = ctk.CTkFrame(wrap, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 12))
        bar.columnconfigure((0, 2), weight=2, uniform="b")
        bar.columnconfigure(1, weight=3, uniform="b")
        self._tombol(bar, self.tr("btn_preview"), lambda: self._klik("preview")).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._tombol(bar, self.tr("btn_run"), lambda: self._klik("run"), primer=True).grid(row=0, column=1, sticky="ew", padx=6)
        self._tombol(bar, self.tr("btn_undo"), lambda: self._klik("undo")).grid(row=0, column=2, sticky="ew", padx=(6, 0))

        self.progress = ctk.CTkProgressBar(wrap, height=6, corner_radius=6, fg_color=CARD2, progress_color=ACCENT)
        self.progress.set(0)
        self.progress.pack(fill="x", pady=(0, 6))
        self.status = ctk.CTkLabel(wrap, text="", font=("Segoe UI Semibold", 12), text_color=ACCENT, anchor="w")
        self.status.pack(fill="x", pady=(0, 6))

        # Footer (dipack dulu supaya selalu di bawah)
        foot = ctk.CTkFrame(wrap, fg_color="transparent")
        foot.pack(side="bottom", pady=(10, 0))
        ctk.CTkLabel(foot, text="by Fajar Umarsandi  |", font=("Segoe UI", 10), text_color=MUTED).pack(side="left")
        ctk.CTkButton(
            foot, text="Donate", width=44, height=16, fg_color="transparent", hover=False,
            text_color=ACCENT, font=ctk.CTkFont(family="Segoe UI", size=10, underline=True),
            command=lambda: webbrowser.open(DONATE_URL),
        ).pack(side="left", padx=(2, 0))

        self.log = ctk.CTkTextbox(
            wrap, corner_radius=18, fg_color=CARD, border_width=1, border_color=BORDER,
            text_color="#C9CCDA", font=("Consolas", 12), state="disabled",
        )
        self.log.pack(fill="both", expand=True)
        self.tulis(self.tr("intro"))

    # ----- Handler UI -----
    def _ganti_bahasa(self, val):
        if self.sibuk:
            return
        self.lang = val.lower()
        self.simpan_settings()
        self.after(30, self._bangun_ulang)

    def _bangun_ulang(self):
        self.wrap.destroy()
        self._build()

    def _on_date(self, val):
        self.date_key = DATE_KEYS[self.dvals.index(val)]
        self.simpan_settings()

    def _on_src(self, val):
        self.src_key = SRC_KEYS[self.svals.index(val)]
        self.simpan_settings()

    def tulis(self, teks):
        self.log.configure(state="normal")
        self.log.insert("end", teks + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def bersihkan(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.status.configure(text="")

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.folder.set(d)
            self.simpan_settings()

    def _pintas(self, nama):
        h = Path.home()
        for c in (h / "OneDrive" / nama, h / nama):
            if c.is_dir():
                self.folder.set(str(c))
                self.simpan_settings()
                return

    def _on_drop(self, event):
        try:
            paths = self.tk.splitlist(event.data)
            if not paths:
                return
            p = Path(paths[0])
            if p.is_file():
                p = p.parent
            self.folder.set(str(p))
            self.simpan_settings()
        except Exception:
            pass

    def _ambil_folder(self):
        p = Path(self.folder.get().strip())
        if not p.is_dir():
            messagebox.showwarning(APP_NAME, self.tr("warn_invalid"))
            return None
        if folder_berbahaya(p):
            messagebox.showwarning(APP_NAME, self.tr("warn_sensitive"))
            return None
        return p

    def _opts(self):
        return {
            "type": self.v_type.get(), "sub": self.v_sub.get(), "dup": self.v_dup.get(),
            "clean": self.v_clean.get(), "date": self.date_key, "src": self.src_key,
            "lang": self.lang, "dupdir": DUP_NAMES[self.lang],
        }

    # ----- Antrian & thread -----
    def _poll(self):
        try:
            while True:
                m = self.q.get_nowait()
                if m[0] == "log":
                    self.tulis(m[1])
                elif m[0] == "clear":
                    self.bersihkan()
                elif m[0] == "progress":
                    self.progress.set(m[1])
                elif m[0] == "status":
                    self.status.configure(text=m[1])
                elif m[0] == "info":
                    messagebox.showinfo(APP_NAME, m[1])
                elif m[0] == "confirm":
                    self.pending = m[1]
                elif m[0] == "done":
                    self._selesai()
        except queue.Empty:
            pass
        self.after(60, self._poll)

    def _mulai(self, fn, *args):
        if self.sibuk:
            return
        self.sibuk = True
        for b in self.btns:
            b.configure(state="disabled")
        self.progress.set(0)
        threading.Thread(target=self._aman, args=(fn,) + args, daemon=True).start()

    def _aman(self, fn, *args):
        try:
            fn(*args)
        except Exception as e:
            self.q.put(("log", self.tr("err", e=e)))
        finally:
            self.q.put(("done",))

    def _selesai(self):
        self.sibuk = False
        for b in self.btns:
            b.configure(state="normal")
        if self.pending:
            p, self.pending = self.pending, None
            root, moves, dups, o = p
            teks = self.tr("confirm_move", n=len(moves))
            if dups:
                teks += self.tr("confirm_dups", d=len(dups), dir=o["dupdir"])
            if messagebox.askyesno(APP_NAME, teks + self.tr("confirm_tail")):
                self._mulai(self._eksekusi, root, moves, dups, o)

    def _klik(self, mode):
        root = self._ambil_folder()
        if not root:
            return
        self.simpan_settings()
        if mode == "undo":
            if not (root / UNDO_FILE).exists():
                messagebox.showinfo(APP_NAME, self.tr("no_undo"))
                return
            self._mulai(self._undo, root)
        elif mode == "preview":
            self._mulai(self._preview, root, self._opts())
        else:
            self._mulai(self._cek, root, self._opts())

    # ----- Kerja berat (jalan di thread) -----
    def _rencana(self, root, o):
        put = self.q.put
        put(("log", self.tr("scan")))
        files = scan(root, o["sub"])
        put(("log", self.tr("found", n=len(files))))

        dups = []
        if o["dup"]:
            per_size = defaultdict(list)
            for f in files:
                try:
                    s = f.stat().st_size
                except OSError:
                    continue
                if s > 0:
                    per_size[s].append(f)
            kandidat = [f for g in per_size.values() if len(g) > 1 for f in g]
            if kandidat:
                put(("log", self.tr("check_dup", n=len(kandidat))))
            per_hash = defaultdict(list)
            for i, f in enumerate(kandidat, 1):
                try:
                    per_hash[(f.stat().st_size, hash_file(f))].append(f)
                except OSError:
                    pass
                put(("progress", i / len(kandidat)))
            for g in per_hash.values():
                if len(g) > 1:
                    g.sort(key=lambda p: (p.stat().st_mtime, len(str(p))))
                    dups.extend(g[1:])  # yang paling lama dipertahankan
            ds = set(dups)
            files = [f for f in files if f not in ds]

        moves = []
        for f in files:
            try:
                t = tujuan_dir(f, root, o)
            except OSError:
                continue
            if f.parent != t:
                moves.append((f, t))
        return moves, dups

    def _preview(self, root, o):
        self.q.put(("clear",))
        moves, dups = self._rencana(root, o)
        put = self.q.put
        put(("log", self.tr("preview_head", m=len(moves), d=len(dups))))
        if not moves and not dups:
            put(("log", self.tr("nothing")))
            return
        hitung = sorted(Counter(str(t.relative_to(root)) for _, t in moves).items())
        for nama, n in hitung[:40]:
            put(("log", f"  {nama:<32} {n}"))
        if len(hitung) > 40:
            put(("log", self.tr("more_folders", n=len(hitung) - 40)))
        if dups:
            total = sum(f.stat().st_size for f in dups if f.exists())
            put(("log", self.tr("dup_line", n=len(dups), size=fmt_size(total), dir=o["dupdir"])))
            for f in dups[:8]:
                put(("log", f"  - {f.relative_to(root)}"))
            if len(dups) > 8:
                put(("log", self.tr("more_items", n=len(dups) - 8)))
        put(("log", self.tr("preview_hint")))

    def _cek(self, root, o):
        self.q.put(("clear",))
        moves, dups = self._rencana(root, o)
        if not moves and not dups:
            self.q.put(("info", self.tr("nothing_info")))
            return
        self.q.put(("confirm", (root, moves, dups, o)))

    def _eksekusi(self, root, moves, dups, o):
        put = self.q.put
        put(("clear",))
        put(("log", self.tr("starting")))
        items = [(f, t, False) for f, t in moves] + [(f, root / o["dupdir"], True) for f in dups]
        riwayat, gagal, asal_dirs = [], 0, set()
        n_move = n_dup = ukuran_move = ukuran_dup = 0
        per_kat = Counter()
        for i, (f, t, is_dup) in enumerate(items, 1):
            try:
                ukuran = f.stat().st_size
                t.mkdir(parents=True, exist_ok=True)
                dst = target_unik(t / f.name)
                shutil.move(str(f), str(dst))
                riwayat.append([str(f), str(dst)])
                asal_dirs.add(f.parent)
                if is_dup:
                    n_dup += 1
                    ukuran_dup += ukuran
                else:
                    n_move += 1
                    ukuran_move += ukuran
                    per_kat[cari_kategori(f.suffix.lstrip(".").lower())] += 1
            except Exception as e:
                gagal += 1
                put(("log", self.tr("fail", name=f.name, err=e)))
            if i % 10 == 0 or i == len(items):
                put(("progress", i / len(items)))
        kosong = bersihin_kosong(asal_dirs, root) if o["clean"] else 0
        (root / UNDO_FILE).write_text(json.dumps(riwayat), encoding="utf-8")

        put(("log", self.tr("done_line", n=len(riwayat), g=gagal)))
        put(("log", self.tr("sum_title")))
        put(("log", self.tr("sum_total", n=n_move, size=fmt_size(ukuran_move))))
        if o["type"]:
            for key, n in per_kat.most_common():
                put(("log", f"    {CAT_NAMES[o['lang']][key]:<12}: {n}"))
        if n_dup:
            put(("log", self.tr("sum_dups", n=n_dup, size=fmt_size(ukuran_dup))))
        if kosong:
            put(("log", self.tr("clean_n", n=kosong)))
        put(("log", "\n" + self.tr("undo_hint")))
        status = self.tr("status_done", n=n_move, size=fmt_size(ukuran_move))
        if n_dup:
            status += self.tr("status_dups", d=n_dup, size=fmt_size(ukuran_dup))
        put(("status", status))

    def _undo(self, root):
        put = self.q.put
        put(("clear",))
        put(("log", self.tr("undoing")))
        berkas = root / UNDO_FILE
        riwayat = json.loads(berkas.read_text(encoding="utf-8"))
        ok = 0
        for i, (asal, kini) in enumerate(reversed(riwayat), 1):
            try:
                kini_p = Path(kini)
                if kini_p.exists():
                    a = target_unik(Path(asal))
                    a.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(kini_p), str(a))
                    ok += 1
            except Exception as e:
                put(("log", self.tr("fail", name=kini, err=e)))
            if i % 10 == 0 or i == len(riwayat):
                put(("progress", i / len(riwayat)))
        bersihin_kosong({Path(k).parent for _, k in riwayat}, root)
        berkas.unlink()
        put(("log", self.tr("undone", n=ok)))
        put(("status", self.tr("status_undo", n=ok)))


if __name__ == "__main__":
    App().mainloop()
