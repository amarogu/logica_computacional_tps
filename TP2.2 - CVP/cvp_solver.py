# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo>=0.23.3",
#     "numpy>=1.26",
#     "cvxpy>=1.5",
#     "clarabel>=0.9",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import heapq
    import itertools
    import time

    import cvxpy as cp
    import marimo as mo
    import numpy as np

    return cp, heapq, itertools, mo, np, time


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # O "Closest Vector Problem" (CVP)

    ## O problema

    Seja $G \in [0,1]^{k \times m}$ uma matriz aleatória de característica $k$
    (com $m \approx 2k$). As linhas de $G$ são $k$ vetores de $\mathbb{R}^m$ e
    geram o **reticulado**
    $$\mathcal{L}(G) = \{\, G^\top z \;:\; z \in \mathbb{Z}^k \,\}.$$

    Dado um **alvo** $t = G^\top u$, com $u$ uniforme em $[0,\ell]^k$ (real,
    portanto $t$ em geral **não** pertence ao reticulado), pretende-se
    encontrar
    $$z^\star = \arg\min_{z \in \mathbb{Z}^k \cap [0,\ell]^k} \; \|G^\top z - t\|_2,
    \qquad x^\star = G^\top z^\star .$$

    Os parâmetros a testar são $k \in \{30,40,50\}$, $m = 2k$ e
    $\ell \in \{1,5\}$ — seis configurações.

    ## Formulação

    Minimizar a norma é o mesmo que minimizar o seu quadrado, que é uma
    forma quadrática convexa em $z$:
    $$f(z) = \|G^\top z - t\|_2^2 = z^\top Q z - 2\,(Gt)^\top z + t^\top t,
    \qquad Q = G G^\top \succ 0 .$$

    Ficamos com um problema de **programação quadrática inteira** (MIQP) com
    restrições de caixa $0 \le z_i \le \ell$, $z_i \in \mathbb{Z}$.

    ## Abordagem: *branch-and-bound* sobre o Clarabel

    O Clarabel resolve programas cónicos/quadráticos **contínuos**, mas não
    trata variáveis inteiras. Por isso implementámos nós próprios um
    *branch-and-bound* (B&B):

    1. **Relaxação.** Num nó com caixa $[L,U]$ resolvemos com o Clarabel a
       relaxação contínua $\min\{f(z) : L \le z \le U\}$. O seu valor é um
       **minorante** de qualquer solução inteira dentro dessa caixa.
    2. **Incumbente.** Arredondamos a solução da relaxação (projetada na caixa)
       e, se for melhor, guardamo-la como melhor solução inteira conhecida —
       um **majorante** do ótimo.
    3. **Poda.** Um nó cujo minorante não é melhor que o incumbente é
       descartado.
    4. **Ramificação.** Escolhe-se uma variável fracionária $z_i = c$ e criam-se
       dois filhos: $z_i \le \lfloor c \rfloor$ e $z_i \ge \lceil c \rceil$.
    5. **Ordem de exploração.** *Best-first*: expande-se sempre o nó com menor
       minorante (fila de prioridade). Assim, o minorante do nó expandido é
       também um minorante **global**, o que permite reportar o *gap* quando se
       atinge o limite de tempo.

    **Escolha da variável de ramificação.** Em vez da regra "mais fracionária",
    usamos uma estimativa do aumento do objetivo: para a quadrática sem
    restrições, fixar $z_i$ a $v$ aumenta o mínimo exatamente
    $(z_i - v)^2 / (Q_{FF}^{-1})_{ii}$, onde $F$ são as variáveis livres
    (não presas à caixa). Escolhemos o $i$ que maximiza
    $\min(\Delta_\downarrow, \Delta_\uparrow)$, i.e. o ramo cujo pior filho
    sobe mais o minorante. Em testes isto reduziu o nº de nós face à regra
    "mais fracionária".

    **Eficiência com o `cvxpy`.** O problema é construído **uma só vez** com
    `cp.Parameter` para $L$ e $U$ (respeita DPP), pelo que em cada nó o `cvxpy`
    reutiliza a canonização e só atualiza os limites antes de chamar o
    Clarabel.

    Observação: com $t = G^\top u$ e $G$ de característica $k$, a relaxação na
    raiz tem sempre valor $0$ (atingido em $z = u$). Toda a dificuldade está em
    provar que não há ponto inteiro melhor que o incumbente.

    *(Alternativa: com o Mosek bastaria declarar `cp.Variable(k, integer=True)`
    e o próprio solver faria o B&B; optámos pelo Clarabel por não exigir
    licença.)*
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Uso de LLMs

    O código marcado com `# [LLM]` foi gerado/revisto com apoio de um LLM
    (Claude). O restante foi escrito pelos autores; todas as decisões finais de
    modelação foram dos autores.

    https://claude.ai/code/session_01DTsGR3EED5kJXr7KS9mzuM
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Geração de instâncias

    $G$ tem entradas uniformes em $[0,1]$; repetimos a geração até
    `matrix_rank(G) == k` (com probabilidade 1 isto acontece à primeira, mas o
    enunciado pede a verificação). O alvo é $t = G^\top u$ com
    $u \sim \mathcal{U}([0,\ell]^k)$.
    """)
    return


@app.cell
def _(np):
    # [LLM] gerador de instâncias
    def gerar_instancia(k, m, l, seed=None):
        """Devolve (G, t, u) com G k×m de característica k e t = Gᵀu."""
        rng = np.random.default_rng(seed)
        while True:
            G = rng.random((k, m))
            if np.linalg.matrix_rank(G) == k:
                break
        u = rng.uniform(0, l, size=k)
        return G, G.T @ u, u

    return (gerar_instancia,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## O solver
    """)
    return


