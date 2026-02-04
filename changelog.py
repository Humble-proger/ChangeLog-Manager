#!/usr/bin/env python3
"""
CHANGELOG Manager - Улучшенная версия с JSON хранилищем и конфигурацией
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

class ChangelogConfig:
    """Класс для управления конфигурацией"""
    
    DEFAULT_CONFIG = {
        'project': {
            'name': 'Мой Проект',
            'version': '0.0.0',
            'author': '',
            'license': 'MIT'
        },
        'paths': {
            'changelog': 'CHANGELOG.md',  # Относительный путь от корня проекта
            'unreleased': '.changelog/unreleased.json',
            'releases': '.changelog/releases'
        },
        'settings': {
            'auto_backup': True,
            'date_format': '%Y-%m-%d',
            'time_format': '%H:%M:%S',
            'git_integration': False
        }
    }
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / '.changelog'
        self.config_file = self.config_dir / 'config.json'
        
        # Создаем директорию если не существует
        self.config_dir.mkdir(exist_ok=True)
        
        # Загружаем конфигурацию
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Загрузить конфигурацию из файла"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️  Ошибка чтения конфига, создаю новый")
                return self.create_default_config()
        else:
            return self.create_default_config()
    
    def create_default_config(self) -> Dict[str, Any]:
        """Создать конфигурацию по умолчанию"""
        config = self.DEFAULT_CONFIG.copy()
        config['project']['name'] = self.project_root.name
        self.save_config(config)
        return config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """Сохранить конфигурацию в файл"""
        if config is not None:
            self.config = config
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_path(self, key: str) -> Path:
        """Получить абсолютный путь по ключу"""
        if key == 'changelog':
            relative_path = self.config['paths']['changelog']
            return self.project_root / relative_path
        elif key == 'unreleased':
            relative_path = self.config['paths']['unreleased']
            return self.project_root / relative_path
        elif key == 'releases':
            relative_path = self.config['paths']['releases']
            return self.project_root / relative_path
        else:
            raise ValueError(f"Неизвестный ключ пути: {key}")
    
    def update_path(self, key: str, relative_path: str):
        """Обновить путь в конфигурации"""
        if key in self.config['paths']:
            self.config['paths'][key] = relative_path
            self.save_config()
        else:
            raise ValueError(f"Неизвестный ключ пути: {key}")
    
    def update_setting(self, key: str, value: Any):
        """Обновить настройку"""
        if key in self.config['settings']:
            self.config['settings'][key] = value
            self.save_config()
        else:
            raise ValueError(f"Неизвестная настройка: {key}")

class ChangelogManager:
    def __init__(self, config: Optional[ChangelogConfig] = None):
        """
        Инициализация менеджера CHANGELOG
        
        Args:
            config: Конфигурация (если None - создается автоматически)
        """
        self.config = config or ChangelogConfig()
        
        # Поддерживаемые типы изменений
        self.change_types = {
            'added': '### Added',
            'changed': '### Changed',
            'deprecated': '### Deprecated',
            'removed': '### Removed',
            'fixed': '### Fixed',
            'security': '### Security'
        }
        
        # Получаем пути из конфигурации
        self.changelog_file = self.config.get_path('changelog')
        self.unreleased_file = self.config.get_path('unreleased')
        self.releases_dir = self.config.get_path('releases')
        
        # Создаем необходимые директории
        self.unreleased_file.parent.mkdir(parents=True, exist_ok=True)
        self.releases_dir.mkdir(parents=True, exist_ok=True)
    
    def init(self, project_name: Optional[str] = None):
        """
        Инициализировать новый CHANGELOG проект
        
        Args:
            project_name: Название проекта (если None - из конфига)
        """
        if project_name:
            self.config.config['project']['name'] = project_name
            self.config.save_config()
        
        # Создаем начальный CHANGELOG
        content = f"""# Changelog - {self.config.config['project']['name']}

