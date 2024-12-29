let x = 1

if x == 1 then
    print("x is 1\n")
else
    print("x is not 1\n")
end

if x > 0 then
    print("x greater than 0\n")
else if x < 100 then
    print("else if\n")
end

if x then
    print("ident expression will also evaluate\n")
end

x = 10
while x do ' only while loop for now
    print(x)
    x = x - 1
end
