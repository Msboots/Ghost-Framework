#!/usr/bin/env python3
# -*- coding: utf-8 -*-
### BEGIN INIT INFO
# Provides:          ghost_framework
# Required-Start:    $network $remote_fs
# Required-Stop:     $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Удалённое управление Android через ADB for Android Devices
# Description:       A tool to manage Android devices via ADB for debugging, file management, screen mirroring, and more.
# Author:            
# + LIONMAD <https://github.com/Midohajhouj> 
# Version:           v2.0
# License:           MIT License - https://opensource.org/licenses/MIT
### END INIT INFO ###

# Standard Libraries
import os 
import sys 
import subprocess 
import logging
import ipaddress
import asyncio 
from datetime import datetime  
import shutil 
import zipfile 
import gzip

# Third-Party Libraries
from tqdm import tqdm 

# Define the log directory
log_dir = os.path.join(os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")), "ghost-framework", "logs")

# Create the directory if it doesn't exist
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Set up logging with more detail (timestamp, log level, message)
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "ghost_framework.log")),
        logging.StreamHandler()
    ]
)

# Color definitions for terminal outputs
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "bold": "\033[1m",
    "end": "\033[0m",
}

def color_text(text, color):
    """Return text wrapped in color codes."""
    return f"{COLORS.get(color, '')}{text}{COLORS['end']}"

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    """Display the Ghost Framework banner."""
    banner = f"""
      .-.
    .'   `.       {color_text('Ghost Framework v2.0', 'blue')}
   :0 0  :        {color_text('Удалённое управление Android через ADB', 'yellow')}
   : o    `.      {color_text ('Автор: LIONMAD' , 'red')}
  :         ``.
 :             `.
:  :         .   `.
:   :          ` . `.
 `.. :            `. ``;
    `:;             `:'
       :              `.
        `.              `.     
          `'`'`'`---..,____`.

{color_text('Ghost Framework v2.0', 'blue')}        
"""
    logging.info(banner)
    
def show_menu():
    """Display the main menu options."""
    items = [
        'Подключённые устройства',
        'Подключиться к устройству',
        'Отключить устройства',
        'Оболочка ADB',
        'Установить APK',
        'Установить несколько APK',
        'Сделать скриншот',
        'Записать экран',
        'Список приложений',
        'Перезагрузить устройство',
        'Создать резервную копию',
        'Восстановить из копии',
        'Отправить файл (шифрование)',
        'Скачать файл (шифрование)',
        'Удалить приложение',
        'Сведения об устройстве',
        'Показать экран',
        'Выполнить команду ADB',
        'Интерактивная оболочка',
        'Файлы на устройстве',
        'Удалить файл на устройстве',
        'Состояние батареи',
        'Выполнить скрипт',
        'Просмотр файлов',
        'Передать несколько файлов',
        'Подключение ADB по Wi-Fi',
        'Упаковать / распаковать',
        'Журнал устройства (logcat)',
    ]
    print()
    for row in range(14):
        left, right = row + 1, row + 15
        print(
            f"{color_text(f'[{left}]'.ljust(4), 'green')} {items[left - 1]:<29} "
            f"{color_text(f'[{right}]', 'green')} {items[right - 1]}"
        )
    print(f"{color_text('[29]', 'green')} Управлять телефоном с ПК (мышь и клавиатура)")
    print(f"\n{color_text('[0]', 'red')} Выход\n")


async def run_command_async(command):
    """Run a command asynchronously and return the output."""
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        logging.error(f"Ошибка выполнения команды: {stderr.decode().strip()}")
        return f"Ошибка выполнения команды: {stderr.decode().strip()}"
    
    logging.debug(f"Команда выполнена: {command}")
    return stdout.decode().strip()

def run_command(command):
    """Run a command synchronously and return the output."""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
        logging.debug(f"Команда выполнена: {command}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка выполнения команды: {e.stderr}")
        return f"Ошибка выполнения команды: {e.stderr}"

def validate_ip(ip):
    """Validate an IP address."""
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ipaddress.AddressValueError:
        return False

