from sudoku_csp import cube, path, pistas_aleatorias, Modelo, XSudoku
from sudoku_visual import exibe_sudoku, construir_grelha_inicial

# --- CONFIGURAÇÃO ---
n = 3 
N = n ** 2

while(True):
    modelo = Modelo(n)

    # Criar grupos

    grupos = []
    for i in range(N):
        grupos.append(path(n, (i, 0), (i, N - 1)))
        grupos.append(path(n, (0, i), (N - 1, i)))

    for i in range(n):
        for j in range(n):
            grupos.append(cube(n, i, j))

    grupos.append(XSudoku(n))

    # adicionar pistas aleatórias
    pistas = pistas_aleatorias(n, k=10)
    grupos.append(pistas)

    # adicionar todos os grupos ao modelo (parametro XS=True para ativar restrições de Sudoku X)
    modelo.adicionar(*grupos, XS=True)

    # Exibir antes de resolver
    grelha_inicial = construir_grelha_inicial(n, *grupos)


    solucao = modelo.resolver()

    if solucao is not None:
        break

exibe_sudoku(grelha_inicial, n, titulo="ESTADO INICIAL (PISTAS)")
exibe_sudoku(solucao, n, titulo="SOLUÇÃO FINAL")