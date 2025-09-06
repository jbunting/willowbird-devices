# <Package Name>

Short description of what this package is for (e.g., lighting control, pool monitoring, environment sensor bundle).

---

## Files

- `<package>.yaml` — main package definition

---

## Usage

Include the package in your ESPHome config:

```yaml
packages:
  <package_name>: !include packages/<package_name>.yaml
```

---

## Contents

This package typically sets up:
- Entities (sensors, switches, lights, etc.)
- Automations
- Defaults (names, update intervals, etc.)

---

## Notes

- Hardware assumptions (e.g., requires DHT22 on GPIO4)  
- Any dependencies (other packages, external components)  
- Things to tweak when reusing  
