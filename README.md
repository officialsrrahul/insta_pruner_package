# insta-pruner

[![PyPI version](https://badge.fury.io/py/insta-pruner.svg)](https://badge.fury.io/py/insta-pruner)
[![Python](https://img.shields.io/pypi/pyversions/insta-pruner)](https://pypi.org/project/insta-pruner/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library to automatically unfollow non-followers on Instagram, with influencer filtering and live logging.

Connects to your **already-open, logged-in Chrome browser** — no credentials stored, no login automation.

---

## 📦 Installation

```bash
pip install insta-pruner
```

---

## 🚀 Quick Start

### Using a file

```python
from insta_pruner import Pruner

pruner = Pruner(
    usernames_file="non_followers.txt",
    threshold=5000,
    inactive_months=6
)
pruner.run()
```

### Using a list directly

```python
from insta_pruner import Pruner

pruner = Pruner(
    usernames=["user1", "user2", "user3"],
    threshold=3000,
    inactive_months=3
)
pruner.run()
```

---

## ⚙️ Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `usernames_file` | `str` | `None` | Path to `.txt` file with one username per line |
| `usernames` | `list` | `None` | Pass usernames directly as a Python list |
| `threshold` | `int` | `5000` | Accounts with ≥ this many followers are kept (influencer filter) |
| `inactive_months` | `int` | `6` | Unfollow if no post or reel within this many months |
| `unfollowed_log` | `str` | `unfollowed.txt` | File to log unfollowed accounts (appended, never overwritten) |
| `kept_log` | `str` | `kept_following.txt` | File to log kept accounts (appended, never overwritten) |
| `debugging_port` | `int` | `9222` | Chrome remote debugging port |
| `pause_before_check` | `int` | `4` | Seconds to wait for each profile page to load |
| `pause_between_users` | `int` | `2` | Seconds to wait between processing each user |

> Either `usernames_file` or `usernames` must be provided. If both are given, `usernames` takes priority.

---

## 💻 Before Running

You must start Chrome with remote debugging enabled so the library can connect to your logged-in session.

**PowerShell:**
```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222", "--user-data-dir=C:\chrome-debug"
```

**CMD:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
```

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
```

Then log in to Instagram in that Chrome window, and run your Python script.

---

## 📏 Unfollow Rules

The usernames list is expected to be **non-followers** (people who don’t follow you back). The library then applies:

- **Influencer filter** — accounts with followers ≥ `threshold` are always kept
- **Inactivity filter** — accounts with no posts or reels in the last `inactive_months` are unfollowed
- Both posts (`/p/`) and reels (`/reel/`) are checked for last activity

---

## 📄 Log Files

Both log files are **appended to** on every run — previous data is never deleted. Each run is separated by a clear divider:

```
# UNFOLLOWED ACCOUNTS
# ===========================================================================
# Run started 2026-06-14 19:00:00
# ===========================================================================
# username                  followers   last_active   reason
# ---------------------------------------------------------------------------
@some_account                      320  2023-05-10    followers < 5,000 | last active 2023-05-10 (inactive)

# ===========================================================================
# NEW RUN — 2026-06-15 10:00:00
# ===========================================================================
# username                  followers   last_active   reason
# ---------------------------------------------------------------------------
@another_account                   150  N/A           followers < 5,000 | no posts/reels found
```

---

## ⚠️ Notes

- Chrome must be **open and logged in to Instagram** before calling `pruner.run()`
- Instagram may rate-limit your account if you process too many users too quickly — increase `pause_between_users` if needed
- Private accounts with hidden posts/reels will show last activity as `N/A` and will be unfollowed if below the threshold
- This library uses Selenium to automate browser actions — use responsibly

---

## 🧑‍💻 Author

**Rahul S R** — [github.com/officialsrrahul](https://github.com/officialsrrahul)