Все значимые изменения в этом проекте документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/),
и проект придерживается [Семантического Версионирования](https://semver.org/).

## [Unreleased]
"""
        self.changelog_file.write_text(content, encoding='utf-8')
        
        # Инициализируем JSON файл невыпущенных изменений
        self._init_unreleased_json()
        
        print(f"✓ CHANGELOG проект инициализирован")
        print(f"  Проект: {self.config.config['project']['name']}")
        print(f"  CHANGELOG: {self.changelog_file}")
        print(f"  Конфиг: {self.config.config_file}")
        print(f"  Невыпущенные: {self.unreleased_file}")
    
    def _init_unreleased_json(self):
        """Инициализировать JSON файл невыпущенных изменений"""
        default_data = {
            'project': self.config.config['project']['name'],
            'created': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'changes': {
                'added': [],
                'changed': [],
                'deprecated': [],
                'removed': [],
                'fixed': [],
                'security': []
            },
            'metadata': {
                'total_changes': 0
            }
        }
        
        self._save_unreleased_json(default_data)
    
    def _load_unreleased_json(self) -> Dict[str, Any]:
        """Загрузить JSON файл невыпущенных изменений"""
        if not self.unreleased_file.exists():
            self._init_unreleased_json()
        
        try:
            with open(self.unreleased_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️  Ошибка чтения JSON, создаю новый файл")
            self._init_unreleased_json()
            return self._load_unreleased_json()
    
    def _save_unreleased_json(self, data: Dict[str, Any]):
        """Сохранить JSON файл невыпущенных изменений"""
        data['last_modified'] = datetime.now().isoformat()
        
        with open(self.unreleased_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add(self, change_type: str, description: str, author: Optional[str] = None):
        """
        Добавить новое изменение в список невыпущенных
        
        Args:
            change_type: Тип изменения
            description: Описание изменения
            author: Автор изменения (опционально)
        
        Returns:
            True если успешно, False если ошибка
        """
        # Проверяем тип изменения
        if change_type not in self.change_types:
            print(f"✗ Неподдерживаемый тип изменения: {change_type}")
            print(f"  Доступные типы: {', '.join(self.change_types.keys())}")
            return False
        
        # Загружаем текущие изменения
        data = self._load_unreleased_json()
        
        # Создаем запись
        change_entry = {
            'id': self._generate_id(),
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'author': author,
            'status': 'pending'
        }
        
        # Добавляем в соответствующую секцию
        if change_type in data['changes']:
            data['changes'][change_type].append(change_entry)
        else:
            # Если тип неизвестен, создаем новую секцию
            data['changes'][change_type] = [change_entry]
        
        # Обновляем метаданные
        data['metadata']['total_changes'] = sum(
            len(changes) for changes in data['changes'].values()
        )
        
        # Сохраняем
        self._save_unreleased_json(data)
        
        print(f"✓ Изменение добавлено: [{change_type}] {description}")
        if author:
            print(f"  Автор: {author}")
        
        return True
    
    def _generate_id(self) -> str:
        """Сгенерировать уникальный ID для изменения"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        return f"chg_{timestamp}"
    
    def show(self, show_all: bool = False, format_output: str = 'pretty'):
        """
        Показать изменения
        
        Args:
            show_all: Показать все изменения, включая выпущенные
            format_output: Формат вывода (pretty, json, markdown)
        """
        if show_all and self.changelog_file.exists():
            print("=" * 60)
            print("ВСЕ ИЗМЕНЕНИЯ (из CHANGELOG.md):")
            print("=" * 60)
            print(self.changelog_file.read_text(encoding='utf-8'))
            print("=" * 60)
        
        # Показываем невыпущенные изменения
        if format_output == 'json':
            data = self._load_unreleased_json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif format_output == 'markdown':
            self._show_unreleased_markdown()
        else:  # pretty
            self._show_unreleased_pretty()
    
    def _show_unreleased_pretty(self):
        """Показать невыпущенные изменения в красивом формате"""
        data = self._load_unreleased_json()
        
        if data['metadata']['total_changes'] == 0:
            print("✓ Нет невыпущенных изменений")
            return
        
        print("\n" + "=" * 60)
        print(f"НЕВЫПУЩЕННЫЕ ИЗМЕНЕНИЯ ({data['metadata']['total_changes']}):")
        print("=" * 60)
        
        for change_type in self.change_types.keys():
            changes = data['changes'].get(change_type, [])
            if changes:
                print(f"\n{self.change_types[change_type]}")
                for i, change in enumerate(changes, 1):
                    line = f"  {i}. {change['description']}"
                    if change.get('author'):
                        line += f" 👤{change['author']}"
                    print(line)
        
        print("=" * 60)
    
    def _show_unreleased_markdown(self):
        """Показать невыпущенные изменения в Markdown формате"""
        data = self._load_unreleased_json()
        
        output = []
        
        for change_type in self.change_types.keys():
            changes = data['changes'].get(change_type, [])
            if changes:
                output.append(f"### {change_type.capitalize()}")
                for change in changes:
                    line = f"- {change['description']}"
                    if change.get('author'):
                        line += f" ({change['author']})"
                    output.append(line)
                output.append("")
        
        if output:
            print("\n".join(output))
        else:
            print("✓ Нет невыпущенных изменений")
    
    def release(self, version: str, release_notes: str = "", tag_git: bool = False):
        """
        Создать новый релиз
        
        Args:
            version: Версия релиза
            release_notes: Заметки о релизе
            tag_git: Создать git tag
        
        Returns:
            True если успешно, False если ошибка
        """
        # Проверяем формат версии
        if version.startswith('v'):
            version_display = version
            version_clean = version[1:]
        else:
            version_display = version
            version_clean = version
        
        # Загружаем невыпущенные изменения
        data = self._load_unreleased_json()
        
        # Проверяем, есть ли изменения
        if data['metadata']['total_changes'] == 0:
            print("✗ Нет невыпущенных изменений для релиза")
            print("  Используйте: chlog add <type> <description>")
            return False
        
        # Создаем релиз в JSON формате
        release_data = {
            'version': version_display,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'release_notes': release_notes,
            'changes': data['changes'].copy(),
            'metadata': {
                'total_changes': data['metadata']['total_changes']
            }
        }
        
        # Сохраняем релиз в отдельный файл
        release_file = self.releases_dir / f"release_{version_clean}.json"
        with open(release_file, 'w', encoding='utf-8') as f:
            json.dump(release_data, f, indent=2, ensure_ascii=False)
        
        # Обновляем CHANGELOG.md
        self._update_changelog_md(version_display, release_notes, data['changes'])
        
        # Очищаем невыпущенные изменения
        self._init_unreleased_json()
        
        # Создаем git tag если нужно
        if tag_git:
            self._create_git_tag(version_display, release_notes)
        
        print(f"✓ Релиз {version_display} успешно создан!")
        print(f"  Дата: {release_data['date']}")
        print(f"  Изменений: {data['metadata']['total_changes']}")
        print(f"  Файл релиза: {release_file}")
        
        return True
    
    def _update_changelog_md(self, version: str, release_notes: str, changes: Dict[str, List]):
        """Обновить CHANGELOG.md файл"""
        # Читаем существующий CHANGELOG
        if self.changelog_file.exists():
            content = self.changelog_file.read_text(encoding='utf-8')
        else:
            content = "# Changelog\n\n## [Unreleased]\n"
        
        # Формируем блок релиза
        today = datetime.now().strftime('%Y-%m-%d')
        release_block = f"\n## [{version}] - {today}\n"
        
        if release_notes:
            release_block += f"\n{release_notes}\n"
        
        # Добавляем изменения
        for change_type in self.change_types.keys():
            if change_type in changes and changes[change_type]:
                release_block += f"\n{self.change_types[change_type]}\n"
                for change in changes[change_type]:
                    line = f"- {change['description']}"
                    if change.get('author'):
                        line += f" ({change['author']})"
                    release_block += f"{line}\n"
        
        # Ищем позицию для вставки (после ## [Unreleased])
        lines = content.splitlines()
        new_lines = []
        inserted = False
        
        for line in lines:
            new_lines.append(line)
            if line.strip() == '## [Unreleased]' and not inserted:
                # Вставляем новый релиз ПОД [Unreleased]
                # Находим конец секции [Unreleased]
                i = len(new_lines) - 1
                while i < len(lines) and not lines[i].strip().startswith('## ['):
                    i += 1
                
                # Вставляем релиз
                new_lines.append(release_block)
                inserted = True
        
        # Если не нашли [Unreleased], добавляем в конец
        if not inserted:
            new_lines.append(release_block)
        
        # Записываем обратно
        self.changelog_file.write_text('\n'.join(new_lines), encoding='utf-8')
    
    def _create_git_tag(self, version: str, message: str):
        """Создать git tag"""
        try:
            import subprocess
            tag_message = f"Release {version}"
            if message:
                tag_message += f": {message}"
            
            subprocess.run(['git', 'tag', '-a', version, '-m', tag_message], 
                         check=True, capture_output=True)
            print(f"✓ Git tag создан: {version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠ Не удалось создать git tag (git не найден или ошибка)")
    
    def stats(self):
        """Показать статистику по изменениям"""
        data = self._load_unreleased_json()
        
        if data['metadata']['total_changes'] == 0:
            print("📊 Нет невыпущенных изменений")
            return
        
        print("📊 Статистика невыпущенных изменений:")
        print("-" * 40)
        
        total = 0
        for change_type in self.change_types.keys():
            count = len(data['changes'].get(change_type, []))
            if count > 0:
                print(f"  {change_type:12}: {count:3d}")
                total += count
        
        print("-" * 40)
        print(f"  Всего      : {total:3d}")
        
        # Статистика по авторам
        authors = {}
        for changes in data['changes'].values():
            for change in changes:
                author = change.get('author')
                if author:
                    authors[author] = authors.get(author, 0) + 1
        
        if authors:
            print("\n👥 Авторы:")
            for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True):
                print(f"  {author:20}: {count:3d}")
    
    def remove(self, change_type: Optional[str] = None, 
               pattern: Optional[str] = None, 
               index: Optional[int] = None):
        """
        Удалить изменение из невыпущенных
        
        Args:
            change_type: Тип изменения
            pattern: Текст для поиска
            index: Номер записи (начиная с 1)
        
        Returns:
            True если успешно, False если ошибка
        """
        data = self._load_unreleased_json()
        
        # Находим изменения для удаления
        changes_to_remove = []
        
        for ctype in self.change_types.keys():
            # Пропускаем если указан тип и он не совпадает
            if change_type and ctype != change_type:
                continue
            
            changes = data['changes'].get(ctype, [])
            for i, change in enumerate(changes):
                match = True
                
                # Проверяем по тексту
                if pattern and pattern.lower() not in change['description'].lower():
                    match = False
                
                # Проверяем по индексу (если указан)
                # Нужно учитывать глобальный индекс
                if index is not None:
                    # Считаем глобальный номер
                    global_idx = 1
                    for ct in self.change_types.keys():
                        if ct == ctype:
                            # Если это наша секция
                            if i == index - 1:
                                break
                            else:
                                match = False
                                break
                        else:
                            global_idx += len(data['changes'].get(ct, []))
                    if global_idx != index:
                        match = False
                
                if match:
                    changes_to_remove.append({
                        'type': ctype,
                        'index': i,
                        'change': change
                    })
        
        if not changes_to_remove:
            print("✗ Не найдено изменений для удаления")
            return False
        
        # Показываем найденные изменения
        print("🔍 Найдены изменения для удаления:")
        for i, item in enumerate(changes_to_remove, 1):
            print(f"  [{i}] [{item['type']}] {item['change']['description']}")
        
        # Подтверждение
        if len(changes_to_remove) == 1:
            confirm = input(f"Удалить это изменение? (y/N): ").lower()
            if confirm != 'y':
                print("❌ Отменено")
                return False
            indices_to_remove = [0]
        else:
            print("\nВыберите действие:")
            print("  1) Удалить все найденные")
            print("  2) Выбрать конкретные")
            print("  3) Отмена")
            
            choice = input("Ваш выбор [1-3]: ").strip()
            
            if choice == '1':
                indices_to_remove = list(range(len(changes_to_remove)))
            elif choice == '2':
                numbers = input("Введите номера через запятую: ").strip()
                selected = [int(n.strip()) - 1 for n in numbers.split(',') 
                          if n.strip().isdigit() and 1 <= int(n.strip()) <= len(changes_to_remove)]
                
                if not selected:
                    print("❌ Неверные номера")
                    return False
                
                indices_to_remove = selected
            else:
                print("❌ Отменено")
                return False
        
        # Удаляем выбранные изменения (с конца к началу для корректности индексов)
        for idx in sorted(indices_to_remove, reverse=True):
            item = changes_to_remove[idx]
            data['changes'][item['type']].pop(item['index'])
            
            # Если секция пустая, удаляем ее
            if not data['changes'][item['type']]:
                del data['changes'][item['type']]
        
        # Обновляем метаданные
        data['metadata']['total_changes'] = sum(
            len(changes) for changes in data['changes'].values()
        )
        
        # Сохраняем
        self._save_unreleased_json(data)
        
        print(f"✅ Удалено {len(indices_to_remove)} изменений")
        return True
    
    def config_show(self):
        """Показать текущую конфигурацию"""
        print("⚙️  Текущая конфигурация:")
        print("=" * 60)
        print(f"Проект: {self.config.config['project']['name']}")
        print(f"Версия: {self.config.config['project']['version']}")
        print(f"Автор: {self.config.config['project']['author']}")
        print("\n📁 Пути:")
        print(f"  CHANGELOG: {self.changelog_file}")
        print(f"  Невыпущенные: {self.unreleased_file}")
        print(f"  Релизы: {self.releases_dir}")
        print("\n⚡ Настройки:")
        for key, value in self.config.config['settings'].items():
            print(f"  {key}: {value}")
        print("=" * 60)
    
    def config_update(self, key: str, value: str):
        """
        Обновить конфигурацию
        
        Args:
            key: Ключ конфигурации (формат: section.key)
            value: Новое значение
        """
        try:
            # Парсим ключ
            if '.' in key:
                section, subkey = key.split('.', 1)
            else:
                section = 'project'
                subkey = key
            
            # Проверяем существование секции
            if section not in self.config.config:
                print(f"✗ Неизвестная секция: {section}")
                return False
            
            # Обновляем значение
            if section == 'paths':
                self.config.update_path(subkey, value)
            elif section == 'settings':
                # Парсим значение в правильный тип
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                
                self.config.update_setting(subkey, value)
            else:
                self.config.config[section][subkey] = value
                self.config.save_config()
            
            print(f"✅ Конфигурация обновлена: {key} = {value}")
            return True
            
        except Exception as e:
            print(f"✗ Ошибка обновления конфигурации: {e}")
            return False

