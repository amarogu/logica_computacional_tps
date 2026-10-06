# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.23.3",
#     "ortools>=9.0.0",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import io
    import random
    from contextlib import redirect_stdout

    import marimo as mo
    from ortools.sat.python import cp_model

    return cp_model, io, mo, random, redirect_stdout


@app.cell
def _(mo):
    mo.md(r"""
    # Sudoku Genérico como CSP

    Neste trabalho, o Sudoku $n^2 \times n^2$ é modelado como um
    **problema de satisfação de restrições (CSP)**.

    Linhas, colunas e blocos têm todos a mesma regra — *"os valores têm de ser
    todos diferentes"* — e só muda o conjunto de células a que ela se aplica.
    Por isso, usamos uma classe genérica (`box`) para representar um grupo de
    células e construímos tudo a partir dela.

    **Resolução:** usámos o **CP-SAT do OR-Tools**, que tem `AddAllDifferent` e
    é a ferramenta sugerida na disciplina.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Uso de LLMs

        Neste trabalho, a inteligência artificial foi utilizada para auxiliar na construção do código, fornecendo feedback da nossa implementação, corrigindo e
        explicando erros, sugerindo melhorias, criando código para fins de apresentação, criando alguns testes unitários para validar nossa solução e fornecendo explicações sobre conceitos de programação e lógica computacional. No entanto, todas as decisões finais de design e implementação foram
        feitas pelos autores do trabalho, garantindo a originalidade e a integridade do código apresentado.

        https://share.gemini.google/t2JGmho9KtrN

        https://claude.ai/share/5bed2586-b4fc-43a8-947a-c37800a59d80
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Estruturas

    | Classe | Para que serve |
    |---|---|
    | `box` | Grupo genérico de células: guarda `(linha, coluna) -> valor` (`None` = livre) |
    | `cube(n, i, j)` | Bloco $n \times n$ na posição $(i, j)$ |
    | `path(n, start, end)` | Trecho reto de células (usado para linhas e colunas) |
    | `XSudoku(n)` | Extensão: as duas diagonais como grupos |
    | `pistas_aleatorias(n, k)` | `box` com $k$ pistas em células distintas |
    | `Modelo(n)` | Uma variável por célula, restrições e `resolver()` |
    """)
    return


@app.cell
def _(cp_model, random):
    class box:
        def __init__(self, n, cells=None):
            self.n = n
            self.coords = cells if cells is not None else {}

        def checaLimites(self, i, j):
            if i < 0 or i >= self.n**2 or j < 0 or j >= self.n**2:
                raise ValueError(f"Coordenadas fora da grelha: ({i}, {j})")

        def add(self, i, j, val=None):
            self.checaLimites(i, j)
            if val is not None and not (1 <= val <= self.n**2):
                raise ValueError(f"Valor fora de [1, {self.n**2}]: {val}")
            self.coords[(i, j)] = val

        def matriz(self):

            grid = [[0 for _ in range(self.n**2)] for _ in range(self.n**2)]

            for i in range(self.n**2):
                for j in range(self.n**2):
                    grid[i][j] = self.coords.get((i, j), 0)
                print(*grid[i])

    class cube(box):
        def __init__(self, n, i, j):
            super().__init__(n)
            self.n = n
            self.coords = {(i * n + a, j * n + b): None for a in range(n) for b in range(n)}

    class path(box):

        def __init__(self, n, start, end):
            self.n = n
            a1, b1 = start
            a2, b2 = end
            if(a1 < 0 or a2 >= n**2 or b1 < 0 or b2 >= n**2):
                raise ValueError(f"Coordenadas inválidas: ({a1},{b1}), ({a2},{b2})")
            if(a1 > a2 or b1 > b2):
                self.coords = {(i,j) : None for i in range(a2, a1+1) for j in range(b2, b1+1)}
            else:
                self.coords = {(i,j) : None for i in range(a1, a2+1) for j in range(b1, b2+1)}

    class XSudoku(box):
        def __init__(self, n):
            super().__init__(n)
            N = n**2
            self.diagonalPrincipal = [box(n, {(i, i): None for i in range(N)})]
            self.diagonalSecundaria = [box(n, {(i, N - 1 - i): None for i in range(N)})]

    def pistas_aleatorias(n, k=None):

        if k is not None and (k < 0 or k > n**4):
            raise ValueError(f"Valor de k inválido: {k}")

        N = n**2
        rng = random.Random()

        if k is not None:
            k = k
        else:
            k = n
        celulas = rng.sample([(i, j) for i in range(N) for j in range(N)], k)
        valores = rng.choices(range(1, N + 1), k=k)
        return box(n, dict(zip(celulas, valores)))

    class Modelo:

        def __init__(self, n):

            self.n = n
            self.N = n**2
            self.m = cp_model.CpModel()

            self.x = {
                (i, j): self.m.NewIntVar(1,self.N, f"x_{i}_{j}")
                for i in range(self.N) for j in range(self.N)
            }

        def adicionar(self, *grupos, XS:bool=False):
            for grupo in grupos:
                if isinstance(grupo, XSudoku):
                    if XS:
                        for diagonal in grupo.diagonalPrincipal + grupo.diagonalSecundaria:
                            vars_diagonal = [self.x[i, j] for i, j in diagonal.coords]
                            self.m.AddAllDifferent(vars_diagonal)
                    continue

                vars_do_grupo = [self.x[i, j] for (i, j) in grupo.coords.keys()] #retorna as variáveis de cada célula do grupo
                if isinstance(grupo, (path, cube)):
                    self.m.AddAllDifferent(vars_do_grupo)  #impoe que todas as variáveis do grupo sejam diferentes para o solver

                for (i, j), val in grupo.coords.items():
                    if val is not None:
                        self.m.Add(self.x[i, j] == val)  #Se nao é nula, diz ao solver que a variável não é livre, e sim fixa ao valor val

        def resolver(self):
            solver = cp_model.CpSolver()
            status = solver.Solve(self.m)

            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                return [[solver.Value(self.x[i, j]) for j in range(self.N)] for i in range(self.N)]
            else:
                return None

    return Modelo, XSudoku, cube, path, pistas_aleatorias


