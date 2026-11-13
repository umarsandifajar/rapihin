@echo off
echo Menginstall dependensi...
pip install -r requirements.txt pyinstaller
echo.
echo Membuat rapihin.exe...
pyinstaller --onefile --windowed --name rapihin --icon rapihin.ico --add-data "rapihin.ico;." --collect-all customtkinter --collect-all tkinterdnd2 rapihin.py
echo.
echo Selesai! Hasilnya ada di folder dist\rapihin.exe
pause
