\# 🤝 Contributing Guide



\## 🚀 Workflow



```text

Pull main

→ Create branch

→ Make changes

→ Commit

→ Push

→ Pull Request

→ Merge

```



Avoid working directly on `main`.



```bash

git checkout main

git pull origin main

git checkout -b feature/<task-name>

```



\---



\## 👤 Individual Work



Each member works mainly inside:



```text

contributions/<member>/

├── code/

├── weekly/

├── reports/

└── notes/

```



Avoid changing another member's folder unless discussed first.



\---



\## 🧩 Shared Code



```text

source-code/

```



is for work agreed and adopted by the team.



\---



\## 💾 Commit \& Push



```bash

git status

git add .

git commit -m "Describe the change"

git push -u origin <branch-name>

```



Use clear commit messages.



\---



\## 🔀 Pull Requests



Create a PR into:



```text

main

```



Briefly explain:



\- what changed;

\- why;

\- testing/checks performed.



After merge:



```bash

git checkout main

git pull origin main

```



\---



\## 📅 Weekly Contribution



Record work in:



```text

contributions/<member>/weekly/

```



Include:



\- work completed;

\- evidence / commits / PRs;

\- issues;

\- next steps.



\---



\## 🔐 Important



Do not commit:



\- passwords / API keys;

\- `.env` files;

\- restricted partner data;

\- unnecessary datasets;

\- virtual environments or cache files.



Always check:



```bash

git status

```



before committing.



\---



> Keep the repository clear, organised and easy for the whole team to follow.

