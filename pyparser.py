import os
import json
import fnmatch
from pathlib import Path
import sys


class PyParser:
    def __init__(self):
        self.config_file = Path("pyparser_config.json")
        self.config = self.init_config()
        self.main_loop()

    def init_config(self):
        default_config = {
            "excluded": [".venv", "__pycache__", ".git", "pyparser.py", "pyparser_config.json", "code.txt",
                         "choosen_code.txt", "structure.txt"],
            "auto_gitignore": True
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("Ошибка чтения конфига, создан новый")
                return self.create_config(default_config)
        else:
            return self.create_config(default_config)

    def create_config(self, config):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("Создан файл конфигурации")

        if config.get("auto_gitignore", True):
            self.update_gitignore()

        return config

    def update_gitignore(self):
        gitignore_path = Path(".gitignore")
        entries_to_add = [
            "pyparser_config.json",
            "code.txt",
            "choosen_code.txt",
            "structure.txt",
            "pyparser.py"
        ]

        if not gitignore_path.exists():
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write("# PyParser generated files\n")
                for entry in entries_to_add:
                    f.write(f"{entry}\n")
            print(f"Создан {gitignore_path} с исключениями PyParser")
            return

        with open(gitignore_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            f.seek(0, os.SEEK_END)

            if "# PyParser" not in content:
                f.write("\n# PyParser generated files\n")
                for entry in entries_to_add:
                    if entry not in content:
                        f.write(f"{entry}\n")
                print(f"Обновлен {gitignore_path}")

    def should_exclude(self, path):
        path_str = str(path)
        path_parts = Path(path_str).parts

        for pattern in self.config.get("excluded", []):
            pattern = pattern.rstrip('/\\')

            if '*' in pattern:
                if fnmatch.fnmatch(path_str, pattern):
                    return True
                dir_pattern = pattern + '/*'
                if fnmatch.fnmatch(path_str, dir_pattern):
                    return True
            else:
                if pattern in path_parts:
                    return True
                if Path(pattern) in Path(path_str).parents:
                    return True
                if path_str.startswith(pattern):
                    if len(path_str) == len(pattern):
                        return True
                    if path_str[len(pattern)] in ['/', '\\']:
                        return True

        return False

    def find_py_files(self, root_dir="."):
        py_files = []
        excluded_count = 0

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not self.should_exclude(os.path.join(root, d))]

            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    if not self.should_exclude(full_path):
                        py_files.append(full_path)
                    else:
                        excluded_count += 1

        return py_files, excluded_count

    def try_read_file(self, file_path):
        encodings = ['utf-8', 'cp1251', 'latin-1', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(f"Не удалось прочитать файл {file_path}")

    def collect_all_py_files(self):
        print("Поиск .py файлов...")
        py_files, excluded_count = self.find_py_files()

        if not py_files:
            print("Не найдено .py файлов для обработки")
            return

        output_file = "code.txt"

        try:
            with open(output_file, 'w', encoding='utf-8') as out_f:
                for file_path in py_files:
                    try:
                        content = self.try_read_file(file_path)

                        out_f.write(f"\n{'=' * 80}\n")
                        out_f.write(f"# Файл: {file_path}\n")
                        out_f.write(f"{'=' * 80}\n\n")
                        out_f.write(content)
                        out_f.write("\n\n")

                    except UnicodeDecodeError as e:
                        print(f"Пропущен {file_path} ({e})")
                    except Exception as e:
                        print(f"Ошибка чтения {file_path}: {e}")

            print(f"✓ Собрано {len(py_files)} файлов (исключено: {excluded_count})")
            print(f"✓ Результат сохранен в: {output_file}")

        except Exception as e:
            print(f"Ошибка записи в файл: {e}")

    def manage_exceptions(self):
        while True:
            print("\n" + "=" * 40)
            print("Управление исключениями")
            print("=" * 40)
            print("Текущие исключения:")

            excluded = self.config.get("excluded", [])
            for i, item in enumerate(excluded, 1):
                print(f"{i}. {item}")

            print(f"\n1. Добавить исключение")
            print(f"2. Удалить исключение")
            print(f"3. Сбросить к значениям по умолчанию")
            print(f"4. Назад")

            choice = input("\nВыберите действие (1-4): ").strip()

            if choice == "1":
                self.add_exception()
            elif choice == "2":
                self.remove_exception()
            elif choice == "3":
                self.reset_exceptions()
            elif choice == "4":
                self.save_config()
                break
            else:
                print("Неверный выбор")

    def add_exception(self):
        print("\nФормат ввода:")
        print("- Файл: example.py")
        print("- Папка (и всё внутри): folder/ или folder")
        print("- Паттерн: *.py, test_*")
        print("- Полный путь: /home/user/project/.venv")
        print("Можно указать несколько через запятую")

        user_input = input("\nВведите исключение(я): ").strip()
        if not user_input:
            return

        new_items = [item.strip() for item in user_input.split(',') if item.strip()]
        excluded = self.config.get("excluded", [])

        for item in new_items:
            if item not in excluded:
                excluded.append(item)
                print(f"Добавлено: {item}")
            else:
                print(f"Уже существует: {item}")

        self.config["excluded"] = excluded

    def remove_exception(self):
        excluded = self.config.get("excluded", [])
        if not excluded:
            print("Список исключений пуст")
            return

        print("Введите номер исключения для удаления (можно несколько через запятую):")
        try:
            nums = input("Номера: ").strip()
            if not nums:
                return

            indices = [int(n.strip()) - 1 for n in nums.split(',')]
            indices.sort(reverse=True)

            for idx in indices:
                if 0 <= idx < len(excluded):
                    removed = excluded.pop(idx)
                    print(f"Удалено: {removed}")
                else:
                    print(f"Неверный номер: {idx + 1}")

        except ValueError:
            print("Ошибка: введите номера цифрами")

    def reset_exceptions(self):
        default = [".venv", "__pycache__", ".git", "pyparser.py", "pyparser_config.json", "code.txt",
                   "choosen_code.txt", "structure.txt"]
        self.config["excluded"] = default.copy()
        print("Исключения сброшены к значениям по умолчанию")

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print("Конфигурация сохранена")

    def collect_selected_files(self):
        print("\nВведите названия файлов .py (через запятую):")
        user_input = input("Файлы: ").strip()
        if not user_input:
            print("Не указаны файлы")
            return

        file_names = [name.strip() for name in user_input.split(',') if name.strip()]

        all_files, _ = self.find_py_files()

        selected_files = []
        for pattern in file_names:
            matches = []
            for file_path in all_files:
                file_name = os.path.basename(file_path)
                if fnmatch.fnmatch(file_name, pattern) or file_name == pattern:
                    matches.append(file_path)

            if not matches:
                print(f"Не найдено файлов для паттерна: {pattern}")
            elif len(matches) == 1:
                selected_files.append(matches[0])
                print(f"Найден: {matches[0]}")
            else:
                print(f"\nНайдено несколько файлов для '{pattern}':")
                for i, match in enumerate(matches, 1):
                    print(f"{i}. {match}")

                while True:
                    choice = input(f"Выберите номер (можно несколько через запятую, 0 для пропуска): ").strip()
                    if choice == "0":
                        break

                    try:
                        indices = [int(n.strip()) - 1 for n in choice.split(',') if n.strip()]
                        valid_indices = [i for i in indices if 0 <= i < len(matches)]
                        if valid_indices:
                            for idx in valid_indices:
                                selected_files.append(matches[idx])
                            break
                        else:
                            print("Неверные номера")
                    except ValueError:
                        print("Ошибка: введите номера цифрами")

        if not selected_files:
            print("Не выбрано ни одного файла")
            return

        output_file = "choosen_code.txt"

        try:
            with open(output_file, 'w', encoding='utf-8') as out_f:
                for file_path in selected_files:
                    try:
                        content = self.try_read_file(file_path)

                        out_f.write(f"\n{'=' * 80}\n")
                        out_f.write(f"# Файл: {file_path}\n")
                        out_f.write(f"{'=' * 80}\n\n")
                        out_f.write(content)
                        out_f.write("\n\n")

                    except Exception as e:
                        print(f"Ошибка чтения {file_path}: {e}")

            print(f"\n✓ Собрано {len(selected_files)} файлов")
            print(f"✓ Результат сохранен в: {output_file}")

        except Exception as e:
            print(f"Ошибка записи в файл: {e}")

    def generate_structure(self):
        output_file = "structure.txt"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Структура проекта: {os.path.basename(os.getcwd())}\n")
                f.write("=" * 60 + "\n\n")

                self._write_directory_tree(".", f, "", True)

            print(f"✓ Структура проекта сохранена в: {output_file}")

        except Exception as e:
            print(f"Ошибка при создании структуры: {e}")

    def _write_directory_tree(self, path, file_obj, prefix, is_last=True):
        try:
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if not self.should_exclude(full_path):
                    items.append((item, full_path))

            items.sort(key=lambda x: (not os.path.isdir(x[1]), x[0].lower()))

            for i, (item_name, full_path) in enumerate(items):
                is_last_item = (i == len(items) - 1)

                if is_last:
                    connector = "└── "
                    next_prefix = prefix + "    "
                else:
                    connector = "├── "
                    next_prefix = prefix + "│   "

                file_obj.write(f"{prefix}{connector}{item_name}\n")

                if os.path.isdir(full_path):
                    self._write_directory_tree(full_path, file_obj, next_prefix, is_last_item)

        except PermissionError:
            file_obj.write(f"{prefix}└── [Доступ запрещен]\n")
        except Exception as e:
            file_obj.write(f"{prefix}└── [Ошибка: {str(e)}]\n")

    def show_menu(self):
        print("\n" + "=" * 40)
        print("PyParser - Парсер Python проектов")
        print("=" * 40)
        print("1. Собрать все .py файлы в txt (code.txt)")
        print("2. Управление исключениями")
        print("3. Собрать выбранные файлы .py в txt (choosen_code.txt)")
        print("4. Создать структуру проекта в txt (structure.txt)")
        print("5. Выход")
        return input("\nВыберите действие (1-5): ").strip()

    def main_loop(self):
        while True:
            try:
                choice = self.show_menu()

                if choice == "1":
                    self.collect_all_py_files()
                elif choice == "2":
                    self.manage_exceptions()
                elif choice == "3":
                    self.collect_selected_files()
                elif choice == "4":
                    self.generate_structure()
                elif choice == "5":
                    print("\nДо свидания!")
                    break
                else:
                    print("Неверный выбор, попробуйте снова")

                input("\nНажмите Enter для продолжения...")

            except KeyboardInterrupt:
                print("\n\nПрограмма прервана пользователем")
                break
            except Exception as e:
                print(f"\nПроизошла ошибка: {e}")
                import traceback
                traceback.print_exc()
                input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    if sys.platform == "win32":
        os.system("chcp 65001 > nul")

    parser = PyParser()