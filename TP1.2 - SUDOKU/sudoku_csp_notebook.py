# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.24.2",
#     "ortools",
# ]
# ///

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import random

    import marimo as mo
    from ortools.sat.python import cp_model

    return cp_model, mo, random


@app.cell
def _(mo):
    mo.md(r"""
    # Sudoku genérico como CSP

    Linhas, colunas, blocos e pistas são todos o mesmo objeto: um **grupo de
    células com a restrição "todos diferentes"** (`box`). O modelo CSP recebe
    grupos e não quer saber de onde vieram.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## R1 — `box`: grupo genérico de células
    """)
    return


@app.cell
def _():
    class box:
        def __init__(self, n, cells=None):
            self.n = n
            self.coords = {}  # (linha, coluna) -> valor ou None
            for (i, j), val in (cells or {}).items():
                self.add(i, j, val)

        def checaLimites(self, i, j):
            if i < 0 or i >= self.n**2 or j < 0 or j >= self.n**2:
                raise ValueError(f"Coordenadas fora da grelha: ({i}, {j})")

        def add(self, i, j, val=None):
            self.checaLimites(i, j)
            if val is not None and not (1 <= val <= self.n**2):
                raise ValueError(f"Valor fora de [1, {self.n**2}]: {val}")
            self.coords[(i, j)] = val

        def matriz(self):
            N = self.n**2
            return [[self.coords.get((i, j)) or 0 for j in range(N)] for i in range(N)]

    return (box,)


@app.cell
def _(mo):
    mo.md(r"""
    ## R2 e R3 — `cube` (bloco) e `path` (troço reto)
    """)
    return


@app.cell
def _(box):
    class cube(box):
        def __init__(self, n, i, j):
            super().__init__(n)
            for a in range(n):
                for b in range(n):
                    self.add(i * n + a, j * n + b)

    class path(box):
        def __init__(self, n, inicio, fim):
            super().__init__(n)
            a1, b1 = inicio
            a2, b2 = fim
            if a1 != a2 and b1 != b2:
                raise ValueError("O troço tem de ser horizontal ou vertical")
            # passo -1, 0 ou +1 em cada eixo: funciona nos dois sentidos
            di = (a2 > a1) - (a2 < a1)
            dj = (b2 > b1) - (b2 < b1)
            for t in range(max(abs(a2 - a1), abs(b2 - b1)) + 1):
                self.add(a1 + t * di, b1 + t * dj)

    return cube, path


@app.cell
def _(mo):
    mo.md(r"""
    ## R4 — Pistas aleatórias

    Devolve um `box`. Células **e valores** são sorteados sem repetição, porque
    o modelo impõe "todos diferentes" também ao grupo das pistas. Por omissão
    `k = n`.
    """)
    return


@app.cell
def _(box, random):
    def pistas_aleatorias(n, k=None, seed=None):
        N = n**2
        rng = random.Random(seed)
        k = k if k is not None else n
        celulas = rng.sample([(i, j) for i in range(N) for j in range(N)], k)
        valores = rng.sample(range(1, N + 1), k)
        return box(n, dict(zip(celulas, valores)))

    return (pistas_aleatorias,)


@app.cell
def _(mo):
    mo.md(r"""
    ## R5 — Modelo CSP (OR-Tools CP-SAT)

    Uma variável inteira por célula, domínio $[1, n^2]$. `adicionar` impõe
    `AllDifferent` a cada grupo e fixa as células com valor. `resolver`
    devolve a grelha ou `None` se não houver solução.

    **Porquê CP-SAT:** tem `AddAllDifferent` nativo, é a sugestão da disciplina
    e resolve instâncias deste tamanho em milissegundos.
    """)
    return


@app.cell
def _(cp_model):
    class Modelo:
        def __init__(self, n):
            self.n = n
            self.N = n**2
            self.m = cp_model.CpModel()
            self.x = {
                (i, j): self.m.NewIntVar(1, self.N, f"x_{i}_{j}")
                for i in range(self.N)
                for j in range(self.N)
            }

        def adicionar(self, *grupos):
            for grupo in grupos:
                self.m.AddAllDifferent([self.x[c] for c in grupo.coords])
                for c, val in grupo.coords.items():
                    if val is not None:
                        self.m.Add(self.x[c] == val)

        def resolver(self):
            solver = cp_model.CpSolver()
            status = solver.Solve(self.m)
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                return [
                    [solver.Value(self.x[i, j]) for j in range(self.N)]
                    for i in range(self.N)
                ]
            return None

    return (Modelo,)


@app.cell
def _(mo):
    mo.md(r"""
    ## R6 — Sudoku completo

    Linhas + colunas + blocos + pistas aleatórias.

    **Puzzles sem solução:** pistas aleatórias podem ser contraditórias. A
    escolha foi tentar novas pistas (seeds consecutivas) até haver solução, com
    um limite de tentativas. Assim o resultado é sempre um puzzle válido e,
    com uma seed fixa, continua reprodutível.
    """)
    return


