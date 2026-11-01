# StatTutor

StatTutor is a statistics tutor built with FastAPI. It can run locally with SQLite or deploy to Vercel with Supabase Auth and Postgres.

## Run locally (Windows)

1. Install Python 3.11 or newer.
2. Double-click `start.bat`.
3. Open [http://localhost:8000](http://localhost:8000). Local development uses SQLite and does not require an account.

Run the automated tests with:

```powershell
python -m pytest backend/tests -q
```

## Deploy to Vercel with Supabase

The Vercel entry point is configured explicitly as `backend.main:app` in `pyproject.toml`, so Vercel does not have to guess between the application and its test modules.

### 1. Prepare Supabase

1. In the Supabase project, enable **Authentication → Providers → Email**.
2. In **Project Settings → API**, copy the project URL and the **publishable/anon key**. The publishable key is intended for browser use; never use a `service_role` or secret API key here.
3. In **Project Settings → Database → Connection string**, choose the **Transaction pooler** and copy its URI. Set a strong database password if Supabase asks for one. The connection string is a server-side secret.
4. In **Authentication → URL Configuration**, set the Site URL to your Vercel domain and add that domain to the allowed redirect URLs.

Each Supabase account receives a separate Postgres schema. The backend validates each access token with Supabase Auth before opening that account's schema. API keys saved in StatTutor are encrypted with `APP_ENCRYPTION_KEY`.

### 2. Configure Vercel environment variables

In the Vercel project's **Settings → Environment Variables**, set the following for Production (and Preview if needed):

| Variable | Value |
|---|---|
| `SUPABASE_URL` | `https://uhhvtubbevwgdtnuyprb.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase publishable/anon key |
| `SUPABASE_DB_URL` | Supabase **Transaction pooler** URI, including `sslmode=require` |
| `APP_ENCRYPTION_KEY` | A new Fernet key generated with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

Keep the database URI and encryption key private. Do not commit them, put them in frontend code, or use Supabase's `service_role` key. If `APP_ENCRYPTION_KEY` is lost or changed, previously saved AI provider keys cannot be decrypted; keep a secure backup.

After setting the variables, redeploy from Vercel. When users sign up, Supabase may require email confirmation before their first sign-in.
In Supabase → Authentication → URL Configuration, set **Site URL** to `https://stattutor.vercel.app` and add that same URL under **Redirect URLs**. This ensures confirmation links return to the deployed app instead of `localhost:3000`.
If a student cannot sign in, use **Forgot password?** on the sign-in form. The reset email returns to StatTutor, where the student can set a new password.
Environment variable changes apply only to new deployments. In Vercel, keep **Root Directory** set to the repository root and use the Python framework preset; the FastAPI entry point is explicitly set in `pyproject.toml`.

### Existing local data

The local `data/stattutor.db` is deliberately excluded from Git and is not copied to Supabase. It may contain API keys and chat history. Each Supabase account starts with a fresh copy of the bundled syllabus and question papers, and private notes, chat, and provider keys are saved separately for that account.
