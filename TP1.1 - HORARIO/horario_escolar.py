import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    # https://claude.ai/code/session_01UKPx4PhmMbk1saWW2Rvzkk
    import anywidget, traitlets

    class Clickable(anywidget.AnyWidget):
        _esm = """
        function render({ model, el }) {
          el.innerHTML = model.get("html");
          el.style.cursor = "pointer";
          el.style.display = "inline";
          el.onclick = () => { model.set("clicks", model.get("clicks") + 1); model.save_changes(); };
        }
        export default { render };
        """
        html = traitlets.Unicode("").tag(sync=True)
        clicks = traitlets.Int(0).tag(sync=True)

    w = mo.ui.anywidget(Clickable(html="<b style=\"display: inline\">clique aqui</b>"))
    return (w,)


@app.cell(hide_code=True)
def _(mo, w):
    mo.md(f"""
    # Horário escolar ⏱️

    Para gerar um horário com base nos dados
    em <code>./dados/</code>, {w}.
    <div style="width: 100%; height: 1px; background-color: #ccc" />
    """)
    return


@app.cell
def _(mo):
    from pathlib import Path
    import csv

    # data folders are relative to this notebook, not to where marimo was launched
    root = mo.notebook_dir() or Path('.')

    # https://claude.ai/code/session_01F7LZyQp7Dv7GgNpcerp6aS
    def get_data(from_folder):
        data = {}
        for file in (root / from_folder).rglob('*.csv'):
            with file.open(encoding='utf-8', newline='') as f:
                data[file.stem] = list(csv.DictReader(f))
        return data

    return (get_data,)


@app.function
# https://claude.ai/code/session_011oP4T7nB5aq5sgZ9XxvDvf
def assert_data(from_folder, data):
    expected = {'disciplinas', 'disponibilidade_excecoes', 'salas', 'turmas'}
    # bonus: teacher preferences are optional
    optional = {'preferencias'}
    unknown = sorted(data.keys() - expected - optional)
    if unknown:
        raise ValueError(
            f"Ficheiros CSV não reconhecidos em {from_folder}: {', '.join(unknown)}. "
            f"Esperados: {', '.join(sorted(expected))}; opcional: {', '.join(sorted(optional))}."
        )

    missing = sorted(expected - data.keys())
    if missing:
        raise ValueError(
            f"Ficheiros CSV em falta: {missing}"
        )

    # R4: duplo_periodo subjects are split into blocks of 2 periods
    odd = [subject['disciplina'] for subject in data['disciplinas']
           if subject['duplo_periodo'] == 'sim' and int(subject['carga_semanal']) % 2]
    if odd:
        raise ValueError(
            f"Disciplinas com duplo_periodo=sim e carga_semanal ímpar: {', '.join(odd)}."
        )

    # R6 and preferences: each row names one of the 5 × 5 periods of the week
    for name in ('disponibilidade_excecoes', 'preferencias'):
        invalid = [f"{row['professor']} ({row['dia']}, {row['periodo']})"
                   for row in data.get(name, [])
                   if row['dia'] not in ('Seg', 'Ter', 'Qua', 'Qui', 'Sex')
                   or row['periodo'] not in ('1', '2', '3', '4', '5')]
        if invalid:
            raise ValueError(
                f"{name}.csv com dia/periodo inválido: {', '.join(invalid)}."
            )

    # R7: every sala_especial must be a special room of salas.csv
    special = {room['sala'] for room in data['salas'] if room['tipo'] == 'especial'}
    missing_rooms = sorted({subject['sala_especial'] for subject in data['disciplinas']
                            if subject['sala_especial'] and subject['sala_especial'] not in special})
    if missing_rooms:
        raise ValueError(
            f"Salas especiais em falta em salas.csv: {', '.join(missing_rooms)}."
        )


