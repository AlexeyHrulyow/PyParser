import os
import json
import fnmatch
from pathlib import Path
import sys


class PyParser:
    def __init__(self):
        self.config_file = Path("pyparser_config.json")
        self.output_files = ["code.txt", "choosen_code.txt", "structure.txt"]
        self.config = self.init_config()
        self.ensure_gitignore()
        self.main_loop()

    def init_config(self):
        default_config = {
            "excluded": [".venv", "__pycache__", ".git", "pyparser.py", "pyparser_config.json"] + self.output_files,
            "file_types": [".py", ".html", ".css", ".js", ".json", ".txt", ".md"],
            "auto_gitignore": True
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    system_files = ["pyparser.py", "pyparser_config.json"] + self.output_files
                    for sys_file in system_files:
                        if sys_file not in config.get("excluded", []):
                            config["excluded"].append(sys_file)
                    if "file_types" not in config:
                        config["file_types"] = default_config["file_types"]
                    return config
            except json.JSONDecodeError:
                print("Ошибка чтения конфига, создан новый")
                return self.create_config(default_config)
        else:
            return self.create_config(default_config)

    def create_config(self, config):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("Создан файл конфигурации")
        return config

    def ensure_gitignore(self):
        if not self.config.get("auto_gitignore", True):
            return

        gitignore_path = Path(".gitignore")
        entries_to_add = self.output_files + ["pyparser_config.json", "pyparser.py"]

        if not gitignore_path.exists():
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write("# PyParser generated files\n")
                for entry in entries_to_add:
                    f.write(f"{entry}\n")
            print(f"Создан {gitignore_path} с исключениями PyParser")
            return

        with open(gitignore_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
            new_lines = []

            pyparser_section = False
            updated = False

            for line in lines:
                if line.strip() == "# PyParser generated files":
                    pyparser_section = True
                    new_lines.append(line)
                elif pyparser_section and line.strip() and not line.strip().startswith("#"):
                    continue
                else:
                    if pyparser_section and (not line.strip() or line.strip().startswith("#")):
                        pyparser_section = False
                    new_lines.append(line)

            while new_lines and not new_lines[-1].strip():
                new_lines.pop()

            if not any("# PyParser generated files" in line for line in new_lines):
                new_lines.append("")
                new_lines.append("# PyParser generated files")
            else:
                for i, line in enumerate(new_lines):
                    if line.strip() == "# PyParser generated files":
                        j = i + 1
                        while j < len(new_lines) and new_lines[j].strip() and not new_lines[j].strip().startswith("#"):
                            del new_lines[j]

            for entry in entries_to_add:
                if not any(entry == line.strip() for line in new_lines):
                    for i, line in enumerate(new_lines):
                        if line.strip() == "# PyParser generated files":
                            new_lines.insert(i + 1, entry)
                            updated = True
                            break

            if updated:
                f.seek(0)
                f.write("\n".join(new_lines))
                f.truncate()
                print(f"Обновлен {gitignore_path}")

    def should_exclude(self, path):
        if isinstance(path, str):
            path_obj = Path(path)
        else:
            path_obj = path

        try:
            abs_path = path_obj.absolute()
        except:
            return False

        path_str = str(abs_path).replace('\\', '/')

        cwd = Path.cwd().absolute()
        cwd_str = str(cwd).replace('\\', '/')

        if path_str.startswith(cwd_str + '/'):
            rel_path = path_str[len(cwd_str) + 1:]
        else:
            rel_path = path_str

        for pattern in self.config.get("excluded", []):
            pattern = pattern.strip()
            if not pattern:
                continue

            pattern = pattern.replace('\\', '/')

            if os.path.isabs(pattern):
                pattern_abs = Path(pattern).absolute()
                pattern_str = str(pattern_abs).replace('\\', '/')
                if path_str.startswith(pattern_str):
                    return True

            else:
                if pattern.endswith('/*'):
                    dir_pattern = pattern[:-2]
                    if rel_path.startswith(dir_pattern + '/') or rel_path == dir_pattern:
                        return True
                    if path_str.endswith('/' + dir_pattern) or path_str.endswith('/' + dir_pattern + '/'):
                        return True

                elif '*' in pattern:
                    if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(path_str, pattern):
                        return True

                else:
                    if pattern in rel_path.split('/') or pattern in path_str.split('/'):
                        path_parts = rel_path.split('/')
                        if pattern in path_parts:
                            return True

                    if rel_path == pattern or path_str.endswith('/' + pattern):
                        return True

        return False

    def find_files_by_types(self, root_dir=".", file_types=None):
        if file_types is None:
            file_types = self.config.get("file_types", [".py"])

        files = []
        excluded_count = 0

        for root, dirs, filenames in os.walk(root_dir):
            dirs_to_remove = []
            for d in dirs:
                full_dir_path = os.path.join(root, d)
                if self.should_exclude(full_dir_path):
                    dirs_to_remove.append(d)
                    excluded_count += 1

            for d in dirs_to_remove:
                dirs.remove(d)

            for filename in filenames:
                if any(filename.endswith(ext) for ext in file_types):
                    full_path = os.path.join(root, filename)
                    if not self.should_exclude(full_path):
                        files.append(full_path)
                    else:
                        excluded_count += 1

        return files, excluded_count

    def try_read_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()

            encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1', 'iso-8859-1']

            for encoding in encodings:
                try:
                    return raw_data.decode(encoding)
                except UnicodeDecodeError:
                    continue

            try:
                return raw_data.decode('utf-16')
            except UnicodeDecodeError:
                pass

            return raw_data.decode('utf-8', errors='ignore')

        except Exception as e:
            raise UnicodeDecodeError(f"Не удалось прочитать файл {file_path}: {e}")

    def collect_all_files(self):
        file_types = self.config.get("file_types", [".py"])
        print(f"Поиск файлов с расширениями: {', '.join(file_types)}...")
        files, excluded_count = self.find_files_by_types(".", file_types)

        if not files:
            print("Не найдено файлов для обработки")
            return

        output_file = "code.txt"

        try:
            with open(output_file, 'w', encoding='utf-8') as out_f:
                for file_path in files:
                    try:
                        content = self.try_read_file(file_path)

                        out_f.write(f"\n{'=' * 80}\n")
                        out_f.write(f"# Файл: {file_path}\n")
                        out_f.write(f"{'=' * 80}\n\n")
                        out_f.write(content)
                        if not content.endswith('\n'):
                            out_f.write('\n')
                        out_f.write("\n")

                    except Exception as e:
                        print(f"Ошибка при обработке {file_path}: {e}")

            print(f"✓ Собрано {len(files)} файлов (исключено: {excluded_count})")
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
            output_files_set = set(self.output_files + ["pyparser.py", "pyparser_config.json"])

            for i, item in enumerate(excluded, 1):
                marker = " [системное]" if item in output_files_set else ""
                print(f"{i}. {item}{marker}")

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
        print("- Папка (и всё внутри): folder/  или folder/*")
        print("- Паттерн: *.py, test_*")
        print("Можно указать несколько через запятую")

        user_input = input("\nВведите исключение(я): ").strip()
        if not user_input:
            return

        new_items = [item.strip() for item in user_input.split(',') if item.strip()]
        excluded = self.config.get("excluded", [])

        for item in new_items:
            item = item.replace('\\', '/')

            if item.endswith('/'):
                item = item.rstrip('/') + '/*'
            elif not item.endswith('/*') and not '*' in item and not '.' in item:
                item = item + '/*'

            if item not in excluded:
                excluded.append(item)
                print(f"Добавлено: {item}")
            else:
                print(f"Уже существует: {item}")

        self.config["excluded"] = excluded
        self.save_config()

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

            system_files = set(self.output_files + ["pyparser.py", "pyparser_config.json"])

            removed_count = 0
            for idx in indices:
                if 0 <= idx < len(excluded):
                    if excluded[idx] in system_files:
                        print(f"Нельзя удалить системное исключение: {excluded[idx]}")
                        continue
                    removed = excluded.pop(idx)
                    print(f"Удалено: {removed}")
                    removed_count += 1
                else:
                    print(f"Неверный номер: {idx + 1}")

            if removed_count > 0:
                self.config["excluded"] = excluded
                self.save_config()

        except ValueError:
            print("Ошибка: введите номера цифрами")

    def manage_file_types(self):
        while True:
            print("\n" + "=" * 40)
            print("Управление типами файлов")
            print("=" * 40)
            print("Текущие типы файлов для сбора:")

            file_types = self.config.get("file_types", [".py"])
            for i, ext in enumerate(file_types, 1):
                print(f"{i}. {ext}")

            print(f"\n1. Добавить тип файла")
            print(f"2. Удалить тип файла")
            print(f"3. Сбросить к значениям по умолчанию")
            print(f"4. Назад")

            choice = input("\nВыберите действие (1-4): ").strip()

            if choice == "1":
                self.add_file_type()
            elif choice == "2":
                self.remove_file_type()
            elif choice == "3":
                self.reset_file_types()
            elif choice == "4":
                self.save_config()
                break
            else:
                print("Неверный выбор")

    def add_file_type(self):
        print("\nФормат ввода:")
        print("- Расширение должно начинаться с точки")
        print("- Примеры: .html, .css, .js, .json")
        print("Можно указать несколько через запятую")

        user_input = input("\nВведите расширения: ").strip()
        if not user_input:
            return

        new_exts = [ext.strip() for ext in user_input.split(',') if ext.strip()]
        file_types = self.config.get("file_types", [".py"])

        for ext in new_exts:
            if not ext.startswith('.'):
                ext = '.' + ext

            if ext not in file_types:
                file_types.append(ext)
                print(f"Добавлено: {ext}")
            else:
                print(f"Уже существует: {ext}")

        self.config["file_types"] = file_types
        self.save_config()

    def remove_file_type(self):
        file_types = self.config.get("file_types", [".py"])
        if not file_types:
            print("Список типов файлов пуст")
            return

        print("Введите номер типа файла для удаления (можно несколько через запятую):")
        try:
            nums = input("Номера: ").strip()
            if not nums:
                return

            indices = [int(n.strip()) - 1 for n in nums.split(',')]
            indices.sort(reverse=True)

            removed_count = 0
            for idx in indices:
                if 0 <= idx < len(file_types):
                    removed = file_types.pop(idx)
                    print(f"Удалено: {removed}")
                    removed_count += 1
                else:
                    print(f"Неверный номер: {idx + 1}")

            if removed_count > 0:
                self.config["file_types"] = file_types
                self.save_config()

        except ValueError:
            print("Ошибка: введите номера цифрами")

    def reset_file_types(self):
        default = [".py", ".html", ".css", ".js", ".json", ".txt", ".md"]
        self.config["file_types"] = default.copy()
        self.save_config()
        print("Типы файлов сброшены к значениям по умолчанию")

    def reset_exceptions(self):
        default = [".venv", "__pycache__", ".git", "pyparser.py", "pyparser_config.json"] + self.output_files
        self.config["excluded"] = default.copy()
        self.save_config()
        print("Исключения сброшены к значениям по умолчанию")
        self.ensure_gitignore()

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print("Конфигурация сохранена")

    def collect_selected_files(self):
        print("\nВведите названия файлов (через запятую):")
        print("Можно указывать с расширением или без")
        user_input = input("Файлы: ").strip()
        if not user_input:
            print("Не указаны файлы")
            return

        file_names = [name.strip() for name in user_input.split(',') if name.strip()]
        file_types = self.config.get("file_types", [".py"])

        all_files, _ = self.find_files_by_types(".", file_types)

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
                        if not content.endswith('\n'):
                            out_f.write('\n')
                        out_f.write("\n")

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

            if not items:
                return

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
        print("1. Собрать все файлы в txt (code.txt)")
        print("2. Управление исключениями")
        print("3. Собрать выбранные файлы в txt (choosen_code.txt)")
        print("4. Создать структуру проекта в txt (structure.txt)")
        print("5. Управление типами файлов")
        print("6. Выход")
        return input("\nВыберите действие (1-6): ").strip()

    def main_loop(self):
        while True:
            try:
                choice = self.show_menu()

                if choice == "1":
                    self.collect_all_files()
                elif choice == "2":
                    self.manage_exceptions()
                elif choice == "3":
                    self.collect_selected_files()
                elif choice == "4":
                    self.generate_structure()
                elif choice == "5":
                    self.manage_file_types()
                elif choice == "6":
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