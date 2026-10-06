from sudoku_csp import cube, path, pistas_aleatorias, Modelo
from sudoku_visual import exibe_sudoku, construir_grelha_inicial

# --- CONFIGURAÇÃO ---
n = 3
N = n ** 2

while(True):
# 1. Instanciar o modelo
    modelo = Modelo(n)

    # 2. Criar linhas e colunas com 'path'
    grupos = []
    for i in range(N):
        grupos.append(path(n, (i, 0), (i, N - 1)))
        grupos.append(path(n, (0, i), (N - 1, i)))

    # 3. Criar blocos com 'cube'
    for i in range(n):
        for j in range(n):
            grupos.append(cube(n, i, j))

    # 4. Gerar e adicionar pistas aleatórias
    pistas = pistas_aleatorias(n, k=10)
    grupos.append(pistas)

    # 5. Adicionar todos os grupos ao modelo
    modelo.adicionar(*grupos)

    # 6. EXIBIR ANTES DE RESOLVER
    grelha_inicial = construir_grelha_inicial(n, *grupos)

    # 7. RESOLVER E EXIBIR DEPOIS
    solucao = modelo.resolver()
    
    if solucao is not None:
        break

exibe_sudoku(grelha_inicial, n, titulo="ESTADO INICIAL (PISTAS)")
exibe_sudoku(solucao, n, titulo="SOLUÇÃO FINAL")