@app.cell
def _(cp, heapq, np, time):
    # [LLM] branch-and-bound best-first com relaxações resolvidas pelo Clarabel
    def resolver_cvp(G, t, l, limite_tempo=60.0, tol=1e-9):
        """
        Resolve  min ||Gᵀz - t||₂  com z inteiro em [0, l]^k.

        Devolve um dicionário com:
          z, x, dist       — melhor solução encontrada
          minorante        — minorante global da distância
          otimo            — True se a otimalidade foi provada
          nos, tempo
        """
        k, _ = G.shape
        Q = G @ G.T

        # Modelo cvxpy construído uma única vez; L e U são parâmetros.
        z = cp.Variable(k)
        L_par = cp.Parameter(k)
        U_par = cp.Parameter(k)
        relaxacao = cp.Problem(
            cp.Minimize(cp.sum_squares(G.T @ z - t)),
            [z >= L_par, z <= U_par],
        )

        def relaxar(L, U):
            L_par.value, U_par.value = L, U
            relaxacao.solve(solver=cp.CLARABEL)
            return max(relaxacao.value, 0.0), z.value

        def f(zz):
            return float(np.sum((G.T @ zz - t) ** 2))

        def escolher_variavel(L, U, zr):
            # Variáveis fracionárias candidatas.
            frac = np.abs(zr - np.round(zr))
            cand = np.flatnonzero(frac > 1e-6)
            # Variáveis livres (não presas à caixa) e diag. de Q_FF^{-1}.
            F = np.flatnonzero((zr > L + 1e-7) & (zr < U - 1e-7))
            d = dict(zip(F, np.diag(np.linalg.inv(Q[np.ix_(F, F)]))))
            melhor, escolhida = -1.0, cand[np.argmax(frac[cand])]
            for i in cand:
                if i not in d:
                    continue
                baixo = (zr[i] - np.floor(zr[i])) ** 2 / d[i]
                cima = (np.ceil(zr[i]) - zr[i]) ** 2 / d[i]
                if min(baixo, cima) > melhor:
                    melhor, escolhida = min(baixo, cima), i
            return escolhida

        t0 = time.perf_counter()
        L0, U0 = np.zeros(k), np.full(k, float(l))
        v0, zr0 = relaxar(L0, U0)

        melhor_z = np.clip(np.round(zr0), L0, U0)
        melhor_v = f(melhor_z)

        fila = [(v0, 0, L0, U0, zr0)]
        contador, nos, minorante, otimo = 1, 0, v0, True

        while fila:
            v, _, L, U, zr = heapq.heappop(fila)
            if v >= melhor_v - tol:
                continue  # poda (o incumbente pode ter melhorado)
            if time.perf_counter() - t0 > limite_tempo:
                minorante, otimo = v, False  # best-first ⇒ v é minorante global
                break
            nos += 1
            if np.max(np.abs(zr - np.round(zr))) < 1e-6:
                continue  # relaxação já inteira: foi tratada como incumbente
            i = escolher_variavel(L, U, zr)

            L1, U1 = L.copy(), U.copy()
            U1[i] = np.floor(zr[i])
            L2, U2 = L.copy(), U.copy()
            L2[i] = np.ceil(zr[i])
            for Ln, Un in ((L1, U1), (L2, U2)):
                vn, zn = relaxar(Ln, Un)
                if vn >= melhor_v - tol:
                    continue
                zi = np.clip(np.round(zn), Ln, Un)
                fi = f(zi)
                if fi < melhor_v:
                    melhor_z, melhor_v = zi, fi
                contador += 1
                heapq.heappush(fila, (vn, contador, Ln, Un, zn))

        if otimo:
            minorante = melhor_v
        z_final = melhor_z.astype(int)
        return {
            "z": z_final,
            "x": G.T @ z_final,
            "dist": np.sqrt(melhor_v),
            "minorante": np.sqrt(max(minorante, 0.0)),
            "otimo": otimo,
            "nos": nos,
            "tempo": time.perf_counter() - t0,
        }

    return (resolver_cvp,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Exemplo

    Uma instância pequena ($k=6$, $m=12$, $\ell=5$) para ver o formato da
    resposta.
    """)
    return


@app.cell
def _(gerar_instancia, np, resolver_cvp):
    G_ex, t_ex, u_ex = gerar_instancia(6, 12, 5, seed=1)
    r_ex = resolver_cvp(G_ex, t_ex, 5)
    np.set_printoptions(precision=3, suppress=True)
    print("característica(G) =", np.linalg.matrix_rank(G_ex))
    print("u (real)          =", u_ex)
    print("z* (inteiro)      =", r_ex["z"])
    print("x* = Gᵀz*         =", r_ex["x"])
    print(f"‖x* − t‖          = {r_ex['dist']:.4f}   (ótimo provado: {r_ex['otimo']})")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Testes de correção

    Para $k$ pequeno é possível enumerar **todos** os $(\ell+1)^k$ pontos da
    caixa e obter o ótimo por força bruta. Comparamos o valor do B&B com o da
    força bruta em várias instâncias aleatórias, e verificamos também que a
    solução respeita a caixa e é inteira.
    """)
    return


