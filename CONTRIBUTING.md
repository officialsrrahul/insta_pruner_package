# Contributing to insta-pruner

Thank you for considering contributing! Here's how to get started.

---

## 🛠️ Local Setup

```bash
git clone https://github.com/officialsrrahul/insta_pruner_package.git
cd insta_pruner_package
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows
pip install -e .
pip install selenium webdriver-manager
```

---

## 📦 Project Structure

```
insta_pruner_package/
├── insta_pruner/
│   ├── __init__.py      ← exposes Pruner class
│   └── pruner.py        ← all core logic
├── .github/
│   └── workflows/
│       ├── publish.yml  ← auto-publish to PyPI on release
│       └── test.yml     ← lint + build check on every push/PR
├── pyproject.toml
├── CONTRIBUTING.md
├── README.md
├── LICENSE
└── .gitignore
```

---

## 🔀 Workflow

1. **Fork** the repo and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** inside `insta_pruner/`

3. **Test locally** by running a quick script:
   ```python
   from insta_pruner import Pruner
   pruner = Pruner(usernames=["test_user"], threshold=5000)
   pruner.run()
   ```

4. **Lint your code** before pushing:
   ```bash
   pip install flake8
   flake8 insta_pruner/ --max-line-length=120
   ```

5. **Open a Pull Request** against `main` with a clear description of what you changed and why.

---

## 🚀 Releasing a New Version (maintainer only)

1. Update the version in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. Commit and push:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 0.2.0"
   git push
   ```

3. Create a new GitHub Release with a tag matching the version (e.g. `v0.2.0`).

4. The **GitHub Actions workflow** will automatically build and publish the new version to PyPI. ✅

---

## 💡 Guidelines

- Keep all logic inside `insta_pruner/pruner.py` as methods of the `Pruner` class
- All new parameters should have sensible defaults and be documented in the docstring
- Don’t store Instagram credentials anywhere in the code
- Be mindful of Instagram rate limits — don’t reduce default pause values

---

## 🧑‍💻 Author

**Rahul S R** — [github.com/officialsrrahul](https://github.com/officialsrrahul)
