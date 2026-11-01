"""The student's real course data, read from the uploaded syllabus (UST24E01J) and
question papers. Loaded once on first run when the database is empty. Everything
here can be edited or replaced from the Papers tab."""
from . import db

SYLLABUS = [
 ("Unit 1: Descriptive statistics, tabulation and averages (CLO-1)", [
   "Nature, scope and limitations of statistics", "Classification and tabulation",
   "Diagrams and graphs (bar, pie, histogram, ogives, Lorenz curve)", "Arithmetic mean", "Median", "Mode",
   "Empirical relation and graphical solution of mean, median, mode"]),
 ("Unit 2: Measures of dispersion, skewness and kurtosis (CLO-2)", [
   "Measures of dispersion: meaning and types", "Range", "Quartile deviation", "Mean deviation",
   "Standard deviation and coefficient of variation", "Skewness (Karl Pearson and Bowley)", "Kurtosis"]),
 ("Unit 3: Correlation and regression (CLO-3)", [
   "Correlation: definition, uses and types", "Karl Pearson's correlation coefficient and its properties",
   "Spearman's rank correlation", "Bivariate distribution", "Regression: definition and uses",
   "Regression coefficients and equations", "Relationship between correlation and regression",
   "Correcting wrongly entered correlation values"]),
 ("Unit 4: Sampling and tests of significance (CLO-4)", [
   "Types of sampling (purposive, random, non-random)", "Parameter, statistic, sampling distribution and standard error",
   "Hypotheses, critical region and one/two-tailed tests", "Large sample tests and test for proportions"]),
 ("Unit 5: Small sample tests, chi-square and ANOVA (CLO-5)", [
   "t-test for single mean", "t-test for two sample means", "F-test for equality of variances",
   "Chi-square goodness of fit", "Chi-square test of independence", "One-way ANOVA"]),
]

# (paper, number, text, marks, type, topic, alt)
QUESTIONS = [
 ("ct1", "1", "Calculate the standard deviation and coefficient of variation. Blood pressure 112, 113, 118, 120, 125, 130 with number of patients 12, 14, 10, 16, 4, 14.", 10, "numerical", "Standard deviation and coefficient of variation", 0),
 ("ct1", "2", "Study hours X = 2,3,4,5,6,7,8 and exam scores Y = 40,45,55,64,75,80,87. Find the regression line of Y on X and estimate the score when X = 5.5.", 10, "numerical", "Regression coefficients and equations", 0),
 ("ct1", "3", "Two salesmen A (20 sales, average Rs 170, SD 20) and B (18 sales, average Rs 205, SD 25). Is there a significant difference in average sales? (Table value of t for 36 df at 1% = 2.58)", 10, "numerical", "t-test for two sample means", 0),
 ("ct1", "4", "A machine should fill 5 kg bags. Ten bags weighed 4.7, 4.9, 5.0, 5.1, 5.4, 5.2, 4.6, 5.1, 4.6, 4.7. Test whether it works properly. (Table value (9, 0.05) = 2.262)", 10, "numerical", "t-test for single mean", 0),
 ("ct1", "5", "Sample I: 5,6,8,1,12,4,3,9,6,10. Sample II: 2,3,6,8,1,10,2,8. Test the significance of the difference between the two sample variances. (Table value (7, 9, 0.05) = 3.29)", 10, "numerical", "F-test for equality of variances", 0),
 ("ct1", "6", "A die rolled 120 times gave face frequencies 15, 18, 22, 20, 25, 20. At the 5% level test whether the die is fair. (Table value (5, 0.05) = 11.07)", 10, "numerical", "Chi-square goodness of fit", 0),
 ("ct2", "1", "Give short note about measures of dispersion.", 2, "theory", "Measures of dispersion: meaning and types", 0),
 ("ct2", "2", "Define mean deviation with coefficient.", 2, "definition", "Mean deviation", 0),
 ("ct2", "3", "Define standard deviation.", 2, "definition", "Standard deviation and coefficient of variation", 0),
 ("ct2", "4", "Find the range for the given Minor students data. Marks 35, 45, 18, 25, 48 with frequencies 3, 4, 5, 4, 3.", 2, "numerical", "Range", 0),
 ("ct2", "5", "Give short note about kurtosis.", 2, "theory", "Kurtosis", 0),
 ("ct2", "6", "Uses of correlation analysis.", 2, "theory", "Correlation: definition, uses and types", 0),
 ("ct2", "7", "Properties of correlation coefficient.", 2, "theory", "Karl Pearson's correlation coefficient and its properties", 0),
 ("ct2", "8", "Define regression and explain regression lines.", 2, "theory", "Regression: definition and uses", 0),
 ("ct2", "9", "What is the relationship between correlation and regression?", 2, "theory", "Relationship between correlation and regression", 0),
 ("ct2", "10(a)", "Calculate quartile deviation and its relative measure. Weight (kg) 28, 30, 40, 45, 22, 20, 35, 48, 50 with number of persons 10, 5, 8, 7, 6, 3, 4, 7, 5.", 16, "numerical", "Quartile deviation", 0),
 ("ct2", "10(b) OR", "Calculate Karl Pearson's coefficient of skewness. Age 0-5, 5-10, 10-15, 15-20, 20-25, 25-30, above 30 with patients 6, 5, 8, 10, 7, 13, 9.", 16, "numerical", "Skewness (Karl Pearson and Bowley)", 1),
 ("ct2", "11(a)", "Ten competitors in a beauty contest are ranked by three judges. J I: 1, 5, 4, 8, 9, 6, 10, 7, 3, 2. J II: 4, 8, 7, 6, 5, 9, 10, 3, 2, 1. J III: 6, 7, 8, 1, 5, 10, 9, 2, 3, 4. Use rank correlation to discuss which pair of judges has the nearest approach to common tastes in beauty.", 16, "numerical", "Spearman's rank correlation", 0),
 ("ct2", "11(b) OR", "Hours studied X = 2, 3, 4, 5, 6, 7 and exam score Y = 40, 45, 50, 55, 60, 65 for six students. Find the regression line of Y on X and estimate the exam score when study hours = 5.5.", 16, "numerical", "Regression coefficients and equations", 1),
]

