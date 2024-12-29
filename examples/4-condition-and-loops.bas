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
