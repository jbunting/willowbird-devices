# <Component Name>

Short description of what this component does (e.g., custom sensor, actuator, driver).

---

## Files

- `<component>.h` / `<component>.cpp` — core implementation
- `__init__.py` — ESPHome registration (if needed)

---

## Configuration

Example YAML snippet showing how to use the component:

```yaml
esphome:
  name: my_device

external_components:
  - source: github://your-username/esphome-repo
    components: [<component_name>]

<component_name>:
  id: my_component
  option: value
```

List any options here:
- `option1` — what it does  
- `option2` — what it does  

---

## Notes

- Hardware requirements (pins, chips, etc.)  
- Known limitations  
- Any gotchas future-you should remember  
