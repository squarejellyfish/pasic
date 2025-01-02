'program that proves pasic language is turing complete'
#define N 100

let board[N] = [0]
let i = 0
while i < N - 1 do 
    *(board + i * 8) = 0 
    i = i + 1
end
*(board + (N - 1) * 8) = 1

i = 0
while i < N do
    let j = 0
    while j < N do
        if *(board + j * 8) then
            print("*")
        else
            print(" ")
        end
        j = j + 1
    end
    print("\n")

    let pattern = *board
    j = 0
    while j < N - 1 do
        pattern = ((pattern << 1) & 7) | *(board + (j + 1) * 8)
        *(board + j * 8) = (110 >> pattern) & 1
        j = j + 1
    end

    i = i + 1
end