PAPER_META = {
 "ct1": (40, "Answer any 4 of 6 questions (4 x 10 = 40 marks). The paper heading says Model Practical Examination, II Minor E."),
 "ct2": (50, "Cycle Test II, 17.09.2026, 1.30 hrs. Part A: 9 questions x 2 marks. Part B: 2 questions x 16 marks, each with an OR option."),
}

def _paper_text(paper, title):
    out = [title]
    for pp, num, text, marks, qt, topic, alt in QUESTIONS:
        if pp == paper:
            out.append(f"Question {num} ({marks:g} marks, {qt}): {text}")
    return "\n".join(out)

def seed_materials():
    import os
    from . import materials
    with db.conn() as c:
        if c.execute("SELECT COUNT(*) FROM materials").fetchone()[0]:
            return False
    here = os.path.join(os.path.dirname(__file__), "seed_docs", "syllabus.txt")
    materials.add_material("Syllabus UST24E01J (official)", "syllabus", open(here, encoding="utf-8").read())
    materials.add_material("CT-1 paper (model practical, 40 marks)", "papers", _paper_text("ct1", "CT-1 question paper, UST24E01J Statistical Techniques, answer any four, 10 marks each."))
    materials.add_material("CT-2 paper (17.09.2026, 50 marks)", "papers", _paper_text("ct2", "Cycle Test II question paper, UST24E01J Statistical Techniques, 50 marks."))
    return True

def seed_if_empty():
    with db.conn() as c:
        if c.execute("SELECT COUNT(*) FROM units").fetchone()[0]:
            return False
        ids = {}
        for i, (unit, topics) in enumerate(SYLLABUS):
            uid = c.execute("INSERT INTO units(name, position) VALUES (?,?)", (unit, i)).lastrowid
            for j, t in enumerate(topics):
                ids[t] = c.execute("INSERT INTO topics(unit_id, name, position) VALUES (?,?,?)", (uid, t, j)).lastrowid
        for paper, (mx, note) in PAPER_META.items():
            c.execute("INSERT OR REPLACE INTO paper_meta(paper, max_marks, note) VALUES (?,?,?)", (paper, mx, note))
        if not c.execute("SELECT COUNT(*) FROM questions").fetchone()[0]:
            for paper, num, text, marks, qt, topic, alt in QUESTIONS:
                c.execute("INSERT INTO questions(paper, number, text, marks, qtype, topic_id, alt) VALUES (?,?,?,?,?,?,?)",
                          (paper, num, text, marks, qt, ids[topic], alt))
    return True
