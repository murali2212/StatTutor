# StatTutor: your Statistics tutor (UST24E01J)

## Start it (Windows)
1. Install Python from python.org (tick "Add Python to PATH").
2. Unzip this folder, then double-click **start.bat**. Mac/Linux: run `./start.sh`.
3. Your browser opens at http://localhost:8000. Keep the black window open while you use the app.

## Test it live (about 5 minutes)
1. **Key tab > Run system check.** Everything should say PASS except "API key ready".
2. Get a free key (Gemini: https://aistudio.google.com/apikey, Groq: https://console.groq.com/keys). In the **Key** tab paste it and press **Test and save**, then **Test the AI now**.
3. **Tutor tab.** Ask: `Teach me quartile deviation from zero`. The answer should be in small steps and end with a "From your materials" line naming your CT-2 paper or syllabus.
4. Say `I don't understand`. It must teach the same idea a different way, not repeat itself.
5. **Calc tab > Quartile deviation.** The answer must match what the tutor showed (Q1 = 28, Q3 = 45, QD = 8.5).
6. **Notes tab.** Add a few lines of your own notes, then ask the tutor about them. It should cite your note.
7. **Exam tab.** Check the pattern, then press **Teach me this** on any topic.
8. To see the limit message: delete your key in the Key tab and send a question. The Key page opens by itself.

## Run the automated tests
    python -m pytest backend/tests -q

Your data is one file: `data/stattutor.db`. Copy it to back up. Your API keys are stored only in that file.
