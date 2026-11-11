### Summary

The `vault_lookup` filter returns an empty string instead of raising an error when the vault file cannot be decrypted. Playbooks then continue with an empty secret. This is a synthetic example report for the offline demo.

### Issue Type

Bug Report

### Component Name

lib/exampletool/vault/reader.py

### Exampletool Version

```console
$ exampletool --version
exampletool 3.8.2
  python version = 3.11.4
```

### Configuration

```console
$ exampletool-config dump --only-changed
DEFAULT_VAULT_IDENTITY_LIST(/etc/exampletool.cfg) = ['dev@prompt']
```

### OS / Environment

Debian 12, running from a container image.

### Steps to Reproduce

<!-- Describe exactly how to reproduce the problem. -->

```yaml
- hosts: localhost
  tasks:
    - ansible.builtin.debug:
        msg: "{{ lookup('vault_lookup', 'secrets/db.vault') }}"
```

1. Create `secrets/db.vault` with a different vault password than the one configured.
2. Run the playbook above.
3. Look at the printed message.

### Expected Results

`read_vault()` in `lib/exampletool/vault/reader.py` raises `VaultDecryptError` and the play stops.

### Actual Results

The play continues and prints an empty message. `read_vault()` returns `""` after the decrypt step fails at `reader.py:142`.

### Code of Conduct

- [X] I agree to follow the project's Code of Conduct
