# llm-docs-gen

Генератор markdown-документации для LLM из декларативного `docs.yml`.

Поддерживает выполнение shell-команд, генерацию таблиц, вставку статического текста и алертов (GitHub-style). 
Автоматически определяет язык подсветки кода по расширению файла.
## Установка (если в проекте есть uv)
```bash
# Из GitHub
uv add git+https://github.com/xxxyyy-97/llm-docs-gen

# Для разработки (editable, локально)
uv add --editable ~/projects/llm-docs-gen
```

## Быстрый старт
1. Создайте файл `docs/docs.yml` в корне вашего проекта:
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
        # Команда: вывод автоматически определится как toml
        - cmd: cat
          args: pyproject.toml
          title: Зависимости
        
        # Таблица
        - type: table
          title: Сервисы
          headers: ["Name", "Port"]
          rows:
            - ["PostgreSQL", "5432"]
            - ["Airflow", "8080"]

        # Алерт
        - type: alert
          alert: WARNING
          body: Не редактируйте этот файл вручную!
```

2. Запустите генератор:
```bash
cd ~/projects/llm-docs-gen
# генерация документации в текущем проекте
uv run llm-docs-gen --config docs/docs.yml

# генерация документации в другом проекте
uv run llm-docs-gen --config ~/projects/pg-cdc/docs/docs.yml
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
Универсальный блок контента. Тип определяется полем type (по умолчанию command).

#### Общие поля (для всех типов)
| Поле          | Тип       | По умолчанию  | Описание |
|---------------|-----------|---------------|----------|
| type          | string    | "command"     | Тип блока: command, table, text, alert |
| title         | string    | —             | Заголовок блока. Если не указан, используется дефолтное название или путь |
| title_level   | int       | 2             | Уровень заголовка Markdown (1=#, 2=##, ... 6=######) |

#### Тип `command` (выполнение shell-команды)
| Поле  | Тип           | Обязательное  | Описание |
|-------|---------------|---------------|----------|
| cmd   | string        | Да            | Команда (cat, tree, awk, любая утилита) |
| args  | list/string   | Нет           | Аргументы команды |
| lang  | string        | "bash"        | Язык блока вывода. Если не задан явно и команда cat, определяется автоматически по расширению файла |

#### Форматы `args`

```yaml
args: docker-compose.yml        # строка
args: [file1.yml, file2.yml]    # Список строк
args:                           # Список флагов и значений
  - flag: a                     # → -a
  - flag: I                     # → -I
    value: 'venv|.git'          # → venv|.git
```

#### Автоопределение языка (`lang`):
Если lang не указан (или равен bash) и команда cat, генератор смотрит на расширение первого аргумента:
- .yml, .yaml → yaml
- .json → json
- .toml → toml
- .sql → sql
- .py → python
- .sh → bash
- Dockerfile* → dockerfile
- Остальное → bash (или значение lang, если задано явно)
Явно указанный lang всегда имеет приоритет над автоопределением.

#### Тип `table` (Markdown-таблица)
| Поле      | Тип               | Обязательное  | Описание |
|-----------|-------------------|---------------|----------|
| headers   | list[str]         | Да            | Заголовки колонок |
| rows      | list[list[str]]   | Да            | Данные строк. Длина каждой строки должна совпадать с количеством заголовков |

#### Тип `text` (статический текст)
| Поле  | Тип       | Обязательное  | Описание  |
|-------|-----------|---------------|-----------|
| body  | string    | Да            | Текст блока. Поддерживает любой Markdown (списки, ссылки, форматирование) |

#### Тип `alert` (предупреждение GitHub-style)
| Поле  | Тип       | Обязательное  | Описание |
|-------|-----------|---------------|----------|
| alert | string    | "NOTE"        | Вид алерта: NOTE, TIP, IMPORTANT, WARNING, CAUTION |
| body  | string    | Да            | Текст предупреждения |
Алерты рендерятся как цитаты > [!KIND]. Если указан title, он выводится заголовком нужного уровня перед цитатой.

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
      args: docker/docker-compose.yml
      title: Композиция сервисов
      # lang определится как yaml автоматически
    - cmd: cat
      args: docker/Dockerfile.app
      title: Образ приложения
      # lang определится как dockerfile автоматически
    - type: alert
      alert: IMPORTANT
      title: Безопасность
      body: |
        Файл `.env` содержит секреты.
        В репозитории хранится только `.env.example`.
```

### Артефакты сборки
```yaml
- item: artefacts
  render: 20
  file: ARTEFACTS.md
  description: Конфигурация зависимостей и метаданные проекта.
  content:
    - cmd: cat
      args: pyproject.toml
      title: UV / Poetry конфиг
      # lang=toml автоматически
    - type: table
      title: Ключевые зависимости
      headers: ["Пакет", "Версия", "Назначение"]
      rows:
        - ["dbt-core", ">=1.8", "Трансформация данных"]
        - ["dbt-postgres", ">=1.8", "Адаптер PostgreSQL"]
        - ["ruamel-yaml", ">=0.18", "Парсинг YAML"]
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
      lang: text  # явно указываем, чтобы не было bash-подсветки для дерева
```

### Статический текст со списками
```yaml
- type: text
  title: Порядок запуска
  title_level: 3
  body: |
    1. Поднять инфраструктуру: `docker compose up -d`
    2. Дождаться healthcheck всех сервисов
    3. Зарегистрировать коннекторы:
       - `./connectors/register.sh create`
       - проверить статус через `register.sh status`
    4. Запустить dbt: `uv run dbt build`
```

## CLI
```bash
llm-docs-gen [--config PATH] [--verbose]
```
|Флаг       |Короткий   |Описание   |
|-----------|-----------|-----------|
| --config  | -c        | Путь к docs.yml (по умолчанию docs.yml)|
| --verbose | -v        | Включить DEBUG-логи в stderr|

### Поведение при ошибках
- `Отсутствующий файл`: команда завершится ошибкой, но генерация продолжится. В .md будет записано сообщение об ошибке внутри блока вывода.
- `Недоступная команда`: аналогично — блок пропустится с пометкой ОШИБКА ВЫПОЛНЕНИЯ КОМАНДЫ.
- `Пустой content`: создастся файл только с шапкой (path + description).
- `Некорректный YAML`: Pydantic выбросит ValidationError до начала генерации с указанием проблемного поля.

### Использование как Python-модуля
```python
from pathlib import Path
from llm_docs_gen.config import DocsConfig, ProjectConfig
from llm_docs_gen.renderer import generate_all

cfg = DocsConfig.load(Path("docs/docs.yml"))
if cfg.project is None:
    raise ValueError("Missing 'project' section")

proj = ProjectConfig(**cfg.project)
files = generate_all(proj)

for f in files:
    print(f"Generated: {f.resolve()} ({f.stat().st_size} bytes)")
```

## Лицензия
MIT
