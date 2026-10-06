def exibe_sudoku(grelha, n, titulo="SUDOKU"):
    """
    Exibe a grelha do Sudoku formatada no terminal.
    `grelha`: matriz n^2 x n^2 (com inteiros ou 0/None para células vazias)
    `n`: dimensão dos blocos (ex: n=3 para Sudoku 9x9)
    """
    if grelha is None:
        print(f"\n{titulo}: Sem solução!")  
        return

    N = n ** 2
    largura_num = len(str(N))
    linha_divisoria = "+" + "+".join(["-" * (n * (largura_num + 1) + 1)] * n) + "+"

    print(f"\n=== {titulo} ===")
    print(linha_divisoria)
    for i in range(N):
        linha_str = "| "
        for j in range(N):
            val = grelha[i][j]
            # Exibe '.' caso a célula esteja vazia (0 ou None)
            str_val = str(val) if val not in (0, None) else "."
            linha_str += f"{str_val:>{largura_num}} "
            
            if (j + 1) % n == 0:
                linha_str += "| "
        print(linha_str)

        if (i + 1) % n == 0:
            print(linha_divisoria)

def construir_grelha_inicial(n, *grupos):
    """
    Cria uma matriz N x N com os valores fixos de todos os grupos fornecidos.
    """
    N = n ** 2
    grelha_inicial = [[0 for _ in range(N)] for _ in range(N)]
    
    for grupo in grupos:
        for (i, j), val in grupo.coords.items():
            if val is not None:
                grelha_inicial[i][j] = val
                
    return grelha_inicial