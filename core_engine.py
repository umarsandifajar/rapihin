"""
core_engine.py - Smart Engine for Rapihin v2.0
Fitur:
- Tiered Duplicate Detection (Size check -> 4KB partial hash -> full BLAKE2b)
- EXIF parser (Tanggal foto diambil & merk kamera)
- ID3 / Audio parser (Artis, Album, Tahun)
- Old installer & zero-byte / broken shortcut detector
- Safe Recycle Bin integration (send2trash)
- Custom Keyword Rules (e.g. "invoice", "skripsi", "rahasia" -> Folder Tujuan Aman)
- Folder Exclusions / Stabilo (Protected folders never touched)
- Windows Context Menu installer/uninstaller
- GitHub update checker
"""

import hashlib
import json
import os
import re
import shutil
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import mutagen
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import send2trash
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False

APP_NAME = "rapihin"
APP_VERSION = "2.0.0"
GITHUB_REPO = "umarsandifajar/rapihin"
UNDO_FILE = ".rapihin_undo.json"

KATEGORI = {
    "images": {"jpg", "jpeg", "png", "webp", "gif", "bmp", "svg", "heic", "tiff", "ico", "raw", "cr2", "nef"},
    "video": {"mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "ts", "3gp"},
    "docs": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "odt", "rtf", "epub", "md"},
    "audio": {"mp3", "wav", "flac", "m4a", "aac", "ogg", "wma"},
    "archives": {"zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso"},
    "installers": {"exe", "msi", "bat", "cmd"},
    "code": {"py", "js", "ts", "html", "css", "json", "xml", "cpp", "c", "cs", "java", "php", "sql"},
}

CAT_NAMES = {
    "id": {
        "images": "Gambar", "video": "Video", "docs": "Dokumen", "audio": "Audio",
        "archives": "Arsip", "installers": "Installer", "code": "Kode", "other": "Lainnya"
    },
    "en": {
        "images": "Images", "video": "Videos", "docs": "Documents", "audio": "Audio",
        "archives": "Archives", "installers": "Installers", "code": "Code", "other": "Others"
    },
}

SKIP_FILES = {"desktop.ini", "thumbs.db", UNDO_FILE}
SKIP_DIRS = {"_Duplikat", "_Duplicates", "node_modules", "$RECYCLE.BIN", "System Volume Information", ".git"}


