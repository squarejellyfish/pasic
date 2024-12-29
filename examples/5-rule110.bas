'program that proves pasic language is turing complete'
let N = 60

let char = "* "
let board = 1

let i = 0
while i < N do
    let j = 0
    while j < N do
        if (board >> (N - j - 1)) & 1 then
            write(char, 1) 
        else
            write(char + 1, 1) 
        end
        j = j + 1
    end
    print("")

    let nboard = 0
    let j = N - 1
    while j >= 0 do
        let left = (board >> (j + 1)) & 1
        if j == N - 1 then 
            left = 0 
        end
        let center = (board >> j) & 1
        let right = (board >> (j - 1)) & 1
        if j == 0 then 
            right = 0 
        end

        let pat = (left << 2) | (center << 1) | right

        if (110 >> pat) & 1 then
            nboard = nboard | (1 << j)
        end

        j = j - 1
    end

    board = nboard
    i = i + 1
end
