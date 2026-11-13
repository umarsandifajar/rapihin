<div align="center">

<img src="assets/icon.png" alt="rapihin" width="110">

# rapihin

**Rapihin folder berantakan dalam sekali klik.**
Pilah file otomatis per jenis & tanggal, ikut proses subfolder, dan temukan file duplikat.

![Version](https://img.shields.io/badge/version-1.1.0-6F75E8)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-6F75E8)
![Python](https://img.shields.io/badge/python-3.9%2B-6F75E8)
![License](https://img.shields.io/badge/license-MIT-6F75E8)

<img src="https://i.ibb.co.com/gbT18r3D/rapihin.webp" alt="Tampilan rapihin" width="720">

</div>

---

## ✨ Fitur

- **Pilah per jenis file**: Gambar, Video, Dokumen, Audio, Arsip, Installer, dan Lainnya.
- **Kelompokkan per tanggal**: per tahun (`2026`) atau per bulan (`2026-11`), pakai tanggal diubah atau tanggal dibuat.
- **Ikut proses subfolder**: semua file di dalam subfolder ikut dirapikan.
- **Deteksi file duplikat**: dibandingkan lewat isi file (hash), bukan cuma nama. Duplikat **tidak dihapus**, hanya dipindah ke folder `_Duplikat` supaya kamu bisa cek dulu.
- **Drag & drop**: seret folder langsung ke jendela aplikasi, atau pakai tombol pintas Downloads / Desktop / Documents.
- **Preview**: lihat dulu apa yang akan dipindah sebelum eksekusi.
- **Ringkasan hasil**: jumlah file, total ukuran, per kategori, dan ruang yang dihemat dari duplikat.
- **Undo**: balikin semua file ke tempat semula kalau hasilnya kurang pas.
- **Ingat pengaturan**: folder dan opsi terakhir tersimpan otomatis.
- **Dua bahasa**: Indonesia dan English, bisa diganti langsung dari pojok kanan atas.
- **Aman**: tidak pernah menghapus file, nama bentrok otomatis diberi angka (`foto_1.jpg`), dan folder sistem (`Windows`, `Program Files`, root drive) ditolak.
- Tampilan **soft dark** yang modern, dan tetap responsif walau filenya ribuan.

## 🗂 Contoh hasil

```
Downloads/
├── Gambar/
│   ├── 2026-09/screenshot.png
│   └── 2026-11/foto.jpg
├── Video/
│   └── 2026-10/rekaman.mp4
├── Dokumen/
│   └── 2026-11/tugas.pdf
└── _Duplikat/
    └── foto_1.jpg
```

## 📥 Download (paling gampang)

Buka halaman [**Releases**](../../releases/latest), lalu pilih salah satu:

| File | Untuk siapa |
|---|---|
| **`rapihin-setup-1.1.0.exe`** | Installer biasa. Dapat shortcut Start Menu, opsi shortcut Desktop, dan bisa di-uninstall dari *Apps & features*. Tidak butuh hak admin. |
| **`rapihin.exe`** | Versi portable. Tinggal double-click, tanpa install. Hapus file-nya kalau sudah tidak dipakai. |

Setelah terbuka: pilih folder, klik **Preview**, lalu **Rapihin sekarang**. Tidak perlu install Python.

> ⚠️ **Muncul "Windows protected your PC"?**
> Itu normal untuk aplikasi baru yang belum punya sertifikat digital berbayar. Klik **More info** lalu **Run anyway**.
> Kode sumbernya terbuka di repo ini, jadi kamu bisa cek sendiri atau build sendiri (lihat di bawah).

## 🧑‍💻 Jalankan dari source

```bash
git clone https://github.com/USERNAME/rapihin.git
cd rapihin
pip install -r requirements.txt
python rapihin.py
```

## 🔨 Build jadi .exe sendiri

Di Windows, jalankan `build.bat`, atau manual:

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name rapihin --icon rapihin.ico --add-data "rapihin.ico;." --collect-all customtkinter --collect-all tkinterdnd2 rapihin.py
```

Hasilnya ada di `dist/rapihin.exe`.

### Buat installer (opsional)

1. Install [Inno Setup 6](https://jrsoftware.org/isdl.php).
2. Pastikan `dist\rapihin.exe` sudah ada (jalankan `build.bat` dulu).
3. Jalankan `build_installer.bat`.

Hasilnya ada di `installer_output/rapihin-setup-1.1.0.exe`.

## ❓ FAQ

**Apakah file saya akan terhapus?**
Tidak. rapihin hanya memindahkan file. Duplikat pun cuma dipindah ke `_Duplikat`.

**Cara uninstall?**
Versi installer: *Settings → Apps → Installed apps → rapihin → Uninstall* (akan ditanya apakah pengaturan ikut dihapus). Versi portable: hapus file `rapihin.exe`.

**Salah klik, gimana?**
Klik **Undo**. Undo mengembalikan proses terakhir di folder tersebut.

**File apa yang dilewati?**
File tersembunyi (diawali titik), `desktop.ini`, `Thumbs.db`, dan folder tersembunyi atau `node_modules`.

**Nama folder kategori ikut bahasa?**
Ya. Bahasa Indonesia menghasilkan `Gambar`, `Dokumen`, dst. Bahasa English menghasilkan `Images`, `Documents`, dst.

**Di mana pengaturan disimpan?**
Di `%APPDATA%\rapihin\settings.json`. Hapus file itu untuk mereset.

**Antivirus mendeteksi exe-nya?**
Aplikasi yang dibuat dengan PyInstaller kadang kena false positive. Kamu bisa build sendiri dari source, atau lapor sebagai false positive ke vendor antivirus.

## 🌐 English

**rapihin** is a Windows desktop app that organizes messy folders: sorts files by type and date, processes subfolders, detects duplicate files by content hash, and lets you preview and undo every run. Nothing is ever deleted, files are only moved. It supports drag & drop, remembers your last settings, and has an English / Indonesian interface. Download `rapihin.exe` from [Releases](../../releases/latest) or run `python rapihin.py` after `pip install -r requirements.txt`.

## ☕ Dukung

Kalau rapihin membantu, kamu bisa dukung lewat [**Donate**](https://umarsandifajar.github.io/bio-sandiana/).

## 📄 Lisensi

[MIT](LICENSE) © 2026 Fajar Umarsandi