def fmt_size(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def get_category(ext):
    ext = ext.lstrip(".").lower()
    for cat, exts in KATEGORI.items():
        if ext in exts:
            return cat
    return "other"


def is_sensitive_folder(path):
    p = Path(path).resolve()
    if p.parent == p:
        return True
    sensitive = {"windows", "program files", "program files (x86)", "programdata", "system volume information"}
    return any(part.lower() in sensitive for part in p.parts)


# --- Tiered Hashing ---

def partial_hash(path, chunk_size=4096):
    h = hashlib.blake2b(digest_size=8)
    try:
        with open(path, "rb") as f:
            chunk = f.read(chunk_size)
            if chunk:
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def full_hash(path):
    h = hashlib.blake2b(digest_size=16)
    try:
        with open(path, "rb") as f:
            while chunk := f.read(1 << 20):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def find_duplicates_tiered(file_list, progress_callback=None):
    by_size = defaultdict(list)
    for p in file_list:
        try:
            sz = p.stat().st_size
            if sz > 0:
                by_size[sz].append(p)
        except OSError:
            continue

    candidates = [paths for sz, paths in by_size.items() if len(paths) > 1]
    total_candidates = sum(len(paths) for paths in candidates)

    by_partial = defaultdict(list)
    processed = 0
    for paths in candidates:
        for p in paths:
            ph = partial_hash(p)
            if ph:
                by_partial[(p.stat().st_size, ph)].append(p)
            processed += 1
            if progress_callback and processed % 20 == 0:
                progress_callback("partial_hash", processed, total_candidates)

    deep_candidates = [paths for key, paths in by_partial.items() if len(paths) > 1]
    total_deep = sum(len(paths) for paths in deep_candidates)

    deep_processed = 0
    by_full = defaultdict(list)
    for paths in deep_candidates:
        for p in paths:
            fh = full_hash(p)
            if fh:
                by_full[fh].append(p)
            deep_processed += 1
            if progress_callback and deep_processed % 10 == 0:
                progress_callback("full_hash", deep_processed, total_deep)

    duplicates = {}
    saved_bytes = 0
    for fh, paths in by_full.items():
        if len(paths) > 1:
            sorted_paths = sorted(paths, key=lambda x: (x.stat().st_mtime, len(x.name)))
            original = sorted_paths[0]
            dups = sorted_paths[1:]
            duplicates[original] = dups
            saved_bytes += sum(d.stat().st_size for d in dups)

    return duplicates, saved_bytes


# --- Metadata Extraction ---

def get_photo_date(path):
    if PIL_AVAILABLE:
        try:
            with Image.open(path) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        if tag_name in ("DateTimeOriginal", "DateTime"):
                            return datetime.strptime(str(value)[:10], "%Y:%m:%d")
        except Exception:
            pass
    return datetime.fromtimestamp(path.stat().st_mtime)


def get_audio_info(path):
    if MUTAGEN_AVAILABLE:
        try:
            audio = mutagen.File(path, easy=True)
            if audio:
                artist = audio.get("artist", [""])[0].strip()
                album = audio.get("album", [""])[0].strip()
                return artist, album
        except Exception:
            pass
    return None, None


# --- Custom Keyword Rule Matcher ---

def match_custom_rules(file_path, custom_rules):
    """
    custom_rules: list of dicts:
    [
        {"keyword": "skripsi", "folder": "Dokumen/Penting_Skripsi"},
        {"keyword": "invoice", "folder": "Keuangan/Invoice"},
        ...
    ]
    Matches if keyword is found in the filename (case-insensitive).
    """
    fname = file_path.name.lower()
    for rule in custom_rules:
        kw = rule.get("keyword", "").strip().lower()
        target_folder = rule.get("folder", "").strip()
        if kw and target_folder and kw in fname:
            return target_folder
    return None


# --- Junk & Installer Version Detector ---

def detect_junk_and_old_installers(file_list):
    zero_byte = []
    broken_lnk = []
    old_installers = []

    installers_by_app = defaultdict(list)
    version_regex = re.compile(r'^(.*?)[-_.v\s]+(\d+(?:\.\d+)+)(.*)$', re.IGNORECASE)

    for p in file_list:
        try:
            sz = p.stat().st_size
            if sz == 0 and p.suffix.lower() not in (".gitkeep", ".gitignore"):
                zero_byte.append(p)
                continue
        except OSError:
            continue

        ext = p.suffix.lower().lstrip(".")
        if ext in ("exe", "msi"):
            m = version_regex.match(p.stem)
            if m:
                app_name = m.group(1).lower().strip("-_ ")
                version_str = m.group(2)
                installers_by_app[app_name].append((version_str, p))

    for app, items in installers_by_app.items():
        if len(items) > 1:
            def parse_ver(v_tuple):
                try:
                    return [int(x) for x in v_tuple[0].split(".")]
                except ValueError:
                    return [0]
            sorted_items = sorted(items, key=parse_ver)
            for ver, path in sorted_items[:-1]:
                old_installers.append(path)

    return {
        "zero_byte": zero_byte,
        "broken_lnk": broken_lnk,
        "old_installers": old_installers
    }


def safe_recycle(path):
    if SEND2TRASH_AVAILABLE:
        try:
            send2trash.send2trash(str(path))
            return True, None
        except Exception as e:
            return False, str(e)
    return False, "send2trash not installed"


def get_unique_target(target_path):
    if not target_path.exists():
        return target_path
    i = 1
    while True:
        candidate = target_path.with_name(f"{target_path.stem}_{i}{target_path.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def set_context_menu(enable=True):
    if sys.platform != "win32":
        return False, "Hanya didukung di Windows"

    import winreg
    key_path = r"Directory\Background\shell\Rapihin"
    folder_key_path = r"Directory\shell\Rapihin"

    exe_path = sys.executable
    if getattr(sys, "frozen", False):
        cmd = f'"{exe_path}" "%V"'
    else:
        script_path = Path(__file__).resolve().parent / "rapihin.py"
        cmd = f'"{exe_path}" "{script_path}" "%V"'

    icon_path = str(Path(__file__).resolve().parent / "rapihin.ico")

    try:
        if enable:
            for kp in (key_path, folder_key_path):
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, kp) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Rapihin Folder Ini")
                    if os.path.exists(icon_path):
                        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{kp}\\command") as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, cmd)
            return True, "Context menu berhasil diaktifkan"
        else:
            for kp in (key_path, folder_key_path):
                try:
                    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{kp}\\command")
                    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, kp)
                except FileNotFoundError:
                    pass
            return True, "Context menu berhasil dinonaktifkan"
    except PermissionError:
        return False, "Perlu izin Administrator untuk mengubah Registry"
    except Exception as e:
        return False, str(e)


def check_github_update():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"Rapihin-App/{APP_VERSION}", "Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "").lstrip("v")
                html_url = data.get("html_url", "")
                body = data.get("body", "")

                def parse_v(v_str):
                    return [int(x) for x in re.findall(r'\d+', v_str)]

                current_parsed = parse_v(APP_VERSION)
                latest_parsed = parse_v(tag_name)

                if latest_parsed > current_parsed:
                    return True, tag_name, html_url, body
    except Exception:
        pass
    return False, APP_VERSION, "", ""
