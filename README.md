# ESPHome Components & Packages

A collection of custom [ESPHome](https://esphome.io/) components and YAML packages I use in my own projects.  
This repo is mainly for my personal use, but I’m sharing it to show what’s possible and to document what I’ve built.  
Feel free to explore, borrow ideas, adapt, and even ask questions — but note I don’t provide support for direct third-party use.

---

## Repository Layout

- **`components/`** – Custom ESPHome components written in C++/Python.  
- **`packages/`** – YAML packages that can be included in ESPHome configs.  
- **`examples/`** – Minimal configs showing how to use the above.  

---

## Using the Packages

Include a package in your ESPHome YAML like this:

```yaml
packages:
  my_package: !include packages/my_package.yaml
```

For custom components, copy the component folder into your own ESPHome `components/` directory, then reference it in YAML. See `examples/` for details.

---

## Components

- `components/sensor_x/` — [short description here]
- `components/relay_driver/` — [short description here]

---

## Packages

- `packages/lighting_control.yaml` — [short description here]
- `packages/pool_monitor.yaml` — [short description here]

---

## License

This project is licensed under the [MIT License](LICENSE).
