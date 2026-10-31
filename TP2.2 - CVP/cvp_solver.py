import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # O "Closest Vector Problem" (CVP)

    Seja um conjunto específico de vetores linearmente independentes $G \equiv \set{g_1, g_2, \dots, g_k \mid g_i \in \reals^m}$; o reticulado determinado por $G$, $\mathcal{L}_G \equiv \set{x = z_1g_1, z_2g_2, \dots, z_kg_k  \mid z_i \in \Z}$. E finalmente um vetor aleatório $t$ (target), com cada um de seus componentes >= 0, qual é o vetor $x \in \mathcal{L}_G$ que está mais próximo de (closest to) $t$?
    """)
    return


if __name__ == "__main__":
    app.run()
