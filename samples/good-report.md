# Crash when parsing empty config file

## Description
Starting the CLI with a zero-byte `config.yaml` crashes instead of falling back to defaults.

## Steps to reproduce
1. Run `touch config.yaml`
2. Run `mytool --config config.yaml build`
3. Observe the traceback

## Expected behavior
The tool prints a warning and uses the default configuration.

## Actual behavior
The tool exits with `TypeError: 'NoneType' object is not iterable` raised in `src/mytool/config.py:88`, inside `load_config()`.

## Environment
- mytool v2.4.1
- Python 3.11.4
- Ubuntu 22.04
