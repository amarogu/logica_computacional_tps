import sudoku_csp as s

b = s.box({
    (0, 0): 1,
    (1, 1): 2,
    (0, 1): 3,
    (1, 0): 4
})


s.pistas_aleatorias(3, 9)

