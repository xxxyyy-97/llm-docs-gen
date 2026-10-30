# llm-docs-gen
Генератор markdown-документации для LLM из декларативного docs.yml.
## Установка
```bash
uv add --editable ~/projects/llm-docs-gen
# Или через PyPI (когда будет опубликован):
uv add llm-docs-gen
```
## Быстрый старт
1. Создайте файл docs/docs.yml в корне вашего проекта:
```yaml
version: "1.0"
project:
  title: Мой проект
  path: ~/projects/my-app
  docs: docs
  items:
    - item: structure
      render: 99
      file: PROJECT_TREE.md
      description: |
        Структура проекта.
      content:
        - cmd: tree
          args:
            - flag: a
            - flag: I
              value: '.venv|.git|node_modules'
          title: Дерево файлов

    - item: config
      render: 10
      file: CONFIGURATION.md
      description: |
        Конфигурация приложения.
      content:
        - cmd: cat
          args: pyproject.toml
          title: Зависимости
        - cmd: cat
          args: .env.example
          title: Переменные окружения
```
2. Запустите генератор:
```bash
uv run llm-docs-gen --config docs/docs.yml
```
Результат — файлы docs/PROJECT_TREE.md и docs/CONFIGURATION.md, готовые к скармливанию LLM.
## Формат docs.yml
### Корневые поля

|Поле    |Тип    |Описание   |
|--------|-------|-----------|
|version |string |Версия конфига (опционально)|
|project |object |Основная секция конфигурации|

### Секция project

| Поле | Тип            | Обязательное | Описание |
|------|----------------|--------------|----------|
| title| string         | Да           | Название проекта |
| path | string         | Да           | Абсолютный или относительный путь к корню проекта. Поддерживает `~` |
| docs | string         | Да           | Имя поддиректории для вывода `.md` файлов |
| items| list[object]   | Нет          | Список документов для генерации |

### Элемент items[]
Каждый элемент описывает один выходной .md файл.
| Поле          | Тип           | Обязательное  | Описание |
|---------------|---------------|---------------|----------|
| item          | string        | Да            | Внутренний идентификатор блока |
| render        | int           | Да            | Порядок генерации (по возрастанию). Позволяет ссылаться на будущие файлы в `description` |
| file          | string        | Да            | Имя выходного файла (например, `INFRASTRUCTURE.md`) |
| description   | string        | Нет           | Текст шапки документа. Используйте `|` вместо `>` для сохранения переносов строк |
| content       | list[object]  | Нет           | Список команд, вывод которых попадёт в файл |

### Элемент content[]
Описывает одну команду, результат которой вставляется в документ.
| Поле  | Тип               | Обязательное  | Описание |
|-------|-------------------|---------------|----------|
| cmd   | string            | Да            | Команда для выполнения (`cat`, `tree`, `ls`, любая shell-утилита) |
| args  | list or string    | Нет           | Аргументы команды. Либо список объектов `{flag: ..., value: ...}`, либо строка/список строк |
| title | string            | Нет           | Заголовок блока (`## Title`). Если не указан — используется путь из аргументов |

### Форматы args

```yaml
args: docker-compose.yml        # строка
args: [file1.yml, file2.yml]    # Список строк
args:                           # Список флагов и значений
  - flag: a                     # → -a
  - flag: I                     # → -I
    value: 'venv|.git'          # → venv|.git
```
## Примеры использования
### Инфраструктура Docker
```yaml
- item: infrastructure
  render: 10
  file: INFRASTRUCTURE.md
  description: |
    Инфраструктура контейнеров.
  content:
    - cmd: cat
      args: docker-compose.yml
      title: Композиция сервисов
    - cmd: cat
      args: docker/Dockerfile.app
      title: Образ приложения
    - cmd: cat
      args: docker/.env
      title: Переменные окружения
```
### Артефакты сборки
```yaml
- item: artefacts
  render: 20
  file: ARTEFACTS.md
  description: |
    Конфигурация зависимостей и метаданные проекта.
  content:
    - cmd: cat
      args: pyproject.toml
      title: UV / Poetry конфиг
    - cmd: cat
      args: uv.lock
      title: Lock-файл
    - cmd: cat
      args: ~/.config/app/settings.yaml
      title: Глобальные настройки
```

### Полное дерево проекта
```yaml
- item: project_tree
  render: 99
  file: PROJECT_TREE.md
  description: |
    Актуальная структура репозитория.
  content:
    - cmd: tree
      args:
        - flag: a
        - flag: I
          value: '.venv|.git|__pycache__|node_modules|dist'
      title: Дерево файлов
```
## CLI
|Флаг        |Короткий  |Описание   |
|-----------|-----------|-----------|
| --config  | -c        | Путь к docs.yml (по умолчанию docs.yml)|
| --verbose | -v        | Включить DEBUG-логи в stderr|

### Поведение при ошибках
- Отсутствующий файл: команда завершится ошибкой, но генерация продолжится. В .md будет записано сообщение об ошибке.
- Недоступная команда: аналогично — блок пропустится с пометкой ОШИБКА ВЫПОЛНЕНИЯ КОМАНДЫ.
- Пустой content: создастся файл только с шапкой (path + description).

### Использование как Python-модуля
```python
from pathlib import Path
from llm_docs_gen.config import DocsConfig, ProjectConfig
from llm_docs_gen.renderer import generate_all

cfg = DocsConfig.load(Path("docs/docs.yml"))
proj = ProjectConfig(**cfg.project)
files = generate_all(proj)

for f in files:
    print(f"Generated: {f.resolve()}")
```    