@app.cell
def _():
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

    return construir_grelha_inicial, exibe_sudoku


@app.cell
def _(mo):
    mo.md(r"""
    ## Montar e resolver

    São reunidas todas as linhas, colunas e blocos, mais um grupo de pistas
    aleatórias (e as diagonais, quando `XS=True`).

    As pistas são geradas ao acaso, por isso podem ser **contraditórias**.
    Quando isso acontece o modelo não tem solução, e o programa gera novas
    pistas até obter um puzzle resolúvel.
    """)
    return


@app.cell
def _(
    Modelo,
    XSudoku,
    construir_grelha_inicial,
    cube,
    path,
    pistas_aleatorias,
):
    def gerar_e_resolver(n=3, k=10, incluir_diagonais=False):
        N = n**2

        while True:
            modelo = Modelo(n)
            grupos = []

            # Linhas e colunas
            for i in range(N):
                grupos.append(path(n, (i, 0), (i, N - 1)))
                grupos.append(path(n, (0, i), (N - 1, i)))

            # Blocos
            for i in range(n):
                for j in range(n):
                    grupos.append(cube(n, i, j))

            grupos.append(XSudoku(n))
            grupos.append(pistas_aleatorias(n, k=k))

            modelo.adicionar(*grupos, XS=incluir_diagonais)
            solucao = modelo.resolver()

            if solucao is not None:
                return construir_grelha_inicial(n, *grupos), solucao

    return (gerar_e_resolver,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Antes e depois

    Escolhe o tipo de Sudoku e o número de pistas; o botão gera um novo puzzle.
    """)
    return


@app.cell
def _(mo):
    tipo = mo.ui.radio(
        options=["Sudoku normal", "X-Sudoku"],
        value="Sudoku normal",
        label="Tipo",
        inline=True,
    )
    pistas = mo.ui.slider(5, 14, value=10, label="Pistas (k)")
    novo = mo.ui.run_button(label="Novo puzzle")

    mo.hstack([tipo, pistas, novo], justify="start", gap=2)
    return novo, pistas, tipo


@app.cell
def _(
    exibe_sudoku,
    gerar_e_resolver,
    io,
    mo,
    novo,
    pistas,
    redirect_stdout,
    tipo,
):
    novo.value  # volta a executar a célula quando o botão é clicado

    _n = 3
    _inicial, _solucao = gerar_e_resolver(
        n=_n,
        k=pistas.value,
        incluir_diagonais=(tipo.value == "X-Sudoku"),
    )

    _blocos = []
    for _titulo, _grelha in [("ANTES", _inicial), ("DEPOIS", _solucao)]:
        _buf = io.StringIO()
        with redirect_stdout(_buf):
            exibe_sudoku(_grelha, _n, titulo=f"{tipo.value} — {_titulo}")
        _blocos.append(mo.md(f"```\n{_buf.getvalue()}\n```"))

    mo.hstack(_blocos, justify="start", gap=4)
    return


if __name__ == "__main__":
    app.run()