def main():
    """Основная функция CLI"""
    parser = argparse.ArgumentParser(
        description='📝 Улучшенный CHANGELOG Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Инициализация
  chlog init --name "Мой Проект"
  
  # Добавление изменений
  chlog add added "Новая функция"
  chlog add fixed "Исправлен баг" --author "Иван"
  
  # Просмотр
  chlog show
  chlog show --all
  chlog show --format json
  
  # Релиз
  chlog release 1.0.0 --notes "Первый релиз"
  chlog release v2.0.0 --tag
  
  # Удаление
  chlog remove --type added --pattern "тест"
  chlog remove --index 3
  
  # Конфигурация
  chlog config show
  chlog config update paths.changelog "docs/CHANGELOG.md"
  chlog config update settings.auto_backup false
  
  # Статистика
  chlog stats
        """
    )
    
    # Общие аргументы
    parser.add_argument('--config', '-c', 
                       help='Путь к файлу конфигурации')
    
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # Команда init
    init_parser = subparsers.add_parser('init', help='Инициализировать проект')
    init_parser.add_argument('--name', help='Название проекта')
    
    # Команда add
    add_parser = subparsers.add_parser('add', help='Добавить изменение')
    add_parser.add_argument('type', choices=[
        'added', 'changed', 'deprecated', 
        'removed', 'fixed', 'security'
    ], help='Тип изменения')
    add_parser.add_argument('description', help='Описание изменения')
    add_parser.add_argument('--author', help='Автор изменения')
    
    # Команда show
    show_parser = subparsers.add_parser('show', help='Показать изменения')
    show_parser.add_argument('--all', action='store_true', 
                           help='Показать все изменения')
    show_parser.add_argument('--format', choices=['pretty', 'json', 'markdown'],
                           default='pretty', help='Формат вывода')
    
    # Команда release
    release_parser = subparsers.add_parser('release', help='Создать релиз')
    release_parser.add_argument('version', help='Версия релиза')
    release_parser.add_argument('--notes', default='', help='Заметки о релизе')
    release_parser.add_argument('--tag', action='store_true',
                              help='Создать git tag')
    
    # Команда remove
    remove_parser = subparsers.add_parser('remove', help='Удалить изменение')
    remove_parser.add_argument('--type', choices=[
        'added', 'changed', 'deprecated', 
        'removed', 'fixed', 'security'
    ], help='Тип изменения')
    remove_parser.add_argument('--pattern', help='Текст для поиска')
    remove_parser.add_argument('--index', type=int, help='Номер записи')
    
    # Команда stats
    subparsers.add_parser('stats', help='Показать статистику')
    
    # Команда config
    config_parser = subparsers.add_parser('config', help='Управление конфигурацией')
    config_subparsers = config_parser.add_subparsers(dest='config_command')
    config_subparsers.add_parser('show', help='Показать конфигурацию')
    
    config_update = config_subparsers.add_parser('update', help='Обновить конфигурацию')
    config_update.add_argument('key', help='Ключ (например: paths.changelog)')
    config_update.add_argument('value', help='Новое значение')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Инициализируем конфигурацию
        if args.config:
            project_root = Path(args.config).parent
            config = ChangelogConfig(project_root)
        else:
            config = ChangelogConfig()
        
        manager = ChangelogManager(config)
        
        # Выполняем команду
        if args.command == 'init':
            manager.init(args.name)
        
        elif args.command == 'add':
            manager.add(args.type, args.description, args.author)
        
        elif args.command == 'show':
            manager.show(args.all, args.format)
        
        elif args.command == 'release':
            manager.release(args.version, args.notes, args.tag)
        
        elif args.command == 'stats':
            manager.stats()
        
        elif args.command == 'remove':
            manager.remove(args.type, args.pattern, args.index)
        
        elif args.command == 'config':
            if args.config_command == 'show':
                manager.config_show()
            elif args.config_command == 'update':
                manager.config_update(args.key, args.value)
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()