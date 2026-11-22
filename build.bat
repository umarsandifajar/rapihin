@echo off
echo Menginstall dependensi...
pip install -r requirements.txt pyinstaller
echo.
echo Membuat rapihin.exe portable...
pyinstaller --noconfirm --clean --onefile --windowed --name rapihin --icon rapihin.ico --add-data "rapihin.ico;." --add-data "assets;assets" --collect-all customtkinter --collect-all tkinterdnd2 --collect-all PIL --collect-all piexif --collect-all send2trash rapihin.py
echo.
echo Selesai! Hasil portable ada di dist\rapihin.exe
pause
