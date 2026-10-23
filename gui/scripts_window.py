import json
import re
import customtkinter as ctk
from config import commands, SettingsEditor
from infrastructure_path_utils import get_root_dir_path
from pathlib import Path


class ScriptsWindow:
    def __init__(self):
        self._settings = SettingsEditor()

        self._root: ctk.CTk | None = None
        self._frame: ctk.CTkFrame | None = None
        self._row_state: ctk.CTkLabel | None = None
        self._storage: dict | None = None
        self._text_area_monitor: ctk.CTkTextbox | None = None
        self._rows = []
        self._padx, self._pady = 10, 10

    @staticmethod
    def select_file(entry: ctk.CTkEntry):
        from tkinter import filedialog
        # Открывает системное окно выбора файла с фильтром по .py
        scripts_folder = get_root_dir_path() / 'scripts'
        file_path = filedialog.askopenfilename(
            title='Выбор скрипта',
            initialdir=scripts_folder,
            filetypes=[("Python scripts", "*.py")]  # если все файлы, то:  ("All files", "*.*")
        )

        if file_path:
            file_path = Path(file_path)
            parts = []
            if str(file_path).startswith(str(scripts_folder)):
                while file_path != scripts_folder.parent and len(file_path.parts) > 1:
                    parts.insert(0, file_path.parts[-1])
                    file_path = file_path.parent
                entry.set('/'.join(parts))
            else:
                entry.set(file_path)
            # entry.configure(fg_color='gray24')

    def add_row(self, cmd_name, file, args, timeout, parent):
        """
        Добавить строку с элементами
        number -> номер строки
        parent -> фрейм на который всё добавляется
        """
        self._row_state.configure(text='')
        number = len(self._rows)
        row = {}
        frame_in = ctk.CTkFrame(parent, fg_color='transparent')
        frame_in.pack(expand=False, fill='x', padx=10, pady=2, anchor='ne')
        row['number'] = lambda n=number: n
        ctk.CTkLabel(
            frame_in, text=f'{number}', text_color='tomato', font=('roboto', 14, 'bold'), width=20,
        ).pack(expand=False, side='left', padx=10, pady=10)
        # название команды (для ассистента)
        ctk.CTkLabel(frame_in, text=f'name:', text_color='gray').pack(expand=False, side='left', padx=5, pady=10)
        name_entry = ctk.CTkEntry(frame_in, width=150)
        name_entry.set(cmd_name)
        name_entry.pack(expand=False, side='left', padx=5, pady=10)
        row['name'] = lambda ne=name_entry: ne.get()
        # путь к файлу скрипта
        ctk.CTkLabel(frame_in, text=f'file:', text_color='gray').pack(expand=False, side='left', padx=5, pady=10)
        file_entry = ctk.CTkEntry(frame_in, width=200)
        file_entry.set(file)
        file_entry.pack(expand=False, side='left', padx=(5, 0), pady=10)
        row['file'] = lambda fe=file_entry: fe.get()
        btn = ctk.CTkButton(frame_in, text='select', cursor='hand2', width=10)
        btn.configure(command=lambda e=file_entry: self.select_file(e))
        btn.pack(expand=False, side='left', padx=(0, 5), pady=10)
        # поле с таймаутом
        ctk.CTkLabel(frame_in, text=f'timeout:', text_color='gray').pack(expand=False, side='left', padx=5, pady=10)
        timeout_entry = ctk.CTkEntry(frame_in, width=50)
        timeout_entry.set(timeout)
        timeout_entry.pack(expand=False, side='left', padx=5, pady=10)
        row['timeout'] = lambda te=timeout_entry: te.get()
        # поле с аргументами
        ctk.CTkLabel(frame_in, text=f'args:', text_color='gray').pack(expand=False, side='left', padx=5, pady=10)
        args_entry = ctk.CTkEntry(frame_in, width=200)
        args = ', '.join(f'"{c}"' for c in args)
        args_entry.set(args)
        args_entry.pack(expand=True, fill='x', side='left', padx=5, pady=10)
        row['args'] = lambda ae=args_entry: ae.get()
        # удалить скрипт
        btn = ctk.CTkButton(frame_in, text='x', cursor='hand2', width=30)

        def btn_del_row_callback(f, row_name):
            self._row_state.configure(text='')
            self._rows = [r for r in self._rows if r['name']() != row_name]
            f.destroy()

        btn.configure(command=lambda f=frame_in, rn=cmd_name: btn_del_row_callback(f=f, row_name=rn))

        btn.configure(fg_color='red4', hover_color='red')
        btn.pack(expand=False, side='left', padx=(5, 10), pady=10)
        self._rows.append(row)

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, storage: dict):
        self._root = root
        self._frame = frame
        self._row_state = row_state
        self._storage = storage
        body_header_label = ctk.CTkLabel(frame, text='Управление скриптами')
        body_header_label.configure(font=('Consolas', 18, 'bold'))
        body_header_label.pack(expand=False, side='top', anchor='nw', padx=10, pady=(self._padx / 2, self._pady / 2))
        scrolable_frame = ctk.CTkScrollableFrame(frame, fg_color='transparent')
        scrolable_frame.pack(expand=True, fill='both', padx=5, pady=5)
        # заполнение таблицы с скриптами
        for cmd in commands:
            cmd_name = cmd
            file = commands[cmd_name]['file']
            args = commands[cmd_name]['args']
            timeout = commands[cmd_name]['timeout']
            self.add_row(cmd_name=cmd, file=file, args=args, timeout=timeout, parent=scrolable_frame)

        btn = ctk.CTkButton(frame, text='применить', cursor='hand2', command=lambda: self.get_apply_new_settings())
        btn.configure(fg_color='red4', hover_color='red')
        btn.pack(expand=False, padx=10, pady=10, side='right')

        btn_add_row = ctk.CTkButton(
            frame, text='добавить', cursor='hand2',
            command=lambda: self.add_row(cmd_name='', file='', args=[], timeout=10, parent=scrolable_frame)
        )
        btn_add_row.pack(expand=False, padx=10, pady=10, side='right')

    def get_apply_new_settings(self):
        """Сбор всех строк с командами для записи аргументов"""
        self._row_state.configure(text='')
        new_commands = {}
        for row in self._rows:
            command = {}
            command_name = ''
            command_number = None
            for key in row:
                val = row[key]()
                if key == 'number':
                    command_number = val
                    continue
                if key == 'name':
                    if not val:
                        self._row_state.configure(
                            text=f'Строка {command_number} - не указано название поля',
                            text_color='red4',
                        )
                        return
                    command_name = val
                    continue
                if key == 'file':
                    if not val:
                        self._row_state.configure(
                            text=f'Строка {command_number} - не указан путь к скрипту',
                            text_color='red4',
                        )
                        return
                if key == 'timeout':
                    val = float(val)
                if key == 'args':  # парсинг строки аргументов
                    val = val.strip()
                    if not val or val == '""':
                        val = []
                    else:
                        search = re.findall(pattern=r'"([^"]*)"', string=val)  # * вместо +
                        # отфильтровать пустые строки, если они вдруг появились
                        val = [s for s in search if s] if search else [val]
                command[key] = val
            new_commands[command_name] = command

        with open(file=get_root_dir_path() / 'scripts.json', mode='w', encoding='utf-8') as f:
            f.write(json.dumps(new_commands, ensure_ascii=False, indent=2))

        # лучше потом заменить на функцию геттер и также и с настройками в EditSettings
        commands.clear()
        commands.update(new_commands)
        self._row_state.configure(
            text=f'Настройки применены',
            text_color='green',
        )