def validate_adb_address(address):
    """Проверить IPv4-адрес с необязательным портом ADB."""
    host, separator, port = address.partition(':')
    return validate_ip(host) and (
        not separator or (1 <= len(port) <= 5 and port.isascii()
                          and port.isdecimal() and 1 <= int(port) <= 65535)
    )

def select_device():
    """Allow the user to select a specific device if multiple devices are connected."""
    devices_output = run_command("adb devices")
    devices = [line.split('\t')[0] for line in devices_output.splitlines()[1:] if line.endswith('\tdevice')]
    
    if not devices:
        logging.error("Нет подключённых устройств.")
        return None
    elif len(devices) == 1:
        return devices[0]
    
    print(color_text("Подключённые устройства:", 'yellow'))
    for i, device in enumerate(devices):
        print(f"{color_text(f'[{i + 1}]', 'green')} {device}")
    
    choice = input(color_text("Выберите устройство: ", 'blue'))
    try:
        choice = int(choice) - 1
        if 0 <= choice < len(devices):
            return devices[choice]
        else:
            logging.error("Неверный выбор.")
            return None
    except ValueError:
        logging.error("Неверный ввод.")
        return None

def show_connected_devices():
    """Show all connected devices."""
    output = run_command("adb devices")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
    else:
        print(color_text(output, 'yellow'))

def connect_device():
    """Подключиться к ADB по IPv4-адресу и проверить авторизацию."""
    address = input(color_text("Введите IP-адрес или IP:порт устройства: ", 'blue')).strip()
    if not validate_adb_address(address):
        logging.error("Неверный адрес. Введите IPv4 или IPv4:порт (1–65535).")
        return None
    serial = address if ':' in address else f"{address}:5555"
    try:
        result = subprocess.run(
            ['adb', 'connect', serial], capture_output=True, text=True, timeout=15
        )
        state = subprocess.run(
            ['adb', '-s', serial, 'get-state'], capture_output=True, text=True, timeout=5
        )
        if state.returncode == 0 and state.stdout.strip() == 'device':
            logging.info(f"Подключено: {serial}")
            return serial
        logging.error((result.stdout + result.stderr + state.stderr).strip())
        logging.error("Проверьте беспроводную отладку и разрешение подключения на телефоне. "
                      "Для нового сопряжения выполните adb pair IP:ПОРТ_СОПРЯЖЕНИЯ.")
    except subprocess.TimeoutExpired:
        logging.error("Телефон не ответил вовремя. Проверьте адрес, порт и сеть.")
    except OSError as e:
        logging.error(f"Не удалось запустить ADB: {e}")
    return None

def choose_stream_settings():
    """Выбрать параметры трансляции до подключения к телефону."""
    print(color_text("Разрешение трансляции (максимальная сторона):", 'yellow'))
    print("[1] Исходное\n[2] До 1920 пикселей\n[3] До 1280 пикселей (по умолчанию)\n"
          "[4] До 960 пикселей\n[5] Свой размер\n[0] Отмена")
    print("Пропорции экрана сохраняются. Разрешение дисплея телефона не меняется.")
    sizes = {'1': 0, '2': 1920, '3': 1280, '4': 960}
    while True:
        choice = input(color_text("Выберите разрешение [3]: ", 'blue')).strip() or '3'
        if choice == '0':
            return None
        if choice in sizes:
            size = sizes[choice]
            break
        if choice == '5':
            value = input(color_text("Максимальная сторона в пикселях (256–8192): ", 'blue')).strip()
            if value.isascii() and value.isdecimal() and len(value) <= 4 and 256 <= int(value) <= 8192:
                size = int(value)
                break
            print("Введите целое число от 256 до 8192.")
        else:
            print("Выберите пункт от 0 до 5.")
    print("Частота кадров: например, 15, 30 или 60. 0 — без ограничения.")
    while True:
        value = input(color_text("Максимальная частота кадров [30]: ", 'blue')).strip() or '30'
        if value.isascii() and value.isdecimal() and len(value) <= 3 and 0 <= int(value) <= 240:
            fps = int(value)
            break
        print("Введите целое число от 0 до 240.")
    options = []
    if size:
        options.extend(['--max-size', str(size)])
    if fps:
        options.extend(['--max-fps', str(fps)])
    print("Звук телефона:\n[1] Воспроизводить на ПК (по умолчанию)\n[2] Без звука")
    while True:
        audio = input(color_text("Выберите режим звука [1]: ", 'blue')).strip() or '1'
        if audio in ('1', '2'):
            break
        print("Выберите 1 или 2.")
    if audio == '1':
        options.extend(['--audio-source=output', '--audio-codec=aac'])
    else:
        options.append('--no-audio')
    print(f"Трансляция: {'до ' + str(size) + ' пикселей' if size else 'исходное разрешение'}, "
          f"{'до ' + str(fps) + ' кадр/с' if fps else 'без ограничения частоты кадров'}, "
          f"{'звук на ПК' if audio == '1' else 'без звука'}.")
    return options

