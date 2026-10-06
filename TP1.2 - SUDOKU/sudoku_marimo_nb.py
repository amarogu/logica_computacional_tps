import marimo

__generated_with = "0.25.1"
app = marimo.App()

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Construção de um Gerador/Resolvedor de Sudoku

    # Neste trabalho, foi construído na linguagem python um código que lida com o sudoku como um problema Problema de
    #  Satisfação de Restrições (CSP), definindo variáveis, o domínio e as restrições para que o resolvedor ache uma solução
    #  para o tabuleiro através destes inputs. Usamos o resolvedor da Google CP-SAT por ser o recomendado pelo enunciado, 
    # além de que é eficiente, gratuito e se encaixa no contexto que estamos trabalhando e com os recursos que podemos 
    # fornecer para obter o resultado desejado.
    """)
    return


@app.cell
def _():
    import random
    from ortools.sat.python import cp_model

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

    class cube():
        
            self.n = n
            self.coords = {(i * n + a, j * n + b): None for a in range(n) for b in range(n)}

    class path():

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

    class XSudoku():
        def __init__(self, n):
            N = n**2
            self.diagonais = [path(n, (0, 0), (N - 1, N - 1)),      # principal
                                path(n, (0, N - 1), (N - 1, 0))]      # secundária

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

        def adicionar(self, *grupos):
            for grupo in grupos: 
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
            
    return


@app.cell
def _():

    import pytest
    from sudoku_csp import box, cube, path, pistas_aleatorias, Modelo


    #Funções auxiliares 

    def montar_e_resolver(n, k=None):
        """colunas + blocos + pistas -> resolver."""
        N = n * n
        pistas = pistas_aleatorias(n, k)

        grupos = [path(n, (i, 0), (i, N - 1)) for i in range(N)]       # linhas
        grupos += [path(n, (0, j), (N - 1, j)) for j in range(N)]      # colunas
        grupos += [cube(n, i, j) for i in range(n) for j in range(n)]  # blocos
        grupos.append(pistas)

        modelo = Modelo(n)
        modelo.adicionar(*grupos)
        return pistas, modelo.resolver()


    def resolver_com_pistas_validas(n, tentativas=50):
        """Testa várias vezes para checar se existe pelo menos uma solução em várias tentativas."""
        for _ in range(tentativas):
            pistas, sol = montar_e_resolver(n)
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


    # R1: linhas, colunas e blocos 

    @pytest.mark.parametrize("n", [2, 3])
    def test_linhas_colunas_blocos_tem_todos_os_valores(n):
        _, sol = resolver_com_pistas_validas(n)
        assert erros_da_grelha(sol, n) == []


    # R2: pistas mantêm o valor 

    @pytest.mark.parametrize("n", [2, 3])
    def test_pistas_mantem_valor_na_solucao(n):
        pistas, sol = resolver_com_pistas_validas(n)
        assert len(pistas.coords) > 0
        for (i, j), val in pistas.coords.items():
            assert sol[i][j] == val, f"pista ({i},{j})={val} mudou para {sol[i][j]}"


    # R3: add rejeita entradas inválidas 

    @pytest.mark.parametrize("n", [2, 3])
    @pytest.mark.parametrize("i, j", [(-1, 0), (0, -1), ("N", 0), (0, "N")])   #N -> Dimensão da grelha, varia de acordo com n
    def test_add_rejeita_coordenadas_fora_da_grelha(n, i, j):
        N = n * n
        if i == "N":
            i = N
        else:
            i = i
        if j == "N":
            j = N
        else:
            j = j
        with pytest.raises((IndexError, ValueError)):   #Avisa que o código dentro deve lançar uma exceção do tipo IndexError ou ValueError para passar
            box(n).add(i, j)


    @pytest.mark.parametrize("n", [2, 3])
    @pytest.mark.parametrize("val", [0, -1, "N+1"])
    def test_add_rejeita_valores_fora_do_intervalo(n, val):
        N = n * n
        if val == "N+1":
            val = N + 1 
        else: 
            val
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



    return


if __name__ == "__main__":
    app.run()
