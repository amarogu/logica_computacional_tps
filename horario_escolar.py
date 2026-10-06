# /// script
# dependencies = ["anywidget", "marimo"]
# requires-python = ">=3.14"
# ///

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
def _():
    from pathlib import Path
    import csv

    # https://claude.ai/code/session_01F7LZyQp7Dv7GgNpcerp6aS
    def get_data(from_folder):
        data = {}
        for file in Path(from_folder).rglob('*.csv'):
            with file.open(encoding='utf-8', newline='') as f:
                data[file.stem] = list(csv.DictReader(f))
        return data

    return Path, get_data


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
def _(get_data, mo):
    from ortools.sat.python import cp_model
    from inspect import getsource
    from textwrap import dedent
    from html import escape
    from collections import defaultdict, namedtuple

    DAYS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex']

    # (professor, day, slot) of the rows of disponibilidade_excecoes.csv or preferencias.csv
    def periods(rows):
        return {(row['professor'], DAYS.index(row['dia']), int(row['periodo']) - 1) for row in rows}

    # R7: subjects without sala_especial share the normal rooms
    def room_pool(subject):
        return subject['sala_especial'] or 'normal'

    # R7: the rooms of each pool, one per unit of quantidade (Sala Normal 1, Sala Normal 2, …)
    def room_names(data):
        names = defaultdict(list)
        for row in data['salas']:
            quantity = int(row['quantidade'])
            pool = 'normal' if row['tipo'] == 'normal' else row['sala']
            names[pool] += ([row['sala']] if quantity == 1
                            else [f"{row['sala']} {n}" for n in range(1, quantity + 1)])
        return names

    # https://claude.ai/code/session_01LGQikCyDfhpbSp5UqZvVCw
    def generate_timetable(from_folder='./dados/'):
        data = get_data(from_folder)
        try:
            assert_data(from_folder, data=data)
        except ValueError as e:
            mo.output.replace(mo.callout(str(e), kind="danger"))
            return
        source = mo.ui.code_editor(
            '\n'.join(dedent(getsource(method))
                      for method in (TimetableModel.__init__, TimetableModel.minimize_holes)),
            language="python", disabled=True
        )
        mo.output.append(mo.md(f"""
            <details>
            <summary style="cursor: pointer"><code>TimetableModel(data)</code></summary>
            {source}
            </details>

            A função inicia com o carregamento dos dados de 📁 <code>from_folder</code>,
            em seguida os ficheiros são validados por <code>assert_data</code> e um modelo é
            inicializado.
            Então, <b>constraints</b> são aplicados: <code>times</code>. <br />
            Estes constraints definem os slots e dias "máximos" que poderão ser encontrados pelo solver.
            Cada bloco só pode começar num tempo em que o professor está disponível durante todo o
            bloco (R6), um professor dá no máximo uma aula de cada vez (R5) e, em cada tempo, nenhum
            tipo de sala tem mais aulas do que salas (R7). <br />
            O solver minimiza os buracos nos horários dos professores (O1) e, se existir
            <code>preferencias.csv</code> (mesmo formato de <code>disponibilidade_excecoes.csv</code>),
            as aulas em tempos que o professor prefere evitar.
            Um buraco pesa mais do que todas essas aulas juntas, para que O1 tenha sempre prioridade. <br />
            Com os tempos decididos, um segundo modelo, mais pequeno, atribui a cada aula uma sala
            concreta (ex.: Sala Normal 3), sem duas aulas na mesma sala ao mesmo tempo.
        """))
        timetable_model = TimetableModel(data)
        timetable_model.minimize_holes()
        timetable = timetable_model.solve()
        if timetable is None:
            mo.output.append(mo.callout("O solver não encontrou um horário válido.", kind="danger"))
            return
        mo.output.append(timetable)
        solver = timetable_model.solver
        n_holes = solver.value(sum(timetable_model.holes))
        n_unwanted = solver.value(sum(timetable_model.unwanted))
        result = f"**{n_holes}** {'buraco' if n_holes == 1 else 'buracos'} nos horários dos professores"
        if data.get('preferencias'):
            result += (f" e **{n_unwanted}** {'aula' if n_unwanted == 1 else 'aulas'}"
                       " em tempos que o professor prefere evitar")
        if solver.response_proto.status == cp_model.OPTIMAL:
            result += f": solução ótima, encontrada em {solver.wall_time:.2f} s."
        else:
            result += f": melhor solução encontrada em {solver.wall_time:.2f} s, sem prova de que é ótima."
        mo.output.append(mo.md(result))
        return timetable

    # one block of consecutive periods of a subject for a grade (2 periods when duplo_periodo)
    Block = namedtuple('Block', 'grade subject length slot day placements')

    class TimetableModel:
        def __init__(self, data):
            self.data = data
            self.model = model = cp_model.CpModel()
            self.blocks = []
            self.previous = None
            # R6: periods in which the teacher can't teach
            unavailable = periods(data['disponibilidade_excecoes'])
            # R7: how many rooms each pool has
            capacity = {pool: len(names) for pool, names in room_names(data).items()}
            # R5 and O1: teaching[professor, day, slot] lists the booleans of the blocks that may cover that period
            teaching = defaultdict(list)
            # R7: occupying[pool, day, slot], the same for each pool of rooms
            occupying = defaultdict(list)
            for grade in data['turmas']:
                times = []
                for subject in data['disciplinas']:
                    length = 2 if subject['duplo_periodo'] == 'sim' else 1
                    # R6: a block may only start where its teacher is available for all its periods
                    starts = [(d, s) for d in range(5) for s in range(6 - length)
                              if all((subject['professor'], d, s + k) not in unavailable
                                     for k in range(length))]
                    days = []
                    for i in range(int(subject['carga_semanal']) // length):
                        name = f'{grade['turma']}_{subject['disciplina']}_{i}'
                        # R4: a double block starts early enough to end on the same day
                        slot = model.new_int_var(0, 5 - length, f'slot_{name}')
                        day = model.new_int_var(0, 4, f'day_{name}')
                        model.add_allowed_assignments([day, slot], starts)
                        days.append(day)
                        times += [day * 5 + slot + k for k in range(length)]
                        # one boolean per allowed start, true where the block is placed
                        placements = {}
                        for d, s in starts:
                            at = model.new_bool_var(f'{name}_at_{d}_{s}')
                            model.add(day == d).only_enforce_if(at)
                            model.add(slot == s).only_enforce_if(at)
                            placements[d, s] = at
                            for k in range(length):
                                teaching[subject['professor'], d, s + k].append(at)
                                occupying[room_pool(subject), d, s + k].append(at)
                        model.add_exactly_one(placements.values())
                        self.blocks.append(
                            Block(grade['turma'], subject['disciplina'], length, slot, day, placements)
                        )
                    # R3: increasing days, which also rules out symmetric solutions
                    for earlier, later in zip(days, days[1:]):
                        model.add(earlier < later)
                # https://claude.ai/code/session_01YEQ5gktWofWoRzXQcxMRHU
                # R1: no two lectures of the same grade at the same time
                model.add_all_different(times)

            # R5: a teacher gives at most one lecture at a time
            for blocks in teaching.values():
                model.add_at_most_one(blocks)
            # R7: never more lectures in a pool of rooms than rooms in it
            for (pool, d, s), blocks in occupying.items():
                model.add(sum(blocks) <= capacity.get(pool, 0))

            # O1: thanks to R5, a teacher teaches 0 or 1 lectures in each period
            busy = {key: sum(blocks) for key, blocks in teaching.items()}
            # O1: a free period with a lecture before and after it, on the same day, is a hole
            self.holes = []
            for teacher in dict.fromkeys(subject['professor'] for subject in data['disciplinas']):
                for d in range(5):
                    day_busy = [busy.get((teacher, d, p), 0) for p in range(5)]
                    for p in range(1, 4):
                        hole = model.new_bool_var(f'hole_{teacher}_{d}_{p}')
                        for q in range(p):
                            for r in range(p + 1, 5):
                                model.add(hole >= day_busy[q] + day_busy[r] - day_busy[p] - 1)
                        self.holes.append(hole)
            # bonus: lectures in periods the teacher would rather not teach (preferencias.csv)
            self.unwanted = [busy[key] for key in periods(data.get('preferencias', [])) if key in busy]

        # O1 comes first: one hole costs more than all the unwanted lectures together
        def minimize_holes(self):
            self.model.minimize((len(self.unwanted) + 1) * sum(self.holes) + sum(self.unwanted))

        # R9: keep as many lectures of `previous` at the same time as possible, the `fixed` ones always
        def minimize_changes(self, previous, fixed):
            self.previous = previous
            kept = []
            for lecture in previous.lectures:
                same_time = [block.placements[lecture.day, lecture.slot] for block in self.blocks
                             if (block.grade, block.subject, block.length)
                             == (lecture.grade, lecture.subject, lecture.length)
                             and (lecture.day, lecture.slot) in block.placements]
                if lecture in fixed:
                    self.model.add(sum(same_time) == 1)
                kept += same_time
            self.model.maximize(sum(kept))
            # R9: the search also starts from `previous` (R3 orders each subject's blocks by day)
            hints = defaultdict(list)
            for lecture in sorted(previous.lectures, key=lambda lecture: lecture.day):
                hints[lecture.grade, lecture.subject].append(lecture)
            for block in self.blocks:
                if hints[block.grade, block.subject]:
                    lecture = hints[block.grade, block.subject].pop(0)
                    self.model.add_hint(block.day, lecture.day)
                    self.model.add_hint(block.slot, lecture.slot)

        # Função helper que resolve o modelo
        # https://claude.ai/code/session_018Mnky33mFUeEiM8PaRGXkP
        def solve(self):
            self.solver = cp_model.CpSolver()
            # O1 needn't be optimal: after 10 s, keep the best timetable found so far
            self.solver.parameters.max_time_in_seconds = 10
            status = self.solver.solve(self.model)
            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                return None
            timetable = Timetable([
                Lecture(block.subject, None, block.grade, self.solver.value(block.slot),
                        self.solver.value(block.day), block.length)
                for block in self.blocks
            ])
            if not assign_rooms(self.data, timetable, self.previous):
                return None
            return timetable

    # R7: with the times decided, a second (small) model gives each lecture a room of its pool,
    # never two lectures in the same room at once. R7's limit on each pool guarantees this exists.
    # R9: lectures that kept their time from `previous` keep their room whenever possible.
    # https://claude.ai/code/session_01LGQikCyDfhpbSp5UqZvVCw
    def assign_rooms(data, timetable, previous=None):
        subjects = {subject['disciplina']: subject for subject in data['disciplinas']}
        rooms = room_names(data)
        model = cp_model.CpModel()
        choices = []
        in_room = defaultdict(list)
        for i, lecture in enumerate(timetable.lectures):
            choice = {room: model.new_bool_var(f'{i}_{room}')
                      for room in rooms[room_pool(subjects[lecture.subject])]}
            model.add_exactly_one(choice.values())
            for room, chosen in choice.items():
                for k in range(lecture.length):
                    in_room[room, lecture.day, lecture.slot + k].append(chosen)
            choices.append(choice)
        for lectures in in_room.values():
            model.add_at_most_one(lectures)
        if previous is not None:
            before = {lecture.key(): lecture.classroom for lecture in previous.lectures}
            preferred = [before.get(lecture.key()) for lecture in timetable.lectures]
        else:
            # without a previous timetable, each grade stays in one normal room when it can
            grades = list(dict.fromkeys(lecture.grade for lecture in timetable.lectures))
            normal = rooms['normal'] or [None]
            preferred = [normal[grades.index(lecture.grade) % len(normal)] for lecture in timetable.lectures]
        model.maximize(sum(choice.get(room, 0) for room, choice in zip(preferred, choices)))
        solver = cp_model.CpSolver()
        if solver.solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return False
        for lecture, choice in zip(timetable.lectures, choices):
            lecture.classroom = next(room for room, chosen in choice.items() if solver.value(chosen))
        return True

    # R9: H1 for `data`, built from `previous` (H0) and changing as few of its lectures as possible
    # https://claude.ai/code/session_01LGQikCyDfhpbSp5UqZvVCw
    def regenerate_timetable(previous, data):
        # the lectures of H0 that break a requirement under the new data have to change
        broken = {lecture for issues in check_requirements(data, previous).values()
                  for _, lectures in issues for lecture in lectures}
        unaffected = set(previous.lectures) - broken
        # fix all the other lectures; if that makes the problem impossible, let any lecture change
        for fixed in (unaffected, set()):
            timetable_model = TimetableModel(data)
            timetable_model.minimize_changes(previous, fixed)
            timetable = timetable_model.solve()
            if timetable is not None:
                return timetable, len(fixed)
        return None, 0

    # R9: lectures of `previous` that are no longer at the same time and in the same room
    def count_changes(previous, timetable):
        before = {(lecture.key(), lecture.classroom) for lecture in previous.lectures}
        after = {(lecture.key(), lecture.classroom) for lecture in timetable.lectures}
        return len(before - after)

    # R1–R7 checked on the timetable itself, without the model: {requirement: [(problem, lectures)]}
    def check_requirements(data, timetable):
        subjects = {subject['disciplina']: subject for subject in data['disciplinas']}
        grades = [grade['turma'] for grade in data['turmas']]
        unavailable = periods(data['disponibilidade_excecoes'])
        rooms = room_names(data)
        issues = {f'R{n}': [] for n in range(1, 8)}
        # who has a lecture in each period: (requirement, grade/teacher/room, day, slot) -> lectures
        occupied = defaultdict(list)
        for lecture in timetable.lectures:
            subject = subjects.get(lecture.subject)
            if subject is None or lecture.grade not in grades:
                issues['R2'].append((f"{lecture.grade}: {lecture.subject} não está nos dados", [lecture]))
                continue
            teacher = subject['professor']
            if (lecture.length != (2 if subject['duplo_periodo'] == 'sim' else 1)
                    or not 0 <= lecture.slot <= 5 - lecture.length):
                issues['R4'].append((f"{lecture.grade}: {lecture.subject} em {lecture.length} tempo(s) "
                                     f"a partir do {lecture.slot + 1}º", [lecture]))
            room_ok = lecture.classroom in rooms[room_pool(subject)]
            if not room_ok:
                issues['R7'].append((f"{lecture.grade}: {lecture.subject} na sala {lecture.classroom}",
                                     [lecture]))
            for k in range(lecture.length):
                d, s = lecture.day, lecture.slot + k
                occupied['R1', lecture.grade, d, s].append(lecture)
                occupied['R5', teacher, d, s].append(lecture)
                if room_ok:
                    occupied['R7', lecture.classroom, d, s].append(lecture)
                if (teacher, d, s) in unavailable:
                    issues['R6'].append((f"{teacher} indisponível em {DAYS[d]} {s + 1}º "
                                         f"({lecture.grade}: {lecture.subject})", [lecture]))
        for (requirement, who, d, s), lectures in occupied.items():
            if len(lectures) > 1:
                issues[requirement].append((f"{who} com {len(lectures)} aulas em {DAYS[d]} {s + 1}º",
                                            lectures))
        for grade in grades:
            for subject in data['disciplinas']:
                lectures = [lecture for lecture in timetable.lectures
                            if (lecture.grade, lecture.subject) == (grade, subject['disciplina'])]
                taught = sum(lecture.length for lecture in lectures)
                if taught != int(subject['carga_semanal']):
                    issues['R2'].append((f"{grade}: {subject['disciplina']} com {taught} "
                                         f"de {subject['carga_semanal']} tempos", lectures))
                for d in range(5):
                    same_day = [lecture for lecture in lectures if lecture.day == d]
                    if len(same_day) > 1:
                        issues['R3'].append((f"{grade}: {len(same_day)} aulas de {subject['disciplina']} "
                                             f"à {DAYS[d]}", same_day))
        return issues

    # O1 recounted on the timetable: free periods between a teacher's first and last lecture of a day
    def count_holes(data, timetable):
        teachers = {subject['disciplina']: subject['professor'] for subject in data['disciplinas']}
        busy = defaultdict(set)
        for lecture in timetable.lectures:
            busy[teachers[lecture.subject], lecture.day].update(
                range(lecture.slot, lecture.slot + lecture.length))
        return sum(max(slots) - min(slots) + 1 - len(slots) for slots in busy.values())

    class Lecture:
        def __init__(self, subject, classroom, grade, slot, day, length):
            self.subject = subject
            self.classroom = classroom
            self.grade = grade
            self.slot = slot
            self.day = day
            self.length = length

        # R9: the same lecture, at the same time, in two timetables
        def key(self):
            return (self.grade, self.subject, self.day, self.slot, self.length)

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

        def __init__(self, lectures):
            self.days = DAYS
            self.lectures = lectures
            # R9: when set, lectures that are not in `previous` (same time and room) are outlined
            self.previous = None

        # Uma tabela por turma, com os tempos nas linhas e os dias nas colunas
        def _repr_html_(self):
            subjects = dict.fromkeys(lecture.subject for lecture in self.lectures)
            # each subject keeps the same colour across grades
            hues = {subject: 360 * i // len(subjects) for i, subject in enumerate(subjects)}
            before = ({(lecture.key(), lecture.classroom) for lecture in self.previous.lectures}
                      if self.previous else None)
            tables = []
            for grade in dict.fromkeys(lecture.grade for lecture in self.lectures):
                cells = {(lecture.day, lecture.slot): lecture
                         for lecture in self.lectures if lecture.grade == grade}
                # R4: a double block's rowspan also fills the period below it
                covered = {(day, slot + k) for (day, slot), lecture in cells.items()
                           for k in range(1, lecture.length)}
                rows = ''
                for slot in range(5):
                    rows += f'<tr><th>{slot + 1}º</th>'
                    for day in range(len(self.days)):
                        lecture = cells.get((day, slot))
                        if lecture is not None:
                            room = f'<small>{escape(lecture.classroom)}</small>' if lecture.classroom else ''
                            changed = (' class="changed"' if before is not None
                                       and (lecture.key(), lecture.classroom) not in before else '')
                            rows += (f'<td rowspan="{lecture.length}" style="--hue: {hues[lecture.subject]}"'
                                     f'{changed}>{escape(lecture.subject)}{room}</td>')
                        elif (day, slot) not in covered:
                            rows += '<td></td>'
                    rows += '</tr>'
                header = ''.join(f'<th>{day}</th>' for day in self.days)
                tables.append(f'<table><caption>Turma {escape(grade)}</caption>'
                              f'<tr><th></th>{header}</tr>{rows}</table>')
            return f'<style>{self.css}</style><div class="timetables" lang="pt">{''.join(tables)}</div>'

    return (
        TimetableModel,
        check_requirements,
        count_changes,
        count_holes,
        generate_timetable,
        regenerate_timetable,
    )


@app.cell(hide_code=True)
def _(generate_timetable, w):
    h0 = generate_timetable() if w.value["clicks"] > 0 else None
    return (h0,)


@app.cell(hide_code=True)
def _(
    Path,
    TimetableModel,
    check_requirements,
    count_changes,
    get_data,
    h0,
    mo,
    regenerate_timetable,
):
    from time import perf_counter

    mo.stop(h0 is None)

    # H1 built from H0, and H1 from scratch (as H0 was), each timed
    def _compare(data):
        start = perf_counter()
        incremental, fixed = regenerate_timetable(h0, data)
        incremental_time = perf_counter() - start
        start = perf_counter()
        scratch_model = TimetableModel(data)
        scratch_model.minimize_holes()
        scratch = scratch_model.solve()
        return incremental, fixed, incremental_time, scratch, perf_counter() - start

    data_v2 = get_data('./dados_v2/')
    assert_data('./dados_v2/', data_v2)
    h1, _fixed, _incremental, h1_scratch, _scratch = _compare(data_v2)
    mo.stop(h1 is None or h1_scratch is None,
            mo.callout("O solver não encontrou um horário válido para dados_v2/.", kind="danger"))
    h1.previous = h0
    _n = len(h0.lectures)
    _changes = count_changes(h0, h1)
    _note = ("Neste H0, nenhuma aula calhou nos tempos que <code>dados_v2/</code> retira à Prof. Ana, "
             "por isso nenhuma tem de mudar e H1 incremental é igual a H0. "
             "Os cenários seguintes mostram H0 a ser mesmo reparado."
             if _changes == 0 else "")

    # other kinds of change: each folder of cenarios/ is dados/ with one change
    _rows = ''
    for _folder in sorted(Path('./cenarios').iterdir()) if Path('./cenarios').is_dir() else []:
        _data = get_data(_folder)
        try:
            assert_data(_folder, _data)
        except ValueError as _error:
            _rows += f'| <code>{_folder.name}</code> | {_error} | | | |\n'
            continue
        _h1, _kept_fixed, _t_incremental, _h1_scratch, _t_scratch = _compare(_data)
        if _h1 is None:
            _rows += f'| <code>{_folder.name}</code> | sem horário possível | | | |\n'
            continue
        _valid = not any(check_requirements(_data, _h1).values())
        _rows += (f'| <code>{_folder.name}</code> | {_kept_fixed} de {_n} '
                  f'| {_t_incremental:.3f} s · {count_changes(h0, _h1)} alteradas '
                  f'| {_t_scratch:.3f} s · {count_changes(h0, _h1_scratch)} alteradas '
                  f'| {"✅" if _valid else "❌"} |\n')
    _scenarios = ('| Alteração (📁 <code>cenarios/</code>) | Aulas fixas | Incremental | Do zero '
                  '| H1 incremental cumpre R1–R7 |\n|---|---|---|---|---|\n' + _rows)

    mo.vstack([
        mo.md(f"""
        ## Construção incremental (R9)

        H1 é gerado para 📁 <code>dados_v2/</code> a partir de H0, em vez de começar do zero:

        1. H0 é verificado com os novos dados, com <code>check_requirements</code> (a verificação
           da secção seguinte). As aulas envolvidas numa violação ficam livres; todas as outras
           ficam fixas no tempo que tinham em H0.
        2. O solver recoloca só as aulas livres, maximizando as que voltam ao tempo de H0, e usa
           H0 como <em>hint</em>.
        3. Se fixar as outras aulas tornar o problema impossível, resolve o modelo completo, com a
           mesma maximização e o mesmo <em>hint</em>.
        4. As salas são atribuídas a seguir, mantendo cada aula na sala de H0 sempre que possível.

        Como as aulas a soltar vêm da verificação dos requisitos, o mesmo processo serve para
        qualquer alteração dos dados: um professor indisponível (ou disponível) em mais tempos,
        uma sala avariada, uma turma nova, um professor substituído.

        | | Tempo | Aulas de H0 alteradas (tempo ou sala) |
        |---|---|---|
        | Incremental ({_fixed} de {_n} aulas fixas) | {_incremental:.3f} s | {_changes} de {_n} |
        | Do zero, sem H0 | {_scratch:.3f} s | {count_changes(h0, h1_scratch)} de {_n} |

        {_note}

        H1 incremental, com as aulas que mudaram em relação a H0 a tracejado:
        """),
        h1,
        mo.md("""
        ### Outras alterações

        Cada pasta de 📁 <code>cenarios/</code> é <code>dados/</code> com uma única alteração:
        a Prof. Ana deixa de poder dar aulas às sextas (<code>ana_indisponivel_sexta</code>),
        Inglês passa da Prof. Diana para a Prof. Ana (<code>ingles_passa_para_ana</code>),
        entra a turma 7ºC (<code>nova_turma_7C</code>) e só fica uma das 6 salas normais
        (<code>so_uma_sala_normal</code>). As aulas alteradas contam em relação ao mesmo H0.
        """),
        mo.md(_scenarios),
    ])
    return data_v2, h1, h1_scratch


@app.cell(hide_code=True)
def _(
    TimetableModel,
    check_requirements,
    count_holes,
    data_v2,
    get_data,
    h0,
    h1,
    h1_scratch,
    mo,
):
    mo.stop(h0 is None)
    _data_test = get_data('./dados_teste/')
    assert_data('./dados_teste/', _data_test)
    _test_model = TimetableModel(_data_test)
    _test_model.minimize_holes()
    _test = _test_model.solve()

    _columns = {
        'H0 · <code>dados/</code>': ('dados/', get_data('./dados/'), h0),
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
        'R7': 'salas do tipo certo, sem duas aulas na mesma sala',
    }
    _issues = {_column: check_requirements(_data, _timetable) if _timetable else None
               for _column, (_, _data, _timetable) in _columns.items()}

    def _verdict(issues):
        if not issues:
            return '✅'
        return f'❌ {len(issues)}: {issues[0][0]}'

    _table = '| Requisito | ' + ' | '.join(_columns) + ' |\n|---|' + '---|' * len(_columns) + '\n'
    for _requirement, _label in _requirements.items():
        _table += (f'| **{_requirement}** {_label} | '
                   + ' | '.join(_verdict(_issues[_column][_requirement]) if _issues[_column] else '—'
                                for _column in _columns) + ' |\n')
    _table += ('| **R8** dados lidos dos CSV de | '
               + ' | '.join(f'📁 <code>{_folder}</code>' for _folder, _, _ in _columns.values()) + ' |\n')
    _table += ('| **O1** buracos (recontados) | '
               + ' | '.join(str(count_holes(_data, _timetable)) if _timetable else '—'
                            for _, _data, _timetable in _columns.values()) + ' |\n')

    mo.vstack([
        mo.md("""
        ## Verificação dos requisitos

        <code>check_requirements</code> verifica cada horário diretamente, sem usar o modelo:
        relê os CSV e confirma R1–R7 aula a aula (O1 é recontado da mesma forma).
        <code>dados_teste/</code> é um conjunto de dados diferente (3 turmas, mais uma disciplina
        de duplo período, a Prof. Diana indisponível às quartas e sem <code>preferencias.csv</code>):
        o mesmo código gera um horário válido para ele, porque nada dos dados está no código (R8).
        """),
        mo.md(_table),
        mo.accordion({'Horário gerado para dados_teste/': _test}),
    ])
    return


if __name__ == "__main__":
    app.run()
