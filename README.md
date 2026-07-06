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

## Manual push (dev / bootstrap)

`scripts/push.sh` wraps ESPHome for local flashing and pulls secrets from
Bitwarden via [`rbw`](https://github.com/doy/rbw). Manual builds are always
*dev* builds (`version=dev`, `auto_update=false`), so a hand-flashed device
never self-updates from the GitHub `latest` release — mainline builds only
come from CI.

```bash
scripts/push.sh secrets                # write devices/secrets.yaml from Bitwarden
scripts/push.sh flash <device> [target]   # compile + upload (USB or OTA)
scripts/push.sh ota <device> <host>       # upload over the network
scripts/push.sh bootstrap <device> [port] # first-time USB flash of a new device
scripts/push.sh logs <device> [target]    # stream logs
```

`<device>` is a config basename (e.g. `bluetooth-proxy`) or a path to a
`.yaml`. `<target>` is a serial port or a network host/IP; omit it to let
ESPHome prompt.

Secrets live in a single Bitwarden item (default name `willowbird-devices`,
override with `WILLOWBIRD_BW_ITEM`) with these custom fields:

- `wifi_ssid`, `wifi_password` — required
- `api_encryption_key`, `ota_password` — optional (written only if present)

---

## License

This project is licensed under the [MIT License](LICENSE).
