# Documentation: `generate` Command for `app_manifest_cli`

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/borislavr/qubership-app-manifest-cli.git
cd qubership-app-manifest-cli
```

2. **Create venv**
```bash
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r pyproject.toml
```

4. **Install the package:**
```bash
pip install .
```

## Using the `generate` Command

The `generate` command creates an application manifest based on a [configuration file](./example/jaeger/qubership-jaeger-am-build.yaml) and, if needed, [additional component files](./example/jaeger/).

### Syntax

```bash
python -m venv venv
source venv/bin/activate
app-manifest generate --config CONFIG_PATH [--name NAME] [--version VERSION] [--out OUT_FILE] [COMPONENTS_FILES ...]
```

- `--config`, `-c` — path to a YAML/JSON configuration file (required).
- `--name`, `-n` — application name (defaults to value from config).
- `--version`, `-v` — application version (defaults to value from config).
- `--out`, `-o` — output file name (generated automatically by default).
- `[COMPONENTS_FILES ...]` — (optional) list of paths to JSON component files.

### Examples

**Minimal example:**
```bash
python -m app_manifest_cli generate --config ./myapp-config.yaml
```

**With name, version, and output file:**
```bash
python -m app_manifest_cli generate --config ./myapp-config.yaml --name my-app --version 2.0.1 --out manifest.json
```

**With additional component files:**
```bash
python -m app_manifest_cli generate --config ./myapp-config.yaml comp1.json comp2.json
```

### Notes

- Working with Helm charts requires [Helm](https://helm.sh/) to be installed.
- If name and version are not specified, they will be taken from the configuration file.
- If output file is not specified, it will be created automatically using the template `<name>-<version>.json`.

---

**For help on all commands:**
```bash
python -m app_manifest_cli --help
```
**For help on generate:**
```bash
python -m app_manifest_cli generate --help
```
