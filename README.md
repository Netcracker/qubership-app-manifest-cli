# Документация: Команда `generate` для `app_manifest_cli`

## Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/borislavr/qubership-app-manifest-cli.git
cd qubership-app-manifest-cli
```

2. **Создайте venv**
```bash
python -m venv venv
source venv/bin/activate
```

3. **Установите зависимости:**
```bash
pip install -r pyproject.toml
```

4. **Установите пакет:**
```bash
pip install .
```

## Использование команды `generate`

Команда `generate` формирует манифест приложения на основе [конфигурационного файла](./example/jaeger/qubership-jaeger-am-build.yaml) и, при необходимости, [дополнительных файлов компонентов](./example/jaeger/).

### Синтаксис

```bash
python -m venv venv
source venv/bin/activate
app-manifest generate --config CONFIG_PATH [--name NAME] [--version VERSION] [--out OUT_FILE] [COMPONENTS_FILES ...]
```

- `--config`, `-c` — путь к YAML/JSON конфигурационному файлу (обязательно).
- `--name`, `-n` — имя приложения (по умолчанию берётся из конфига).
- `--version`, `-v` — версия приложения (по умолчанию берётся из конфига).
- `--out`, `-o` — имя выходного файла (по умолчанию формируется автоматически).
- `[COMPONENTS_FILES ...]` — (необязательно) список путей к JSON-файлам компонентов.

### Примеры

**Минимальный пример:**
```bash
python -m app_manifest_cli generate --config ./myapp-config.yaml
```

**С указанием имени, версии и выходного файла:**
```bash
python -m app_manifest_cli generate --config ./myapp-config.yaml --name my-app --version 2.0.1 --out manifest.json
```

**С дополнительными файлами компонентов:**
```bash
python -m app_manifest_cli generate --config ./myapp-config.yaml comp1.json comp2.json
```

### Примечания

- Для работы с helm-чартами требуется установленный [Helm](https://helm.sh/).
- Если не указать имя и версию, они будут взяты из конфигурационного файла.
- Если не указать выходной файл, он будет создан автоматически по шаблону `<name>-<version>.json`.

---

**Для справки по всем командам:**
```bash
python -m app_manifest_cli --help
```
**Для справки по generate:**
```bash
python -m app_manifest_cli generate --help
```
