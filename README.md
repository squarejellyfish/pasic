---
geometry: margin=20mm
---

# Pasic

Basic-ish language in Python implemented from scratch. Compiled to x86_64 native instruction set.

## Usage

```bash
python pasic.py <input_file>
```

**NOTE**: might want to `pip install -r requirements.txt` first

## Milestones

- Compiled to native x86_64
- Generate AST and XML
- Error reporting on syntax and (some) logical error

## Examples

Hello, world:

```python
print("hello, world!")
```

Printing from 1 to 99:

```python
let x = 1
while x < 100 do
    print(x)
    x = x + 1
end
```
