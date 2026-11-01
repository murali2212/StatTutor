"""Exam pattern analysis. Plain functions over stored data, no AI, so every
number and tip can be traced to the questions that were uploaded."""
from collections import Counter

PAPERS = ("ct1", "ct2", "practical")
LABEL = {"ct1": "CT-1", "ct2": "CT-2", "practical": "the model practical"}
SHORT = {"ct1": "CT-1", "ct2": "CT-2", "practical": "Model practical"}
THEORY = {"theory", "definition"}
ORDER = {"repeated": 0, "once": 1, "untested": 2}
DISCLAIMER = ("These are patterns seen in the papers you uploaded plus your syllabus. "
              "They show where to focus first. They do not predict what the semester paper will contain.")

def _g(x):
    return f"{x:g}"

def analyze(units, questions, meta=None):
    topics = {}
    for u in units:
        for t in u["topics"]:
            topics[t["id"]] = {"id": t["id"], "name": t["name"], "unit": u["name"],
                               "marks": {p: 0.0 for p in PAPERS}, "count": {p: 0 for p in PAPERS}, "types": Counter()}
    totals = {p: {"questions": 0, "marks": 0.0, "numerical": 0.0, "theory": 0.0, "mixed": 0.0} for p in PAPERS}
    unmapped = {"questions": 0, "marks": 0.0}
    missing_marks = 0
    for q in questions:
        p, m = q["paper"], q["marks"]
        if p not in totals:
            continue
        if m is None:
            missing_marks += 1
        m = float(m or 0)
        T = totals[p]
        T["questions"] += 1
        if not q.get("alt"):                     # an OR option is not counted twice in the paper total
            T["marks"] += m
            T["numerical" if q["qtype"] == "numerical" else "theory" if q["qtype"] in THEORY else "mixed"] += m
        t = topics.get(q["topic_id"])
        if t is None:
            unmapped["questions"] += 1
            unmapped["marks"] += m
            continue
        t["marks"][p] += m
        t["count"][p] += 1
        t["types"][q["qtype"]] += m or 1

    for p, T in totals.items():
        m = (meta or {}).get(p) or {}
        T["max_marks"], T["note"] = m.get("max_marks"), m.get("note")
    rows, groups = [], {"repeated": [], "once": [], "untested": []}
    for t in topics.values():
        where = [p for p in PAPERS if t["count"][p] > 0]
        dom = t["types"].most_common(1)[0][0] if t["types"] else None
        level = "repeated" if len(where) >= 2 else "once" if where else "untested"
        groups[level].append(t["name"])
        detail = ", ".join(f"{SHORT[p]} {_g(t['marks'][p])} marks" for p in where)
        style = f"{dom} questions"
        if level == "repeated":
            ev = f"Asked in {len(where)} papers: {detail}, mostly {style}."
            teach = (f'Teach me "{t["name"]}" from zero, step by step. It was asked in {len(where)} of my papers '
                     f'({", ".join(LABEL[p] for p in where)}), mostly as {style}. After teaching, show how to write a full-marks '
                     f'answer and give me 2 practice questions in the same style (no answers yet).')
        elif level == "once":
            ev = f"Asked once: {detail}, mostly {style}."
            teach = (f'Teach me "{t["name"]}" from zero, step by step. It was asked in {LABEL[where[0]]} as {style}. '
                     f'After teaching, show how to write a full-marks answer and give me 2 practice questions in the same style (no answers yet).')
        else:
            ev = "In your syllabus but not asked in the papers you uploaded."
            teach = (f'Teach me "{t["name"]}" from zero, step by step. It is in my syllabus but did not appear in my uploaded papers. '
                     f'After teaching, give me 2 practice questions (no answers yet).')
        rows.append({"id": t["id"], "name": t["name"], "unit": t["unit"], "level": level, "papers": where,
                     "marks": t["marks"], "total_marks": sum(t["marks"].values()), "main_type": dom,
                     "evidence": ev, "teach_prompt": teach})
    rows.sort(key=lambda r: (ORDER[r["level"]], -r["total_marks"], r["name"]))

    tips = []
    total = sum(T["marks"] for T in totals.values())
    if total > 0:
        pct = round(100 * sum(T["numerical"] for T in totals.values()) / total)
        text = (f"{pct}% of the marks in your uploaded papers were numerical, so practise solving problems and writing every step."
                if pct >= 50 else
                f"Only {pct}% of the marks in your uploaded papers were numerical; most marks were theory or definitions, so learn clear written explanations."
                if pct <= 25 else
                f"About {pct}% of the marks in your uploaded papers were numerical and the rest theory, so prepare both.")
        tips.append({"topic": None, "text": text})
    for r in rows:
        if r["level"] == "repeated":
            how = ("practise full numerical solutions with every step written" if r["main_type"] == "numerical"
                   else "learn the definitions and short explanations" if r["main_type"] in THEORY
                   else "prepare both the theory and the calculations")
            tips.append({"topic": r["name"], "text": f"{r['name']}: {r['evidence']} Pattern worth following: {how}."})
    for u in units:
        names = {t["name"] for t in u["topics"]}
        if names and all(r["level"] == "untested" for r in rows if r["name"] in names):
            tips.append({"topic": None, "text": f"Nothing from \"{u['name']}\" appeared in the papers you uploaded. "
                         "The semester paper may still cover it, so check with your teacher and don't skip it."})
    for p in ("ct1", "ct2"):
        if questions and totals[p]["questions"] == 0:
            tips.append({"topic": None, "text": f"{LABEL[p]} has not been uploaded yet. Add it in the Papers tab for a fuller pattern."})
    if unmapped["questions"]:
        tips.append({"topic": None, "text": f"{unmapped['questions']} question(s) ({_g(unmapped['marks'])} marks) are not matched to a topic. "
                     "Match them in the Papers tab for a more accurate analysis."})
    if missing_marks:
        tips.append({"topic": None, "text": f"{missing_marks} question(s) have no marks entered. Fill them in for accurate mark totals."})
    return {"ready": bool(questions), "totals": totals, "groups": groups, "topics": rows,
            "unmapped": unmapped, "tips": tips, "disclaimer": DISCLAIMER, "labels": SHORT}