@app.cell
def _(itertools, np):
    # [LLM] força bruta vetorizada (só para k pequeno)
    def forca_bruta(G, t, l):
        k = G.shape[0]
        Z = np.array(list(itertools.product(range(l + 1), repeat=k)), dtype=float)
        d2 = np.sum((Z @ G - t) ** 2, axis=1)
        i = int(np.argmin(d2))
        return Z[i].astype(int), np.sqrt(d2[i])

    return (forca_bruta,)


@app.cell
def _(forca_bruta, gerar_instancia, mo, np, resolver_cvp):
    # [LLM] bateria de testes de correção
    casos_correcao = [(8, 1), (10, 1), (12, 1), (5, 3), (6, 3), (5, 5), (6, 5)]
    linhas_corr = []
    falhas = 0
    for k_c, l_c in casos_correcao:
        for s_c in range(5):
            G_c, t_c, _ = gerar_instancia(k_c, 2 * k_c, l_c, seed=100 + s_c)
            r_c = resolver_cvp(G_c, t_c, l_c)
            _, d_bf = forca_bruta(G_c, t_c, l_c)
            ok = (
                r_c["otimo"]
                and abs(r_c["dist"] - d_bf) < 1e-6
                and np.all((r_c["z"] >= 0) & (r_c["z"] <= l_c))
            )
            falhas += not ok
            linhas_corr.append(
                {
                    "k": k_c,
                    "ℓ": l_c,
                    "seed": 100 + s_c,
                    "B&B": round(r_c["dist"], 6),
                    "força bruta": round(d_bf, 6),
                    "ok": ok,
                }
            )
    mo.vstack(
        [
            mo.md(f"**{len(linhas_corr) - falhas}/{len(linhas_corr)} testes corretos.**"),
            mo.ui.table(linhas_corr, selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## As seis configurações pedidas

    Para cada $(k,\ell)$ com $k\in\{30,40,50\}$, $m=2k$, $\ell\in\{1,5\}$
    resolvemos uma instância com limite de tempo. Reportamos:

    * **dist** — distância da melhor solução encontrada;
    * **minorante** — minorante global provado pelo B&B (igual a *dist* quando
      a otimalidade é provada);
    * **gap** $= (\text{dist} - \text{minorante})/\text{dist}$;
    * **arred.** — distância obtida arredondando $u$ (o "palpite ingénuo"),
      para mostrar o ganho do B&B.

    O limite de tempo é configurável abaixo (o notebook demora
    $\approx 6\times$ esse valor no pior caso).
    """)
    return


@app.cell
def _(mo):
    limite = mo.ui.slider(10, 300, value=60, step=10, label="limite de tempo por instância (s)")
    limite
    return (limite,)


@app.cell
def _(gerar_instancia, limite, mo, np, resolver_cvp):
    # [LLM] corrida das seis configurações
    linhas_cfg = []
    for k_g in (30, 40, 50):
        for l_g in (1, 5):
            G_g, t_g, u_g = gerar_instancia(k_g, 2 * k_g, l_g, seed=0)
            r_g = resolver_cvp(G_g, t_g, l_g, limite_tempo=limite.value)
            arred = np.sqrt(np.sum((G_g.T @ np.clip(np.round(u_g), 0, l_g) - t_g) ** 2))
            linhas_cfg.append(
                {
                    "k": k_g,
                    "m": 2 * k_g,
                    "ℓ": l_g,
                    "dist": round(r_g["dist"], 4),
                    "minorante": round(r_g["minorante"], 4),
                    "gap %": round(100 * (r_g["dist"] - r_g["minorante"]) / r_g["dist"], 2),
                    "ótimo": r_g["otimo"],
                    "nós": r_g["nos"],
                    "tempo (s)": round(r_g["tempo"], 2),
                    "arred.": round(arred, 4),
                }
            )
    mo.ui.table(linhas_cfg, selection=None)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Escalabilidade

    Para perceber como o custo cresce com $k$, resolvemos 3 instâncias por
    ponto para $k = 10, 15, 20, 25, 30$ ($m=2k$) e registamos a mediana do
    número de nós e do tempo até provar a otimalidade.
    """)
    return


@app.cell
def _(gerar_instancia, mo, np, resolver_cvp):
    # [LLM] estudo de escalabilidade
    linhas_esc = []
    for l_e in (1, 5):
        for k_e in (10, 15, 20, 25, 30):
            rs = [
                resolver_cvp(*gerar_instancia(k_e, 2 * k_e, l_e, seed=200 + s)[:2], l_e, limite_tempo=120)
                for s in range(3)
            ]
            linhas_esc.append(
                {
                    "ℓ": l_e,
                    "k": k_e,
                    "nós (mediana)": int(np.median([r["nos"] for r in rs])),
                    "tempo mediano (s)": round(float(np.median([r["tempo"] for r in rs])), 2),
                    "todos ótimos": all(r["otimo"] for r in rs),
                }
            )
    mo.ui.table(linhas_esc, selection=None)
    return (linhas_esc,)


@app.cell
def _(linhas_esc):
    # [LLM] gráfico (escala log) do nº de nós em função de k
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 3.5))
    for l_p, marca in ((1, "o-"), (5, "s-")):
        pts = [r for r in linhas_esc if r["ℓ"] == l_p]
        ax.semilogy([r["k"] for r in pts], [max(r["nós (mediana)"], 1) for r in pts], marca, label=f"ℓ = {l_p}")
    ax.set_xlabel("k")
    ax.set_ylabel("nós explorados (mediana)")
    ax.set_title("Crescimento do B&B com a dimensão")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Discussão

    * **Correção.** Em todas as instâncias pequenas o B&B devolve exatamente o
      ótimo da força bruta. Por construção, quando `ótimo = True` o
      minorante iguala o valor do incumbente, o que é uma prova de
      otimalidade.
    * **Escalabilidade.** O número de nós cresce de forma aproximadamente
      exponencial em $k$ (reta em escala logarítmica), como esperado: o CVP é
      NP-difícil. Até $k=30$ a otimalidade é provada em segundos/dezenas de
      segundos; para $k=40$ e $k=50$ o limite de tempo é atingido. Nesse caso o
      B&B devolve a melhor solução encontrada e um *gap*, que mede quão longe,
      no máximo, estamos do ótimo. Numa corrida com 60 s: para $k=40$ o *gap*
      ficou em ≈ 4–6 %; para $k=50$ subiu para ≈ 11–17 %. Na maioria dos casos
      a solução é bastante melhor que o arredondamento de $u$ (p.ex. 4.50 vs
      26.3 em $k=50,\ell=1$), mas em $k=50,\ell=5$ o B&B **não** conseguiu
      melhorar o arredondamento dentro do limite — é aqui que a abordagem
      deixa de escalar.
    * **Porque é difícil.** Como as entradas de $G$ são todas positivas, as
      linhas de $G$ são quase paralelas e $Q=GG^\top$ é mal condicionada (um
      valor próprio enorme e muitos pequenos). As relaxações contínuas
      ficam então "achatadas" e dão minorantes fracos, o que obriga a explorar
      muitos nós.
    * **Melhorias possíveis.** Usar o Mosek com variáveis inteiras (B&B
      profissional com cortes); chamar o Clarabel diretamente sem o `cvxpy`
      (≈ 5× menos tempo por nó nos nossos testes); ou combinar com técnicas
      de reticulados (redução LLL e enumeração de Schnorr–Euchner).
    """)
    return


if __name__ == "__main__":
    app.run()