@app.cell
def _():
    from dataclasses import dataclass
    from collections import namedtuple
    from html import escape

    DAYS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex']
    # every (day, slot) of the week: 5 days × 5 slots
    TIMES = [(day, slot) for day in range(5) for slot in range(5)]

    At = namedtuple('At', 'day slot')

    # one period of one subject for one grade, e.g.
    # Lecture(at=At(day=0, slot=1), subject='Matemática', professor='Prof. Ana', grade='7ºA')
    @dataclass
    class Lecture:
        at: At
        subject: str
        professor: str
        grade: str
        room: str = None

    # https://claude.ai/code/session_01LGQikCyDfhpbSp5UqZvVCw
    class Timetable:
        css = """
            .timetables {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(min(100%, 30rem), 1fr));
                gap: 1.5rem;
                margin-top: 1rem;
                hyphens: auto;
                overflow-wrap: break-word;
            }
            .timetables table {
                width: 100%;
                table-layout: fixed;
                border-collapse: separate;
                border-spacing: 3px;
                font-size: 0.9rem;
            }
            .timetables caption {
                text-align: left;
                font-size: 1rem;
                font-weight: 600;
                padding: 0 3px 0.25rem;
            }
            .timetables th {
                font-weight: 500;
                opacity: 0.6;
                text-align: left;
                padding: 0.25rem 0.5rem;
            }
            .timetables tr > th:first-child {
                width: 2.25rem;
                padding: 0;
                text-align: center;
            }
            .timetables td {
                height: 2.5rem;
                padding: 0.25rem 0.5rem;
                border-radius: 6px;
                line-height: 1.2;
                background: color-mix(in srgb, currentColor 4%, transparent);
            }
            .timetables td:not(:empty) {
                font-weight: 500;
                background: oklch(0.7 0.14 var(--hue) / 0.2);
                box-shadow: inset 3px 0 oklch(0.65 0.15 var(--hue));
            }
            .timetables td.changed {
                outline: 2px dashed oklch(0.6 0.15 var(--hue));
                outline-offset: -2px;
            }
            .timetables small {
                display: block;
                font-weight: 400;
                opacity: 0.7;
            }
        """

        def __init__(self, lectures, seconds=None):
            self.lectures = lectures
            # how long the solver took to find it
            self.seconds = seconds
            # R9: when set, lectures that are not in `previous` (same time and room) are outlined
            self.previous = None

        # Uma tabela por turma, com os tempos nas linhas e os dias nas colunas
        def _repr_html_(self):
            subjects = dict.fromkeys(lecture.subject for lecture in self.lectures)
            # each subject keeps the same colour across grades
            hues = {subject: 360 * i // len(subjects) for i, subject in enumerate(subjects)}
            tables = []
            for grade in dict.fromkeys(lecture.grade for lecture in self.lectures):
                cells = {lecture.at: lecture for lecture in self.lectures if lecture.grade == grade}
                rows = ''
                for slot in range(5):
                    rows += f'<tr><th>{slot + 1}º</th>'
                    for day in range(5):
                        lecture = cells.get((day, slot))
                        if lecture is None:
                            rows += '<td></td>'
                            continue
                        room = f'<small>{escape(lecture.room)}</small>' if lecture.room else ''
                        changed = (' class="changed"' if self.previous is not None
                                   and lecture not in self.previous.lectures else '')
                        rows += (f'<td style="--hue: {hues[lecture.subject]}"{changed}>'
                                 f'{escape(lecture.subject)}{room}</td>')
                    rows += '</tr>'
                header = ''.join(f'<th>{day}</th>' for day in DAYS)
                tables.append(f'<table><caption>Turma {escape(grade)}</caption>'
                              f'<tr><th></th>{header}</tr>{rows}</table>')
            return f'<style>{self.css}</style><div class="timetables" lang="pt">{''.join(tables)}</div>'

    return At, DAYS, Lecture, TIMES, Timetable


@app.cell
def _(At, DAYS, Lecture, TIMES, Timetable):
    from ortools.sat.python import cp_model

    # R6: the (professor, day, slot) in which a teacher can't teach
    def unavailable_periods(data):
        return {(row['professor'], DAYS.index(row['dia']), int(row['periodo']) - 1)
                for row in data['disponibilidade_excecoes']}

    # R7: a subject uses its sala_especial or, when that is empty, the normal room
    def uses(subject, room):
        if subject['sala_especial']:
            return subject['sala_especial'] == room['sala']
        return room['tipo'] == 'normal'

    def build_model(data):
        model = cp_model.CpModel()
        grades = [grade['turma'] for grade in data['turmas']]
        subjects = data['disciplinas']
        teachers = dict.fromkeys(subject['professor'] for subject in subjects)
        unavailable = unavailable_periods(data)

        # x[grade, subject, day, slot] is true when the grade has that subject at that time
        x = {(grade, subject['disciplina'], day, slot):
             model.new_bool_var(f"{grade}_{subject['disciplina']}_{day}_{slot}")
             for grade in grades for subject in subjects for day, slot in TIMES}

        for grade in grades:
            # R1: no two lectures of the same grade at the same time
            for day, slot in TIMES:
                model.add(sum(x[grade, subject['disciplina'], day, slot] for subject in subjects) <= 1)

            for subject in subjects:
                name = subject['disciplina']
                # R2: exactly carga_semanal lectures a week
                model.add(sum(x[grade, name, day, slot] for day, slot in TIMES)
                          == int(subject['carga_semanal']))

                for day in range(5):
                    today = [x[grade, name, day, slot] for slot in range(5)]
                    if subject['duplo_periodo'] == 'sim':
                        # R3 and R4: at most one double block a day, so 0 or 2 lectures (never 1)...
                        model.add(sum(today) <= 2)
                        model.add(sum(today) != 1)
                        # R4: ... in consecutive slots: never two slots more than 1 apart
                        for slot in range(5):
                            for later in range(slot + 2, 5):
                                model.add(today[slot] + today[later] <= 1)
                    else:
                        # R3: at most one lecture of this subject a day
                        model.add(sum(today) <= 1)

                    # R6: no lectures when the teacher is unavailable
                    for slot in range(5):
                        if (subject['professor'], day, slot) in unavailable:
                            model.add(today[slot] == 0)
        # R8: all of the above comes from `data`, read from the CSV files

        # the lectures `teacher` gives at (day, slot), over all grades: 0 or 1 because of R5
        def teaching(teacher, day, slot):
            return sum(x[grade, subject['disciplina'], day, slot]
                       for grade in grades for subject in subjects
                       if subject['professor'] == teacher)

        # R5: a teacher gives at most one lecture at a time, over all grades
        for teacher in teachers:
            for day, slot in TIMES:
                model.add(teaching(teacher, day, slot) <= 1)

        # R7: at any time, never more lectures in a type of room than rooms of that type
        for room in data['salas']:
            for day, slot in TIMES:
                model.add(sum(x[grade, subject['disciplina'], day, slot]
                              for grade in grades for subject in subjects if uses(subject, room))
                          <= int(room['quantidade']))

        # O1: a slot is a hole when the teacher teaches before and after it that day, but not in it
        holes = []
        for teacher in teachers:
            for day in range(5):
                busy = [teaching(teacher, day, slot) for slot in range(5)]
                for slot in range(1, 4):
                    hole = model.new_bool_var(f'hole_{teacher}_{day}_{slot}')
                    for before in range(slot):
                        for after in range(slot + 1, 5):
                            model.add(hole >= busy[before] + busy[after] - busy[slot] - 1)
                    holes.append(hole)

        return model, x, holes

    # solves the model and reads the timetable from the x[grade, subject, day, slot] that are true
    def solve(model, x, data):
        solver = cp_model.CpSolver()
        # O1 needn't be optimal: after 10 s, keep the best timetable found so far
        solver.parameters.max_time_in_seconds = 10
        if solver.solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None
        teachers = {subject['disciplina']: subject['professor'] for subject in data['disciplinas']}
        timetable = Timetable([
            Lecture(at=At(day, slot), subject=subject, professor=teachers[subject], grade=grade)
            for (grade, subject, day, slot), chosen in x.items() if solver.value(chosen)
        ], seconds=solver.wall_time)
        assign_rooms(data, timetable)
        return timetable

    # R7: each lecture goes to its subject's sala_especial or, when that is empty, the normal room
    def assign_rooms(data, timetable):
        subjects = {subject['disciplina']: subject for subject in data['disciplinas']}
        for room in data['salas']:
            for lecture in timetable.lectures:
                if uses(subjects[lecture.subject], room):
                    lecture.room = room['sala']

    # H0: a timetable from scratch, with as few holes as possible (O1)
    def generate_timetable(data):
        model, x, holes = build_model(data)
        model.minimize(sum(holes))
        return solve(model, x, data)

    # R9: H1 for `data`, starting from `previous` (H0) and moving as few of its lectures as possible
    def regenerate_timetable(previous, data):
        model, x, holes = build_model(data)
        before = {(lecture.grade, lecture.subject, lecture.at.day, lecture.at.slot)
                  for lecture in previous.lectures}
        # the search starts from H0...
        for key, chosen in x.items():
            model.add_hint(chosen, key in before)
        # ... and keeps as many of its lectures at the same time as it can
        model.maximize(sum(chosen for key, chosen in x.items() if key in before))
        return solve(model, x, data)

    return (
        build_model,
        generate_timetable,
        regenerate_timetable,
        unavailable_periods,
        uses,
    )


@app.cell
def _(unavailable_periods, uses):
    from collections import Counter, defaultdict

    # R1–R7 checked directly on the lectures of a timetable, without the model
    def check_requirements(data, timetable):
        lectures = timetable.lectures
        subjects = {subject['disciplina']: subject for subject in data['disciplinas']}
        rooms = {room['sala']: room for room in data['salas']}
        unavailable = unavailable_periods(data)

        grade_busy = Counter((lecture.grade, lecture.at) for lecture in lectures)
        teacher_busy = Counter((lecture.professor, lecture.at) for lecture in lectures)
        room_busy = Counter((lecture.room, lecture.at) for lecture in lectures)
        per_week = Counter((lecture.grade, lecture.subject) for lecture in lectures)
        # the slots of each subject on each day, for each grade
        per_day = defaultdict(list)
        for lecture in lectures:
            per_day[lecture.grade, lecture.subject, lecture.at.day].append(lecture.at.slot)

        def double(name):
            return subjects[name]['duplo_periodo'] == 'sim'

        return {
            'R1': all(n == 1 for n in grade_busy.values()),
            'R2': all(per_week[grade['turma'], subject['disciplina']] == int(subject['carga_semanal'])
                      for grade in data['turmas'] for subject in data['disciplinas']),
            'R3': all(len(slots) <= (2 if double(name) else 1)
                      for (grade, name, day), slots in per_day.items()),
            'R4': all(len(slots) == 2 and abs(slots[0] - slots[1]) == 1
                      for (grade, name, day), slots in per_day.items() if double(name)),
            'R5': all(n == 1 for n in teacher_busy.values()),
            'R6': all((lecture.professor, lecture.at.day, lecture.at.slot) not in unavailable
                      for lecture in lectures),
            'R7': all(lecture.room in rooms and uses(subjects[lecture.subject], rooms[lecture.room])
                      for lecture in lectures)
                  and all(n <= int(rooms[room]['quantidade']) for (room, at), n in room_busy.items()),
        }

    # O1 recounted on the timetable: free slots between a teacher's first and last lecture of a day
    def count_holes(timetable):
        busy = defaultdict(set)
        for lecture in timetable.lectures:
            busy[lecture.professor, lecture.at.day].add(lecture.at.slot)
        return sum(max(slots) - min(slots) + 1 - len(slots) for slots in busy.values())

    # R9: lectures of `before` that are not in `after` at the same time and in the same room
    def count_changes(before, after):
        return sum(lecture not in after.lectures for lecture in before.lectures)

    return check_requirements, count_changes, count_holes


@app.cell(hide_code=True)
def _(build_model, count_holes, generate_timetable, get_data, mo, w):
    from inspect import getsource
    from textwrap import dedent

    mo.stop(w.value["clicks"] == 0)
    data = get_data('./dados/')
    try:
        assert_data('./dados/', data)
    except ValueError as _error:
        mo.stop(True, mo.callout(str(_error), kind="danger"))
    h0 = generate_timetable(data)
    mo.stop(h0 is None, mo.callout("O solver não encontrou um horário válido.", kind="danger"))

    _source = mo.ui.code_editor(dedent(getsource(build_model)), language="python", disabled=True)
    _holes = count_holes(h0)
    mo.vstack([
        mo.md(f"""
        <details>
        <summary style="cursor: pointer"><code>build_model(data)</code></summary>
        {_source}
        </details>

        Os dados de 📁 <code>dados/</code> são lidos e validados por <code>assert_data</code>.
        O modelo tem uma variável booleana <code>x[turma, disciplina, dia, tempo]</code>,
        verdadeira quando a turma tem essa disciplina nesse tempo. <br />
        Para cada turma, há no máximo uma aula em cada tempo (R1) e, para cada disciplina,
        a carga semanal é exata (R2), há no máximo uma aula por dia (R3) ou, em duplo período,
        0 ou 2 tempos seguidos (R4), e nenhuma aula quando o professor está indisponível (R6). <br />
        Depois, olhando para todas as turmas juntas, um professor dá no máximo uma aula de cada
        vez (R5) e, em cada tempo, nenhum tipo de sala tem mais aulas do que salas (R7).
        O solver minimiza os buracos nos horários dos professores (O1). <br />
        Por fim, cada aula recebe a sua sala: a <code>sala_especial</code> da disciplina ou,
        se estiver vazia, a sala normal.
        """),
        h0,
        mo.md(f"**{_holes}** {'buraco' if _holes == 1 else 'buracos'} nos horários dos professores, "
              f"encontrado em {h0.seconds:.2f} s."),
    ])
    return data, h0


@app.cell(hide_code=True)
def _(count_changes, generate_timetable, get_data, h0, mo, regenerate_timetable):
    data_v2 = get_data('./dados_v2/')
    assert_data('./dados_v2/', data_v2)
    h1 = regenerate_timetable(h0, data_v2)
    h1_scratch = generate_timetable(data_v2)
    mo.stop(h1 is None or h1_scratch is None,
            mo.callout("O solver não encontrou um horário válido para dados_v2/.", kind="danger"))
    h1.previous = h0
    _n = len(h0.lectures)
    _note = ("Neste H0, nenhuma aula calhou nos tempos que <code>dados_v2/</code> retira à Prof. Ana, "
             "por isso nenhuma tem de mudar e H1 incremental é igual a H0."
             if count_changes(h0, h1) == 0 else "")

    mo.vstack([
        mo.md(f"""
        ## Construção incremental (R9)

        H1 é gerado para 📁 <code>dados_v2/</code> com o mesmo modelo, mas a partir de H0:

        1. H0 é dado ao solver como <em>hint</em>, isto é, como ponto de partida da procura.
        2. Em vez de minimizar os buracos (O1), o solver maximiza o número de aulas de H0 que
           ficam no mesmo tempo (a sala depende só da disciplina, por isso também se mantém).

        Como só os dados mudam, o mesmo processo serve para qualquer alteração: um professor
        indisponível (ou disponível) em mais tempos, uma sala avariada, uma turma nova, um
        professor substituído.

        | | Tempo | Aulas de H0 alteradas (tempo ou sala) |
        |---|---|---|
        | Incremental, a partir de H0 | {h1.seconds:.3f} s | {count_changes(h0, h1)} de {_n} |
        | Do zero, sem H0 | {h1_scratch.seconds:.3f} s | {count_changes(h0, h1_scratch)} de {_n} |

        {_note}

        H1 incremental, com as aulas que mudaram em relação a H0 a tracejado:
        """),
        h1,
    ])
    return data_v2, h1, h1_scratch


@app.cell(hide_code=True)
def _(
    check_requirements,
    count_holes,
    data,
    data_v2,
    generate_timetable,
    get_data,
    h0,
    h1,
    h1_scratch,
    mo,
):
    _data_test = get_data('./dados_teste/')
    assert_data('./dados_teste/', _data_test)
    _test = generate_timetable(_data_test)

    _columns = {
        'H0 · <code>dados/</code>': ('dados/', data, h0),
        'H1 incremental · <code>dados_v2/</code>': ('dados_v2/', data_v2, h1),
        'H1 do zero · <code>dados_v2/</code>': ('dados_v2/', data_v2, h1_scratch),
        'Teste · <code>dados_teste/</code>': ('dados_teste/', _data_test, _test),
    }
    _requirements = {
        'R1': 'uma aula de cada vez por turma',
        'R2': 'carga semanal exata',
        'R3': 'no máximo uma aula por dia de cada disciplina',
        'R4': 'duplo período em blocos de 2 tempos',
        'R5': 'um professor numa aula de cada vez',
        'R6': 'disponibilidade dos professores',
        'R7': 'salas do tipo certo, sem exceder a quantidade',
    }
    _checks = {_column: check_requirements(_data, _timetable) if _timetable else None
               for _column, (_, _data, _timetable) in _columns.items()}

    _table = '| Requisito | ' + ' | '.join(_columns) + ' |\n|---|' + '---|' * len(_columns) + '\n'
    for _requirement, _label in _requirements.items():
        _table += (f'| **{_requirement}** {_label} | '
                   + ' | '.join(('✅' if _checks[_column][_requirement] else '❌') if _checks[_column] else '—'
                                for _column in _columns) + ' |\n')
    _table += ('| **R8** dados lidos dos CSV de | '
               + ' | '.join(f'📁 <code>{_folder}</code>' for _folder, _, _ in _columns.values()) + ' |\n')
    _table += ('| **O1** buracos (recontados) | '
               + ' | '.join(str(count_holes(_timetable)) if _timetable else '—'
                            for _, _, _timetable in _columns.values()) + ' |\n')

    mo.vstack([
        mo.md("""
        ## Verificação dos requisitos

        <code>check_requirements</code> verifica cada horário diretamente, sem usar o modelo:
        relê os CSV e confirma R1–R7 aula a aula (O1 é recontado da mesma forma).
        <code>dados_teste/</code> é um conjunto de dados diferente (3 turmas, mais uma disciplina
        de duplo período e a Prof. Diana indisponível às quartas): o mesmo código gera um horário
        válido para ele, porque nada dos dados está no código (R8).
        """),
        mo.md(_table),
        mo.accordion({'Horário gerado para dados_teste/': _test}),
    ])
    return


if __name__ == "__main__":
    app.run()
