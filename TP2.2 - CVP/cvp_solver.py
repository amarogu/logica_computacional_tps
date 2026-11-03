import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    # Índice dos chats com LLM; a transcrição de cada um está nesta pasta (chat_<n>_*.md). Nas células,
    # "# Gerado por LLM: chat (n)" marca o que esse chat gerou e "# Chat associado (n)" o que foi apenas discutido nele.
    mo.md(r"""
    🔗 **Chats com LLM** (transcrições nesta pasta)

    1. [Discussão do enunciado: visão geral do problema](https://github.com/amarogu/logica_computacional_tps/blob/main/TP2.2%20-%20CVP/chat_1_cvp_notebook_exercise_goal.md)
    2. [Geração da interface: figura, parâmetros e resultado](https://github.com/amarogu/logica_computacional_tps/blob/main/TP2.2%20-%20CVP/chat_2_vector_search_ui.md)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # Chat associado (1)
    mo.md(r"""
    # O "Closest Vector Problem" (CVP)

    Seja um conjunto específico de vetores linearmente independentes $G \equiv \set{g_1, g_2, \dots, g_k \mid g_i \in \reals^m}$; o reticulado determinado por $G$, $\mathcal{L}_G \equiv \set{x = z_1g_1, z_2g_2, \dots, z_kg_k  \mid z_i \in \Z}$. E finalmente um vetor aleatório $t$ (target), com cada um de seus componentes >= 0, qual é o vetor $x \in \mathcal{L}_G$ que está mais próximo de (closest to) $t$?
    """)
    return


@app.cell
def _():
    import heapq
    import itertools
    import random
    import time
    import warnings

    import cvxpy as cp
    import numpy as np

    # Um nó com estado OPTIMAL_INACCURATE é tratado em branch_and_bound: não serve para podar
    warnings.filterwarnings("ignore", message="Solution may be inaccurate")

    def branch_and_bound(G, t, l, tempo_limite=60.0, tol=1e-6):
        inicio = time.perf_counter()
        k = G.shape[0]
        H = G @ G.T
        Gt = G @ t

        # Com Gᵀ = QR, ||Gᵀz - t||² = ||Rz - Qᵀt||² + resto²: o cone fica com k + 2 entradas em vez de m + 1
        Q, R = np.linalg.qr(G.T)
        alvo = Q.T @ t
        resto = np.linalg.norm(t - Q @ alvo)

        # Relaxação de cada nó: z contínuo com lo <= z <= hi e r >= ||Gᵀz - t||₂ (cone de segunda ordem)
        z, r = cp.Variable(k), cp.Variable()
        lo, hi = cp.Parameter(k), cp.Parameter(k)
        cone = cp.SOC(r, cp.hstack([alvo - R @ z, [resto]]))
        relaxacao = cp.Problem(cp.Minimize(r), [cone, z >= lo, z <= hi])

        # Passos de ±1 em uma ou duas coordenadas, para a pesquisa local
        passos = []
        for i in range(k):
            for si in (1, -1):
                passo = np.zeros(k)
                passo[i] = si
                passos.append(passo)
                for j in range(i + 1, k):
                    for sj in (1, -1):
                        duplo = passo.copy()
                        duplo[j] = sj
                        passos.append(duplo)
        passos = np.array(passos)
        custos = (passos @ H * passos).sum(axis=1)

        # A partir de um z inteiro, dá sempre o passo que mais reduz dist², até nenhum passo ajudar
        def pesquisa_local(z_int):
            gradiente = 2 * (H @ z_int - Gt)
            while True:
                variacao = passos @ gradiente + custos
                novos = z_int + passos
                variacao[((novos < 0) | (novos > l)).any(axis=1)] = np.inf
                melhor_passo = variacao.argmin()
                if variacao[melhor_passo] >= -1e-9:
                    return z_int
                z_int = novos[melhor_passo]
                gradiente = gradiente + 2 * H @ passos[melhor_passo]

        melhor_z, melhor_d = np.zeros(k), np.linalg.norm(t)

        def avaliar(candidato):
            nonlocal melhor_z, melhor_d
            d = np.linalg.norm(G.T @ candidato - t)
            if d < melhor_d:
                melhor_z, melhor_d = candidato, d

        # Best-first: abre sempre o nó com menor limite inferior (o contador só desempata)
        contador = itertools.count()
        abertos = [(0.0, next(contador), np.zeros(k), np.full(k, float(l)))]
        nos = 0
        while abertos and abertos[0][0] < melhor_d - tol and time.perf_counter() - inicio < tempo_limite:
            limite, _, a, b = heapq.heappop(abertos)
            if (a == b).all():
                avaliar(a)
                continue

            lo.value, hi.value = a, b
            try:
                relaxacao.solve(solver=cp.CLARABEL)
                estado = relaxacao.status
            except cp.SolverError:
                estado = None
            nos += 1

            # Se o solver falhar, continua a ramificar a partir do meio da caixa: nada fica por explorar
            v = z.value if estado in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE) else (a + b) / 2
            candidato = np.clip(np.round(v), 0, l)
            avaliar(pesquisa_local(candidato) if nos % 10 == 1 else candidato)

            # Só uma solução exata da relaxação dá um limite inferior em que se possa confiar
            exato = estado == cp.OPTIMAL
            if exato:
                limite = max(limite, float(r.value))
            if limite >= melhor_d - tol:
                continue

            livres = np.flatnonzero(a < b)
            if exato:
                # Todo o z melhor que o atual cumpre (z - v)ᵀH(z - v) < melhor_d² - r²:
                # a caixa que envolve esse elipsoide aperta os limites das coordenadas livres
                inversa = np.diag(np.linalg.inv(H[np.ix_(livres, livres)]))
                raio = np.sqrt((melhor_d**2 - float(r.value) ** 2 + 1e-6) * inversa)
                a, b = a.copy(), b.copy()
                a[livres] = np.maximum(a[livres], np.ceil(v[livres] - raio - 1e-6))
                b[livres] = np.minimum(b[livres], np.floor(v[livres] + raio + 1e-6))
                if (a > b).any():
                    continue
                livres = np.flatnonzero(a < b)
                if livres.size == 0:
                    avaliar(a)
                    continue

            # Ramifica na coordenada mais fracionária: z_i <= corte ou z_i >= corte + 1
            i = livres[np.abs(v[livres] - np.round(v[livres])).argmax()]
            corte = np.clip(np.floor(v[i]), a[i], b[i] - 1)
            b_baixo, a_cima = b.copy(), a.copy()
            b_baixo[i], a_cima[i] = corte, corte + 1
            heapq.heappush(abertos, (limite, next(contador), a, b_baixo))
            heapq.heappush(abertos, (limite, next(contador), a_cima, b))

        otimo = not abertos or abertos[0][0] >= melhor_d - tol
        return {
            "x": G.T @ melhor_z,
            "z": melhor_z.astype(int),
            "dist": float(melhor_d),
            "limite_inferior": float(melhor_d if otimo else abertos[0][0]),
            "otimo": otimo,
            "nos": nos,
            "tempo": time.perf_counter() - inicio,
        }

    def solve_cvp(k, m, l, seed=None, tempo_limite=60.0):
        if any(v < 1 or v % 1 for v in (k, m, l)):
            raise ValueError("k, m e l têm de ser números inteiros positivos.")
        k, m, l = int(k), int(m), int(l)
        if k > m:
            raise ValueError("Reduz k ou aumenta m: em dimensão m não há mais de m vetores linearmente independentes.")
        gerador = random.Random(seed)

        while True:
            G = []
            for i in range(0, k):
                g_i = []
                for j in range(0, m):
                    g_ij = gerador.uniform(0, 1)
                    g_i.append(g_ij)
                G.append(g_i)
            G = np.array(G)
            if np.linalg.matrix_rank(G) == k:
                break

        u = np.array([gerador.uniform(0, l) for _ in range(k)])
        t = G.T @ u
        return {**branch_and_bound(G, t, l, tempo_limite), "G": G, "t": t}

    return (solve_cvp,)


@app.cell(hide_code=True)
def _(mo):
    # Gerado por LLM: chat (2)
    # Ilustração do problema: o reticulado gerado por g1 e g2, o alvo t e o vetor x mais próximo dele
    _g1, _g2 = (52, 12), (18, -36)
    _o, _t = (296, 112), (478, 52)
    _pontos = [
        (_o[0] + _a * _g1[0] + _b * _g2[0], _o[1] + _a * _g1[1] + _b * _g2[1])
        for _a in range(-8, 9)
        for _b in range(-6, 7)
    ]
    _x = min(_pontos, key=lambda _p: (_p[0] - _t[0]) ** 2 + (_p[1] - _t[1]) ** 2)
    _pontos_svg = "".join(f'<circle cx="{_p[0]}" cy="{_p[1]}" r="2.2"/>' for _p in _pontos)

    figura = mo.Html(f"""
    <svg viewBox="0 0 720 150" role="img"
         aria-label="Reticulado gerado por g1 e g2: x é o ponto do reticulado mais próximo do alvo t."
         style="display: block; width: 100%; height: auto; color: var(--foreground);
                mask-image: linear-gradient(90deg, transparent, #000 16%, #000 84%, transparent)">
      <defs>
        <marker id="cvp-seta" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M1 1 7 4 1 7" fill="none" stroke="context-stroke" stroke-width="1.3"/>
        </marker>
      </defs>
      <g fill="currentColor" opacity=".4">{_pontos_svg}</g>
      <g stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#cvp-seta)">
        <line x1="{_o[0]}" y1="{_o[1]}" x2="{_o[0] + _g1[0]}" y2="{_o[1] + _g1[1]}"/>
        <line x1="{_o[0]}" y1="{_o[1]}" x2="{_o[0] + _g2[0]}" y2="{_o[1] + _g2[1]}"/>
      </g>
      <line x1="{_t[0]}" y1="{_t[1]}" x2="{_x[0]}" y2="{_x[1]}" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3 3"/>
      <circle cx="{_t[0]}" cy="{_t[1]}" r="5" fill="var(--background)" stroke="currentColor" stroke-width="1.5"/>
      <circle cx="{_x[0]}" cy="{_x[1]}" r="6" fill="var(--action)" stroke="var(--action-foreground)" stroke-width="1.5"/>
      <g fill="currentColor" font-family="KaTeX_Math, serif" font-style="italic" font-size="16">
        <text x="{_t[0] - 18}" y="{_t[1] - 4}">t</text>
        <text x="{_x[0] + 12}" y="{_x[1] + 5}">x</text>
        <text x="{_o[0] + _g1[0] + 8}" y="{_o[1] + _g1[1] + 13}" opacity=".7">g<tspan dy="3" font-size="11" font-family="KaTeX_Main, serif" font-style="normal">1</tspan></text>
        <text x="{_o[0] + _g2[0] - 19}" y="{_o[1] + _g2[1] - 3}" opacity=".7">g<tspan dy="3" font-size="11" font-family="KaTeX_Main, serif" font-style="normal">2</tspan></text>
      </g>
    </svg>
    """)
    return (figura,)


@app.cell(hide_code=True)
def _(figura, mo):
    # Gerado por LLM: chat (2)
    def _validar(p):
        if None in p.values():
            return "Preenche todos os parâmetros: k, m e l."
        if p["k"] < 1 or p["m"] < 1 or p["k"] % 1 or p["m"] % 1:
            return "k e m têm de ser números inteiros positivos."
        if p["k"] > p["m"]:
            return "Reduz k ou aumenta m: em dimensão m não há mais de m vetores linearmente independentes."

    parametros = (
        mo.Html("""
        <div style="display: grid; gap: 1rem; align-items: end; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr))">
          {k} {m} {l}
        </div>
        """)
        .batch(
            k=mo.ui.number(start=1, step=1, value=3, label=r"$k$ · vetores em $G$", full_width=True),
            m=mo.ui.number(start=1, step=1, value=5, label=r"$m$ · dimensão de cada vetor", full_width=True),
            l=mo.ui.number(value=10, label=r"$l$", full_width=True),
        )
        .form(bordered=False, submit_button_label="Search for closest vector…", validate=_validar)
    )

    mo.vstack([figura, parametros], gap=0)
    return (parametros,)


@app.cell(hide_code=True)
def _(mo, parametros, solve_cvp):
    # Gerado por LLM: chat (2)
    mo.stop(parametros.value is None)

    try:
        with mo.status.spinner(title="À procura do vetor mais próximo…"):
            _r = solve_cvp(**parametros.value)
    except ValueError as _erro:
        mo.stop(True, mo.callout(str(_erro), kind="danger"))

    # Os vetores partem de linha se forem longos
    _x = r",\allowbreak ".join(f"{_c:.4f}" for _c in _r["x"])
    _z = r",\allowbreak ".join(map(str, _r["z"]))
    _dados = ", ".join(f"{_n} = {_v}" for _n, _v in parametros.value.items())

    # Sem prova de otimalidade, o resultado é apresentado como o melhor encontrado, com o intervalo da distância ótima
    if _r["otimo"]:
        _titulo = f"**Vetor mais próximo** para ${_dados}$"
        _estado = f"Ótimo provado em {_r['nos']} nós e {_r['tempo']:.1f} s."
    else:
        _titulo = f"**Melhor vetor encontrado** para ${_dados}$"
        _estado = (
            f"Tempo esgotado ao fim de {_r['nos']} nós e {_r['tempo']:.1f} s: "
            f"a distância ótima está entre {_r['limite_inferior']:.4f} e {_r['dist']:.4f}."
        )

    mo.callout(
        mo.vstack(
            [
                mo.md(_titulo),
                mo.md(f"$x = ({_x})$"),
                mo.md(f"$z = ({_z})$"),
                mo.md(f"$\\text{{dist}}(x, t) = {_r['dist']:.4f}$"),
                mo.md(_estado),
            ]
        ),
        kind="success" if _r["otimo"] else "warn",
    )
    return


if __name__ == "__main__":
    app.run()