@app.cell
def _(Modelo, cube, path, pistas_aleatorias):
    def resolver_sudoku(n, k=None, seed=None, tentativas=100):
        N = n**2
        base = [path(n, (i, 0), (i, N - 1)) for i in range(N)]  # linhas
        base += [path(n, (0, j), (N - 1, j)) for j in range(N)]  # colunas
        base += [cube(n, i, j) for i in range(n) for j in range(n)]  # blocos
        for t in range(tentativas):
            pistas = pistas_aleatorias(n, k, None if seed is None else seed + t)
            modelo = Modelo(n)
            modelo.adicionar(*base, pistas)
            sol = modelo.resolver()
            if sol is not None:
                return pistas, sol, t + 1
        return None, None, tentativas

    return (resolver_sudoku,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Validação
    """)
    return


@app.cell
def _():
    def erros_da_grelha(g, n):
        """Lista de erros (vazia = grelha válida)."""
        N = n**2
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
                bloco = [g[bi * n + di][bj * n + dj] for di in range(n) for dj in range(n)]
                if set(bloco) != esperado:
                    erros.append(f"bloco ({bi},{bj}) inválido: {bloco}")
        return erros

    return (erros_da_grelha,)


@app.cell
def _(box, erros_da_grelha, mo, path, resolver_sudoku):
    def _rejeita(f, *args):
        try:
            f(*args)
        except (ValueError, IndexError):
            return True
        return False

    # o próprio validador tem de distinguir boa de má
    _boa = [[1, 2, 3, 4], [3, 4, 1, 2], [2, 1, 4, 3], [4, 3, 2, 1]]
    _ma = [linha[:] for linha in _boa]
    _ma[0][0] = 2
    assert erros_da_grelha(_boa, 2) == []
    assert erros_da_grelha(_ma, 2) != []

    for _n in (2, 3):
        _N = _n**2

        # add rejeita coordenadas e valores inválidos
        for _i, _j in [(-1, 0), (0, -1), (_N, 0), (0, _N)]:
            assert _rejeita(box(_n).add, _i, _j), f"n={_n}: aceitou ({_i},{_j})"
        for _v in (0, -1, _N + 1):
            assert _rejeita(box(_n).add, 0, 0, _v), f"n={_n}: aceitou valor {_v}"

        # limites válidos são aceites
        _b = box(_n)
        _b.add(0, 0, 1)
        _b.add(_N - 1, _N - 1, _N)
        _b.add(0, 1)
        assert _b.coords == {(0, 0): 1, (_N - 1, _N - 1): _N, (0, 1): None}

        # path nos dois sentidos dá o mesmo conjunto de células
        assert set(path(_n, (0, 0), (0, _N - 1)).coords) == set(
            path(_n, (0, _N - 1), (0, 0)).coords
        )

        # fluxo completo: grelha válida e pistas preservadas
        _pistas, _sol, _ = resolver_sudoku(_n, seed=0)
        assert _sol is not None, f"n={_n}: sem solução"
        assert erros_da_grelha(_sol, _n) == []
        for (_i, _j), _val in _pistas.coords.items():
            assert _sol[_i][_j] == _val

    mo.md("✅ Todos os testes passaram para $n=2$ e $n=3$.")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Demonstração interativa
    """)
    return


@app.cell
def _(mo):
    n_ui = mo.ui.slider(2, 4, value=3, label="n (grelha n²×n²)")
    k_ui = mo.ui.slider(1, 16, value=3, label="nº de pistas")
    seed_ui = mo.ui.number(0, 9999, value=0, label="seed")
    mo.hstack([n_ui, k_ui, seed_ui], justify="start")
    return k_ui, n_ui, seed_ui


@app.cell
def _(erros_da_grelha, k_ui, mo, n_ui, resolver_sudoku, seed_ui):
    _n = n_ui.value
    _N = _n**2
    _pistas, _sol, _tent = resolver_sudoku(_n, min(k_ui.value, _N), seed_ui.value)

    if _sol is None:
        _saida = mo.md("**Sem solução** nas tentativas feitas.")
    else:
        _linhas = []
        for _i in range(_N):
            _tds = []
            for _j in range(_N):
                _e = "width:2em;height:2em;text-align:center;border:1px solid #888;"
                if _j % _n == 0:
                    _e += "border-left:3px solid #666;"
                if _i % _n == 0:
                    _e += "border-top:3px solid #666;"
                if _j == _N - 1:
                    _e += "border-right:3px solid #666;"
                if _i == _N - 1:
                    _e += "border-bottom:3px solid #666;"
                if (_i, _j) in _pistas.coords:
                    _e += "font-weight:bold;background:#ffe9a8;color:#000;"
                _tds.append(f"<td style='{_e}'>{_sol[_i][_j]}</td>")
            _linhas.append("<tr>" + "".join(_tds) + "</tr>")
        _tabela = mo.Html(
            "<table style='border-collapse:collapse'>" + "".join(_linhas) + "</table>"
        )
        _valida = "válida" if erros_da_grelha(_sol, _n) == [] else "INVÁLIDA"
        _saida = mo.vstack(
            [
                _tabela,
                mo.md(f"Grelha **{_valida}** · pistas a amarelo · tentativas: {_tent}"),
            ]
        )
    _saida
    return


if __name__ == "__main__":
    app.run()