def control_device():
    """Открыть экран выбранного телефона с управлением через scrcpy."""
    scrcpy = shutil.which('scrcpy')
    if not scrcpy:
        logging.error("scrcpy не установлен. Установите scrcpy и повторите запуск пункта 29.")
        return
    options = choose_stream_settings()
    if options is None:
        return
    device = select_device()
    if not device:
        print("Включите беспроводную отладку на телефоне и укажите адрес подключения.")
        device = connect_device()
        if not device:
            return
    print(color_text("Открывается экран телефона. Управление: мышь и клавиатура.\n"
                     "Закройте окно scrcpy, чтобы вернуться в меню Ghost.", 'blue'))
    try:
        result = subprocess.run(
            [scrcpy, '--serial', device,
             '--window-title', f'Ghost — управление телефоном ({device})'] + options
        )
        if result.returncode:
            logging.error(f"scrcpy завершился с кодом {result.returncode}. "
                          "Подробности указаны выше в выводе scrcpy.")
    except OSError as e:
        logging.error(f"Не удалось запустить scrcpy: {e}")

def disconnect_device():
    """Disconnect from all connected devices."""
    output = run_command("adb disconnect")
    if "disconnected" in output.lower():
        logging.info(output)
    else:
        logging.error(output)

def access_shell():
    """Access the shell of a connected device."""
    device = select_device()
    if not device:
        return
    print(color_text(f"Открывается оболочка ADB устройства {device}...", 'blue'))
    try:
        subprocess.run(f"adb -s {device} shell", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка доступа к оболочке: {e}")

def adb_command(device, command):
    """Execute an ADB command on the specified device."""
    try:
        result = subprocess.run(f"adb -s {device} {command}", shell=True, text=True, capture_output=True, check=True)
        logging.debug(f"Команда выполнена: {command}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка выполнения команды: {e.stderr}")
        return f"Ошибка выполнения команды: {e.stderr}"

def install_apk():
    """Install a single APK."""
    device = select_device()
    if not device:
        return
    apk_path = input(color_text("Введите путь к APK: ", 'blue'))
    if not os.path.exists(apk_path):
        logging.error("APK-файл не найден!")
        return
    
    try:
        logging.info(f"Установка APK: {apk_path}")
        output = adb_command(device, f"install {apk_path}")
        if "success" in output.lower():
            logging.info(f"APK успешно установлен: {apk_path}")
        else:
            logging.error(f"Не удалось установить APK: {output}")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")

def install_multiple_apks():
    """Install multiple APKs in batch."""
    device = select_device()
    if not device:
        return
    apk_paths = input(color_text("Введите пути к APK через запятую: ", 'blue')).split(',')
    for apk_path in apk_paths:
        apk_path = apk_path.strip()
        if not os.path.exists(apk_path):
            logging.error(f"APK-файл не найден: {apk_path}")
            continue
        logging.info(f"Установка APK: {apk_path}")
        output = adb_command(device, f"install {apk_path}")
        if "success" in output.lower():
            logging.info(f"APK успешно установлен: {apk_path}")
        else:
            logging.error(f"Не удалось установить APK: {output}")

def take_screenshot():
    """Take screenshot with timestamp-based file naming."""
    device = select_device()
    if not device:
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_file = f"screenshot_{timestamp}.png"
    output = adb_command(device, f"exec-out screencap -p > {screenshot_file}")
    if os.path.exists(screenshot_file):
        logging.info(f"Скриншот сохранён: {screenshot_file}")
    else:
        logging.error("Не удалось сделать скриншот.")

def record_screen():
    """Record the screen of the connected device."""
    device = select_device()
    if not device:
        return
    duration = input(color_text("Введите длительность записи в секундах: ", 'blue'))
    try:
        duration = int(duration)
        if duration <= 0:
            raise ValueError("Длительность должна быть целым положительным числом.")
    except ValueError as e:
        logging.error(f"Неверная длительность: {e}")
        return

    logging.info(f"Запись в течение {duration} секунд...")
    output = adb_command(device, f"shell screenrecord --time-limit {duration} /sdcard/screenrecord.mp4 && pull /sdcard/screenrecord.mp4")
    if os.path.exists("screenrecord.mp4"):
        logging.info("Запись экрана сохранена: screenrecord.mp4")
    else:
        logging.error("Не удалось записать экран.")

def list_installed_apps():
    """List all installed apps on the connected device."""
    device = select_device()
    if not device:
        return
    output = adb_command(device, "shell pm list packages")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
    else:
        print(color_text(output, 'yellow'))

def reboot_device():
    """Reboot the connected device."""
    device = select_device()
    if not device:
        return
    output = adb_command(device, "reboot")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
    else:
        logging.info("Устройство перезагружено.")

def backup_device():
    """Backup device data with progress indicator."""
    device = select_device()
    if not device:
        return
    backup_file = input(color_text("Введите имя файла резервной копии: ", 'blue'))
    print(color_text("Создание резервной копии...", 'blue'))
    process = subprocess.Popen(f"adb -s {device} backup -all -f {backup_file}.ab", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(color_text(output.strip(), 'yellow'))
            print(color_text("Выполняется резервное копирование...", 'blue'))
    
    if process.returncode == 0:
        logging.info(f"Резервная копия сохранена: {backup_file}.ab")
    else:
        logging.error("Не удалось создать резервную копию.")

def restore_device():
    """Restore device data."""
    device = select_device()
    if not device:
        return
    backup_file = input(color_text("Введите имя файла резервной копии: ", 'blue'))
    output = adb_command(device, f"restore {backup_file}.ab")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
    else:
        logging.info(f"Восстановлено из {backup_file}.ab")

def push_file_secure():
    """Push a file to the device securely."""
    device = select_device()
    if not device:
        return
    local_path = input(color_text("Введите путь к файлу на компьютере: ", 'blue'))
    remote_path = input(color_text("Введите путь к файлу на устройстве: ", 'blue'))
    
    # Encrypt the file before pushing
    try:
        with open(local_path, 'rb') as file:
            file_data = file.read()
        encrypted_data = cipher_suite.encrypt(file_data)
        encrypted_file = local_path + ".enc"
        with open(encrypted_file, 'wb') as file:
            file.write(encrypted_data)
        
        output = adb_command(device, f"push {encrypted_file} {remote_path}")
        if "error" in output.lower() or "ошибка" in output.lower():
            logging.error(output)
        else:
            logging.info(f"Зашифрованный файл отправлен в {remote_path}")
        os.remove(encrypted_file)  # Clean up the encrypted file
    except Exception as e:
        logging.error(f"Ошибка отправки зашифрованного файла: {e}")

def pull_file_secure():
    """Pull a file from the device securely."""
    device = select_device()
    if not device:
        return
    remote_path = input(color_text("Введите путь к файлу на устройстве: ", 'blue'))
    local_path = input(color_text("Введите путь к файлу на компьютере: ", 'blue'))
    
    # Pull the encrypted file
    encrypted_file = local_path + ".enc"
    output = adb_command(device, f"pull {remote_path} {encrypted_file}")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
        return
    
    # Decrypt the file
    try:
        with open(encrypted_file, 'rb') as file:
            encrypted_data = file.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        with open(local_path, 'wb') as file:
            file.write(decrypted_data)
        logging.info(f"Расшифрованный файл сохранён в {local_path}")
        os.remove(encrypted_file)  # Clean up the encrypted file
    except Exception as e:
        logging.error(f"Ошибка скачивания зашифрованного файла: {e}")

def uninstall_app():
    """Uninstall an app from the device."""
    device = select_device()
    if not device:
        return
    package_name = input(color_text("Введите имя пакета для удаления: ", 'blue'))
    output = adb_command(device, f"uninstall {package_name}")
    if "success" in output.lower():
        logging.info(f"Приложение {package_name} успешно удалено.")
    else:
        logging.error(f"Не удалось удалить приложение: {output}")

def show_device_info():
    """Show detailed device information."""
    device = select_device()
    if not device:
        return
    model = adb_command(device, "shell getprop ro.product.model")
    android_version = adb_command(device, "shell getprop ro.build.version.release")
    battery_level = adb_command(device, "shell dumpsys battery | grep level")
    logging.info(f"Модель: {model}")
    logging.info(f"Версия Android: {android_version}")
    logging.info(f"Уровень заряда: {battery_level}")

def mirror_screen():
    """Mirror the device screen to the computer."""
    device = select_device()
    if not device:
        return
    output = adb_command(device, "exec-out screenrecord --output-format=h264 - | ffplay -")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
    else:
        logging.info("Трансляция экрана запущена.")

def execute_custom_command():
    """Execute a custom ADB command."""
    device = select_device()
    if not device:
        return
    command = input(color_text("Введите команду ADB: ", 'blue'))
    output = adb_command(device, command)
    logging.info(output)

def interactive_shell():
    """Start an interactive ADB shell session."""
    device = select_device()
    if not device:
        return
    print(color_text(f"Запуск интерактивной оболочки ADB устройства {device}...", 'blue'))
    print(color_text("Введите 'exit' для возврата в главное меню.", 'yellow'))
    while True:
        command = input(color_text("adb shell> ", 'blue'))
        if command.lower() == 'exit':
            break
        output = adb_command(device, f"shell {command}")
        print(color_text(output, 'yellow'))

def list_files_on_device():
    """List files in a specific directory on the device."""
    device = select_device()
    if not device:
        return
    remote_path = input(color_text("Введите путь к каталогу на устройстве: ", 'blue'))
    output = adb_command(device, f"shell ls {remote_path}")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
    else:
        print(color_text(output, 'yellow'))

def delete_file_on_device():
    """Delete a file or directory on the device."""
    device = select_device()
    if not device:
        return
    remote_path = input(color_text("Введите путь к файлу или каталогу на устройстве: ", 'blue'))
    output = adb_command(device, f"shell rm -rf {remote_path}")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
    else:
        logging.info(f"Удалено: {remote_path}")

def check_battery_health():
    """Check the battery health and charging status."""
    device = select_device()
    if not device:
        return
    battery_health = adb_command(device, "shell dumpsys battery | grep health")
    charging_status = adb_command(device, "shell dumpsys battery | grep status")
    logging.info(f"Состояние батареи: {battery_health}")
    logging.info(f"Состояние зарядки: {charging_status}")

def execute_script():
    """Execute a series of ADB commands from a script file."""
    device = select_device()
    if not device:
        return
    script_path = input(color_text("Введите путь к скрипту: ", 'blue'))
    if not os.path.exists(script_path):
        logging.error("Скрипт не найден!")
        return
    
    with open(script_path, 'r') as file:
        commands = file.readlines()
    
    for command in commands:
        command = command.strip()
        if command:
            logging.info(f"Выполнение команды: {command}")
            output = adb_command(device, command)
            print(color_text(output, 'yellow'))

def interactive_file_browser():
    """Interactive file browser for selecting files to push/pull."""
    device = select_device()
    if not device:
        return
    remote_path = input(color_text("Введите путь к каталогу на устройстве: ", 'blue'))
    output = adb_command(device, f"shell ls {remote_path}")
    if "error" in output.lower() or "ошибка" in output.lower():
        logging.error(output)
        return
    
    files = output.splitlines()
    print(color_text("Файлы в каталоге:", 'yellow'))
    for i, file in enumerate(files):
        print(f"{color_text(f'[{i + 1}]', 'green')} {file}")
    
    choice = input(color_text("Выберите файл: ", 'blue'))
    try:
        choice = int(choice) - 1
        if 0 <= choice < len(files):
            selected_file = files[choice]
            action = input(color_text("Действие: (1) отправить или (2) скачать файл: ", 'blue'))
            if action == '1':
                local_path = input(color_text("Введите путь к файлу на компьютере: ", 'blue'))
                output = adb_command(device, f"push {local_path} {remote_path}/{selected_file}")
                if "error" in output.lower() or "ошибка" in output.lower():
                    logging.error(output)
                else:
                    logging.info(f"Файл отправлен в {remote_path}/{selected_file}")
            elif action == '2':
                local_path = input(color_text("Введите путь к файлу на компьютере: ", 'blue'))
                output = adb_command(device, f"pull {remote_path}/{selected_file} {local_path}")
                if "error" in output.lower() or "ошибка" in output.lower():
                    logging.error(output)
                else:
                    logging.info(f"Файл сохранён в {local_path}")
            else:
                logging.error("Неверное действие.")
        else:
            logging.error("Неверный выбор.")
    except ValueError:
        logging.error("Неверный ввод.")

def batch_push_pull_files():
    """Batch push or pull multiple files."""
    device = select_device()
    if not device:
        return
    action = input(color_text("Действие: (1) отправить или (2) скачать файлы: ", 'blue'))
    if action not in ['1', '2']:
        logging.error("Неверное действие.")
        return
    
    if action == '1':
        local_dir = input(color_text("Введите путь к каталогу на компьютере: ", 'blue'))
        remote_dir = input(color_text("Введите путь к каталогу на устройстве: ", 'blue'))
        if not os.path.isdir(local_dir):
            logging.error("Каталог на компьютере не найден.")
            return
        
        files = os.listdir(local_dir)
        for file in tqdm(files, desc="Отправка файлов", unit="файл"):
            local_path = os.path.join(local_dir, file)
            output = adb_command(device, f"push {local_path} {remote_dir}")
            if "error" in output.lower() or "ошибка" in output.lower():
                logging.error(f"Не удалось отправить {file}: {output}")
            else:
                logging.info(f"Файл {file} отправлен в {remote_dir}")
    
    elif action == '2':
        remote_dir = input(color_text("Введите путь к каталогу на устройстве: ", 'blue'))
        local_dir = input(color_text("Введите путь к каталогу на компьютере: ", 'blue'))
        if not os.path.isdir(local_dir):
            logging.error("Каталог на компьютере не найден.")
            return
        
        output = adb_command(device, f"shell ls {remote_dir}")
        if "error" in output.lower() or "ошибка" in output.lower():
            logging.error(output)
            return
        
        files = output.splitlines()
        for file in tqdm(files, desc="Скачивание файлов", unit="файл"):
            output = adb_command(device, f"pull {remote_dir}/{file} {local_dir}")
            if "error" in output.lower() or "ошибка" in output.lower():
                logging.error(f"Не удалось скачать {file}: {output}")
            else:
                logging.info(f"Файл {file} сохранён в {local_dir}")

def connect_wifi_adb():
    """Connect to a device over Wi-Fi using ADB."""
    device = select_device()
    if not device:
        return
    ip = input(color_text("Введите IP-адрес устройства: ", 'blue'))
    if not validate_ip(ip):
        logging.error("Неверный IP-адрес.")
        return
    output = run_command(f"adb -s {device} tcpip 5555")
    if "restarting" in output.lower():
        logging.info("Служба ADB перезапущена в режиме TCP.")
        output = run_command(f"adb -s {device} connect {ip}")
        if "connected" in output.lower():
            logging.info(f"Подключено к {ip} по Wi-Fi.")
        else:
            logging.error(f"Не удалось подключиться к {ip}.")
    else:
        logging.error("Не удалось перезапустить ADB в режиме TCP.")

def compress_file(file_path, compress_type="zip"):
    """Compress a file using ZIP or GZIP."""
    try:
        if compress_type == "zip":
            with zipfile.ZipFile(f"{file_path}.zip", 'w') as zipf:
                zipf.write(file_path, os.path.basename(file_path))
            logging.info(f"Архив сохранён: {file_path}.zip")
        elif compress_type == "gzip":
            with open(file_path, 'rb') as f_in:
                with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logging.info(f"Архив сохранён: {file_path}.gz")
        else:
            logging.error("Неподдерживаемый тип сжатия.")
    except Exception as e:
        logging.error(f"Ошибка сжатия файла: {e}")

def decompress_file(file_path):
    """Decompress a ZIP or GZIP file."""
    try:
        if file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zipf:
                zipf.extractall(os.path.dirname(file_path))
            logging.info(f"Распакован архив {file_path}")
        elif file_path.endswith(".gz"):
            with gzip.open(file_path, 'rb') as f_in:
                with open(file_path[:-3], 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logging.info(f"Распакован архив {file_path}")
        else:
            logging.error("Неподдерживаемый формат файла.")
    except Exception as e:
        logging.error(f"Ошибка распаковки файла: {e}")

def view_device_logs():
    """View device logs (logcat) in real-time."""
    device = select_device()
    if not device:
        return
    print(color_text("Запуск logcat... Для остановки нажмите Ctrl+C.", 'blue'))
    try:
        subprocess.run(f"adb -s {device} logcat", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка чтения журнала: {e}")
    except KeyboardInterrupt:
        logging.info("Чтение logcat остановлено.")

def main():
    """Main function to display menu and handle user input."""
    try:
        
        while True:
            clear_screen()
            show_banner()
            show_menu()

            choice = input(color_text("Выберите пункт: ", 'blue'))

            if choice == '1':
                show_connected_devices()
            elif choice == '2':
                connect_device()
            elif choice == '3':
                disconnect_device()
            elif choice == '4':
                access_shell()
            elif choice == '5':
                install_apk()
            elif choice == '6':
                install_multiple_apks()
            elif choice == '7':
                take_screenshot()
            elif choice == '8':
                record_screen()
            elif choice == '9':
                list_installed_apps()
            elif choice == '10':
                reboot_device()
            elif choice == '11':
                backup_device()
            elif choice == '12':
                restore_device()
            elif choice == '13':
                push_file_secure()
            elif choice == '14':
                pull_file_secure()
            elif choice == '15':
                uninstall_app()
            elif choice == '16':
                show_device_info()
            elif choice == '17':
                mirror_screen()
            elif choice == '18':
                execute_custom_command()
            elif choice == '19':
                interactive_shell()
            elif choice == '20':
                list_files_on_device()
            elif choice == '21':
                delete_file_on_device()
            elif choice == '22':
                check_battery_health()
            elif choice == '23':
                execute_script()
            elif choice == '24':
                interactive_file_browser()
            elif choice == '25':
                batch_push_pull_files()
            elif choice == '26':
                connect_wifi_adb()
            elif choice == '27':
                file_path = input(color_text("Введите путь к файлу для упаковки или распаковки: ", 'blue'))
                action = input(color_text("Действие: (1) упаковать или (2) распаковать: ", 'blue'))
                if action == '1':
                    compress_type = input(color_text("Введите тип сжатия (zip/gzip): ", 'blue'))
                    compress_file(file_path, compress_type)
                elif action == '2':
                    decompress_file(file_path)
                else:
                    logging.error("Неверное действие.")
            elif choice == '28':
                view_device_logs()
            elif choice == '29':
                control_device()
            elif choice == '0':
                logging.info("Выход из Ghost Framework. До свидания!")
                break
            else:
                logging.error("Неверный пункт. Попробуйте ещё раз.")

            input(color_text("Нажмите Enter для продолжения...", 'blue'))
    
    except KeyboardInterrupt:
        logging.error("Выход из Ghost Framework. До свидания!")
        sys.exit(0)  # Exit cleanly

if __name__ == "__main__":
    main()
