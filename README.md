# Local Event Finder

Local event finder project for CSE350. Flask + SQLite backend that also serves the frontend.

## Requirements

- Python 3.9 or newer (`python --version` to check)
- A terminal: Terminal on Mac, PowerShell on Windows

## Setup

Run these once, from the project root.

### Mac

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

### Windows (PowerShell)

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
python app.py
```

If PowerShell blocks the activate script, run this once, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

On Windows Command Prompt (cmd), activate with `venv\Scripts\activate.bat` instead.

Then open http://localhost:5001/

## Running again later

Activate the venv, then start the server. No need to reinstall or reseed.

- Mac: `cd backend`, `source venv/bin/activate`, `python app.py`
- Windows: `cd backend`, `venv\Scripts\Activate.ps1`, `python app.py`

Stop the server with `Ctrl+C`. After changing code, stop and start it again.

## Test accounts

| Email | Password |
|---|---|
| alice@example.com | password123 |
| bob@example.com | password123 |

`python seed.py` resets the database to this sample data. Run it again any time you want a clean start.

## Tests

From `backend/` with the venv active:

```bash
python tests/acceptance_check.py     # requirements checks (56)
python tests/security_check.py       # security checks (31)
python tests/performance_check.py    # search speed on 500+ events
```

## Troubleshooting

- **"No time zone found" or "Time zone data missing"** (Windows): run `pip install -r requirements.txt`. It installs `tzdata`, which Windows doesn't ship.
- **Port 5000 is busy on Mac**: the app uses port 5001 because macOS AirPlay takes 5000.
- **Images missing after an update**: run `python seed.py` again.
- **`python` not found on Mac**: use `python3`. Inside the venv, `python` works.
- **`pip` not found**: use `python -m pip install -r requirements.txt`.
