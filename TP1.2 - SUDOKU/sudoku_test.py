# test_sudoku_csp.py
import pytest
from sudoku_csp import box, cube, path, pistas_aleatorias, Modelo


# ---------- Funções auxiliares ----------

def montar_e_resolver(n, k=None, seed=None):
    """Fluxo completo: pistas -> linhas + colunas + blocos + pistas -> resolver."""
    N = n * n
    pistas = pistas_aleatorias(n, k, seed=seed)

    grupos = [path(n, (i, 0), (i, N - 1)) for i in range(N)]       # linhas
    grupos += [path(n, (0, j), (N - 1, j)) for j in range(N)]      # colunas
    grupos += [cube(n, i, j) for i in range(n) for j in range(n)]  # blocos
    grupos.append(pistas)

    modelo = Modelo(n)
    modelo.adicionar(*grupos)
    return pistas, modelo.resolver()


def resolver_com_pistas_validas(n, tentativas=50):
    """Pistas aleatórias podem ser contraditórias: tenta várias seeds."""
    for seed in range(tentativas):
        pistas, sol = montar_e_resolver(n, seed=seed)
        if sol is not None:
            return pistas, sol
    pytest.fail(f"Nenhum puzzle solúvel em {tentativas} tentativas (n={n})")


def erros_da_grelha(g, n):
    """Devolve a lista de erros encontrados (lista vazia = grelha válida)."""
    N = n * n
    esperado = set(range(1, N + 1))
    erros = []

    if len(g) != N or any(len(linha) != N for linha in g):
        return [f"dimensões diferentes de {N}x{N}"]

    for i in range(N):
        if set(g[i]) != esperado:
            erros.append(f"linha {i} inválida: {g[i]}")

    for j in range(N):
        coluna = [g[i][j] for i in range(N)]
        if set(coluna) != esperado:
            erros.append(f"coluna {j} inválida: {coluna}")

    for bi in range(n):
        for bj in range(n):
            bloco = [g[bi * n + di][bj * n + dj]
                     for di in range(n) for dj in range(n)]
            if set(bloco) != esperado:
                erros.append(f"bloco ({bi},{bj}) inválido: {bloco}")

    return erros


# ---------- Teste do próprio validador ----------

def test_validador_aceita_grelha_correta_e_rejeita_errada():
    boa = [[1, 2, 3, 4],
           [3, 4, 1, 2],
           [2, 1, 4, 3],
           [4, 3, 2, 1]]
    assert erros_da_grelha(boa, 2) == []

    ma = [linha[:] for linha in boa]
    ma[0][0] = 2                       # repete o 2 na primeira linha
    assert erros_da_grelha(ma, 2) != []


# ---------- Requisito 1: linhas, colunas e blocos ----------

@pytest.mark.parametrize("n", [2, 3])
def test_linhas_colunas_blocos_tem_todos_os_valores(n):
    _, sol = resolver_com_pistas_validas(n)
    assert erros_da_grelha(sol, n) == []


# ---------- Requisito 2: pistas mantêm o valor ----------

@pytest.mark.parametrize("n", [2, 3])
def test_pistas_mantem_valor_na_solucao(n):
    pistas, sol = resolver_com_pistas_validas(n)
    assert len(pistas.coords) > 0
    for (i, j), val in pistas.coords.items():
        assert sol[i][j] == val, f"pista ({i},{j})={val} mudou para {sol[i][j]}"


# ---------- Requisito 3: add rejeita entradas inválidas ----------

@pytest.mark.parametrize("n", [2, 3])
@pytest.mark.parametrize("i, j", [(-1, 0), (0, -1), ("N", 0), (0, "N")])
def test_add_rejeita_coordenadas_fora_da_grelha(n, i, j):
    N = n * n
    i = N if i == "N" else i
    j = N if j == "N" else j
    with pytest.raises((IndexError, ValueError)):
        box(n).add(i, j)


@pytest.mark.parametrize("n", [2, 3])
@pytest.mark.parametrize("val", [0, -1, "N+1"])
def test_add_rejeita_valores_fora_do_intervalo(n, val):
    N = n * n
    val = N + 1 if val == "N+1" else val
    with pytest.raises((IndexError, ValueError)):
        box(n).add(0, 0, val)


@pytest.mark.parametrize("n", [2, 3])
def test_add_aceita_limites_validos(n):
    N = n * n
    b = box(n)
    b.add(0, 0, 1)             # canto inicial, valor mínimo
    b.add(N - 1, N - 1, N)     # canto final, valor máximo
    b.add(0, 1)                # célula livre (sem valor)
    assert b.coords[(0, 0)] == 1
    assert b.coords[(N - 1, N - 1)] == N
    assert b.coords[(0, 1)] is None