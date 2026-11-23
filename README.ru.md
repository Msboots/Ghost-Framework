# Ghost Framework — русский интерфейс

Форк [Midohajhouj/Ghost-Framework](https://github.com/Midohajhouj/Ghost-Framework) с русским меню, подсказками и сообщениями. Нумерация пунктов сохранена.

Журналы сохраняются в `$XDG_STATE_HOME/ghost-framework/logs` или в `~/.local/state/ghost-framework/logs`, если переменная не задана. Для запуска права root не требуются.

## Установка и запуск

Требуются Python 3 с модулем venv, ADB и FFmpeg (включая ffplay для показа экрана).

```bash
git clone https://github.com/Msboots/Ghost-Framework.git
cd Ghost-Framework
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python ghost.py
```

Для подключения по Wi-Fi включите беспроводную отладку на своём Android-устройстве. При необходимости выполните сопряжение через `adb pair`, затем подключитесь командой `adb connect IP:ПОРТ`. Адрес и порт указаны в настройках беспроводной отладки; порт может меняться.

При использовании отдельного сервера ADB задайте его порт:

```bash
ANDROID_ADB_SERVER_PORT=5039 .venv/bin/python ghost.py
```

## Проверка и ограничения

Проверены запуск русского меню, обработка неверного пункта и выход. До перевода на Android 16 проверены чтение сведений об устройстве и создание PNG-скриншота; сведения также прочитаны с Samsung Galaxy S8 на LineageOS 23.2.

Пункты 13–14 (шифрованная передача файлов) содержат унаследованную ошибку: переменная `cipher_suite` не определена. Остальные функции не прошли полную проверку. Ответы ADB и Android выводятся на исходном языке.

Лицензия исходного проекта: MIT, см. [LICENSE](LICENSE).
