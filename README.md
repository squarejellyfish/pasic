# Pasic

Basic-ish language in Python implemented from scratch. Compiled to x86_64 native instruction set.

Heavily inspired by [Rexim @TsodingDaily](https://www.youtube.com/@TsodingDaily) 

## Usage

```bash
python pasic.py <input_file>
```

## Milestones

- [x] Compiled to native x86_64
- [x] Generate AST
- [x] Error reporting on syntax and (some) logical error
- [x] Turing Complete (check `./tests/5-rule110.pasic`)
- [x] Simulate Game of Life (check `./examples/gol.pasic`)

## Examples

### Hello, world

```basic
print("hello, world!")
```

### Variables

```basic
let x = 1
let s = "string is pointer"

print(x)
print(s)

x = 69
print(x)
print("variables re-assignment")
```

### Arithmetics

```basic
let x = (12 + 8) * 3 - 20 / 4

print(x) ' 55
```

### Bitwise Operation

```basic
print(1 << 4) ' 16
print(16 >> 2) ' 4
print(1024 | 1) ' 1025
print(1025 ^ 1) ' 1024
print(1025 & 1) ' 1
```

### Condition and Loops

```basic
let x = 1

if x == 1 then
    print("x is 1")
else
    print("x is not 1")
end

if x > 0 then
    print("x greater than 0")
else if x < 100 then
    print("else if")
end

if x then
    print("ident expression will also evaluate")
end

x = 100
while x do ' only while loop for now
    print(x)
    x = x - 1
end
```

Printing from 1 to 99:

```basic
let x = 1
while x < 100 do
    print(x)
    x = x + 1
end
```

### Macros

```basic
macro x 10 end

print(x) // 10

macro print_something(arg)
    print("in macro")
    print(arg)
end

print_something(" hello\n") // in macro hello\n
```

### Functions

```basic
func add(a, b)
    return a + b
end

print(add(1, 2)) // 3
```
