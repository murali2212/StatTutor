# StatTutor: Project Status

**Current phase:** 3 (study materials and search) finished. Next: topic progress, practice questions with answer checking.

## Built and tested (51 automated tests + headless-browser runs of every screen)
- Your data is loaded: syllabus UST24E01J (5 units, 32 topics), CT-1 (6 questions, answer any 4 = 40 marks) and CT-2 (13 questions, 50 marks, OR options not double counted, including the new Q11 page)
- Study materials: add PDF/TXT/MD or pasted notes. They are split into passages and searched offline (SQLite FTS5, ranked by BM25). Your syllabus and both papers are indexed automatically.
- Tutor "training": every question searches your materials, the best passages go to the AI as study text, and the reply names the source ("From your materials: [S1] ..."). Material text cannot give the AI orders (tested).
- Follow-ups like "I don't understand" search with your previous question, so the right passages still arrive
- System check screen (data loaded, search works, calculator correct, key ready) and a "Test the AI now" button
- Everything from earlier phases: Enter sends, key page opens by itself when there is no key or the limit is over, step-by-step calculators checked against scipy, adaptive re-teaching
- start.bat / start.sh launchers

## Things to know
- Free AI models cannot be fine-tuned. The app "trains" by giving the model your syllabus, papers and notes with every question. Answer quality depends on the model you pick.
- The first paper's heading says "Model Practical Examination" but it is treated as your CT-1. Say so if that is wrong.
- Read from photos: check CT-1 Q2 (8 students, 7 pairs shown), CT-1 Q5 numbers, and CT-2 Q10(b) "Above 30" (calculated as 30-35).
- CT-1 Q3 gives table value 2.58; the exact t table value is about 2.72. Same conclusion.

## Not tested against a real provider
- Calls to Gemini, Groq, OpenRouter (the build environment has no internet). Use the live test steps in README.md.

## Not supported yet
- OCR for photos/scans (paste the text). Only the first ~24,000 characters of a paper and 600,000 of a material are read.
- Meaning-based (embedding) search: search is word-based, so use the words your notes use.

## Next
Topic progress (not started / learning / done), practice questions in your paper style with answer checking, mock exam, study planner.
