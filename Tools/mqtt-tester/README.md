# MQTT Tester

A small standalone MQTT Explorer-like tool: connect to any broker, subscribe to a
topic filter (default `#`), browse received topics in a tree, inspect each
payload as raw text or a JSON tree, save a payload to a file, and publish
test messages (with QoS/retain).

Self-contained — no dependency on the rest of the DataHub project.

## Run

```
python main.py
```

Requires `PySide6` and `paho-mqtt` (see `requirements.txt`; already present in
the DataHub project venv).
