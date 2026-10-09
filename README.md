# 🤖 Self-Healing Developer Agent

An AI-powered developer assistant that analyzes software errors, identifies root causes, generates and reviews code patches, requests human approval, applies fixes safely, runs automated tests inside a Docker sandbox, and retries or rolls back when necessary.

The system is designed around a **human-in-the-loop self-healing software development workflow**, combining LLM reasoning, multi-agent collaboration, code analysis, security validation, project memory, Git checkpoints, and sandboxed execution.

---

## 🚀 Project Overview

Software debugging often requires developers to repeatedly:

1. Read an error or traceback
2. Find the relevant source code
3. Identify the root cause
4. Design a fix
5. Modify the code
6. Run tests
7. Analyze the test results
8. Retry if the fix fails
9. Roll back unsafe or unsuccessful changes

The **Self-Healing Developer Agent** automates this workflow while keeping the developer in control of important code modifications.

Instead of directly changing code without verification, the system follows a controlled pipeline:

```text
Error
  ↓
Project Analysis
  ↓
Root Cause Analysis
  ↓
Test Generation
  ↓
Fix Planning
  ↓
Security Review
  ↓
Human Approval
  ↓
Git Checkpoint
  ↓
Patch Application
  ↓
Docker Sandbox
  ↓
Automated Tests
  ↓
Validation
  ↓
 ┌───────────────┐
 │               │
PASS            FAIL
 │               │
 ↓               ↓
Report          Retry
                 │
                 ↓
              Rollback
```

---

# ✨ Key Features

## 🔍 Intelligent Error Analysis

The agent accepts a Python/Django project and an error or traceback, then analyzes the project to determine the likely root cause.

Features include:

* Project structure analysis
* Source-code inspection
* Traceback analysis
* Root-cause identification
* Relevant code-context extraction

---

## 🧪 Automated Test Generation

Before applying a fix, the system can generate tests based on the detected problem.

This helps establish expected behavior and provides a way to verify whether the generated repair actually works.

Example:

```python
def multiply_numbers(a, b):
    return a + b
```

Generated test:

```python
def test_multiply_numbers():
    assert multiply_numbers(2, 3) == 6
```

---

## 🛠️ AI-Powered Fix Generation

The agent generates a structured patch rather than allowing arbitrary code modifications.

Example:

```text
File:
calculator.py

Old Code:
return a + b

New Code:
return a * b

Reason:
The multiply_numbers function is performing addition
instead of multiplication.
```

---

## 🔐 Security & Patch Review

Every generated patch can be reviewed before modification.

The security layer checks for:

* Protected files
* Dangerous modifications
* Excessively large patches
* Unsafe code patterns
* Invalid syntax
* Restricted project paths

The system can block patches considered unsafe.

---

## 👤 Human-in-the-Loop Approval

The agent does not blindly apply important modifications.

The workflow includes an approval stage:

```text
AI generates patch
       ↓
Security review
       ↓
Human approval
       ↓
Patch applied
```

The developer can approve or reject the proposed change through the dashboard.

---

## 🔄 Self-Healing Retry Loop

If the generated fix does not pass the tests, the agent can retry the repair process.

Example:

```text
Attempt 1
   ↓
Tests fail
   ↓
Analyze failure
   ↓
Generate improved fix
   ↓
Attempt 2
   ↓
Tests pass
```

The maximum number of repair iterations is configurable.

Default:

```text
Maximum iterations = 5
```

---

## ↩️ Rollback Protection

Before modifying a Git repository, the system can create a checkpoint.

If the repair process reaches the maximum number of unsuccessful attempts, the system can roll back the changes.

```text
Git Checkpoint
      ↓
Apply Fix
      ↓
Run Tests
      ↓
Tests Fail
      ↓
Retry
      ↓
Maximum Attempts
      ↓
Rollback
```

---

## 🧠 Project Memory with ChromaDB

The system includes project memory using **ChromaDB**.

Previous repair information can be stored and retrieved to provide additional context for future debugging tasks.

Memory can contain information related to:

* Previous errors
* Root causes
* Repairs
* Test results
* Project context

This allows the system to reuse relevant historical debugging knowledge.

---

## 🤝 Multi-Agent Architecture

The system separates responsibilities between specialized agents.

```text
                    ┌─────────────────┐
                    │   Orchestrator  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
 Project Agent         Error Agent         Memory Agent
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ↓
                  Test Generation Agent
                             ↓
                       Fix Agent
                             ↓
                    Security Agent
                             ↓
                     Human Approval
                             ↓
                     Repair Agent
                             ↓
                  Validation Agent
```

### Main Agents

| Agent                  | Responsibility                                 |
| ---------------------- | ---------------------------------------------- |
| Project Agent          | Understands project structure and source files |
| Error Agent            | Analyzes errors and tracebacks                 |
| Test Generation Agent  | Generates tests for detected problems          |
| Fix Agent              | Creates structured repair patches              |
| Security Agent         | Reviews patches for security and safety        |
| Repair Agent           | Coordinates the repair process                 |
| Validation Agent       | Validates test results and repair success      |
| Manager / Orchestrator | Coordinates the overall agent workflow         |

---

# 🐳 Docker Sandbox

Code execution and testing can be performed inside a Docker sandbox.

The sandbox provides additional isolation between the agent and the host environment.

Current configuration includes:

```text
Execution Mode:
Docker

Memory Limit:
512 MB

CPU Limit:
1 CPU

Process Limit:
128

Network:
Disabled

Root Filesystem:
Read-only
```

The goal is to reduce the risk associated with executing generated or modified code.

---

# 🌐 Professional Developer Dashboard

The Django dashboard provides a graphical interface for interacting with the agent.

The dashboard provides information such as:

* Total projects
* Total debugging sessions
* Successful repairs
* Failed repairs
* Running sessions
* Pending approvals
* Success rate
* Average repair iterations
* Recent projects
* Recent repair activity
* Security review information
* Latest repair status
* Agent configuration

The dashboard also provides the human approval interface before important patches are applied.

---

# 🧩 Technology Stack

| Technology          | Purpose                           |
| ------------------- | --------------------------------- |
| Python 3.11         | Core programming language         |
| Django              | Web application and dashboard     |
| LangGraph           | Agent workflow orchestration      |
| LangChain           | LLM integration                   |
| Ollama              | Local LLM execution               |
| Qwen2.5-Coder 7B    | Code-focused local language model |
| ChromaDB            | Project memory / vector storage   |
| SQLite              | Application database              |
| Pytest              | Automated testing                 |
| GitPython           | Git repository operations         |
| Python AST          | Syntax/code validation            |
| Docker              | Sandboxed code execution          |
| HTML/CSS/JavaScript | Dashboard interface               |

---

# 🏗️ Project Structure

```text
self_healing_agent/
│
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── dashboard/
│
├── projects/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── migrations/
│
├── agent/
│   ├── graph.py
│   ├── state.py
│   ├── nodes.py
│   ├── llm.py
│   ├── service.py
│   ├── decision.py
│   ├── multi_agent.py
│   │
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── project_agent.py
│   │   ├── error_agent.py
│   │   ├── test_generation_agent.py
│   │   ├── fix_agent.py
│   │   ├── security_agent.py
│   │   ├── repair_agent.py
│   │   ├── validation_agent.py
│   │   └── manager.py
│   │
│   ├── analyzers/
│   │   ├── project_analyzer.py
│   │   ├── error_analyzer.py
│   │   ├── root_cause.py
│   │   ├── fix_planner.py
│   │   ├── code_validator.py
│   │   ├── context_manager.py
│   │   └── test_generator.py
│   │
│   ├── tools/
│   │   ├── file_tools.py
│   │   ├── code_tools.py
│   │   ├── patch_tools.py
│   │   ├── patch_validator.py
│   │   ├── test_tools.py
│   │   └── git_tools.py
│   │
│   ├── security/
│   │   ├── security_rules.py
│   │   ├── patch_reviewer.py
│   │   └── audit.py
│   │
│   ├── memory/
│   │   ├── embeddings.py
│   │   ├── chroma_store.py
│   │   └── memory_manager.py
│   │
│   └── prompts/
│
├── execution/
│   ├── sandbox.py
│   ├── runner.py
│   └── docker/
│       ├── Dockerfile
│       └── .dockerignore
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── project_upload.html
│   ├── debugging.html
│   ├── approval.html
│   └── report.html
│
├── static/
│   ├── css/
│   └── js/
│
├── media/
│
├── workspace/
│
└── tests/
    ├── test_agent.py
    ├── test_tools.py
    ├── test_projects.py
    └── test_sandbox.py
```

---

# ⚙️ Configuration

The system uses environment/configuration settings for the local LLM and execution environment.

Example configuration:

```python
OLLAMA_BASE_URL = "http://localhost:11434"

OLLAMA_MODEL = "qwen2.5-coder:7b"

AGENT_MAX_ITERATIONS = 5

AGENT_REQUIRE_HUMAN_APPROVAL = True

AGENT_BLOCK_CRITICAL_PATCHES = True

MEMORY_ENABLED = True

EXECUTION_MODE = "docker"

DOCKER_SANDBOX_TIMEOUT = 60

DOCKER_SANDBOX_MEMORY = "512m"

DOCKER_SANDBOX_CPUS = 1.0

DOCKER_SANDBOX_NETWORK_DISABLED = True
```

Sensitive configuration should be stored locally and should not be committed to Git.

---

# 💻 Installation

## 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/self-healing-developer-agent.git
cd self-healing-developer-agent
```

---

## 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

---

## 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

---

# 🧠 Install Ollama

Install Ollama and make sure the Ollama service is running.

Pull the code model:

```powershell
ollama pull qwen2.5-coder:7b
```

For project memory embeddings:

```powershell
ollama pull nomic-embed-text
```

Verify the models:

```powershell
ollama list
```

---

# 🐳 Docker Setup

Make sure Docker Desktop is installed and running.

Build the sandbox image:

```powershell
docker build -t self-healing-agent-sandbox:py311 execution/docker
```

Verify:

```powershell
docker images
```

The project can then use Docker as its execution environment.

---

# 🗄️ Django Setup

Run migrations:

```powershell
python manage.py migrate
```

Optional admin user:

```powershell
python manage.py createsuperuser
```

---

# ▶️ Run the Application

Start Django:

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

The Self-Healing Developer Agent dashboard will be available from the application interface.

---

# 🔧 Example Workflow

Suppose the project contains:

```python
def multiply_numbers(a, b):
    return a + b
```

The expected behavior is multiplication.

A test detects:

```text
Expected:
6

Actual:
5
```

The agent analyzes the problem and identifies:

```text
Root Cause:
multiply_numbers() uses the addition operator instead
of the multiplication operator.
```

The proposed patch becomes:

```diff
- return a + b
+ return a * b
```

The security layer reviews the patch.

The developer approves the change.

The agent applies the patch and executes the tests inside the sandbox.

Result:

```text
2 passed
```

The session is then marked as:

```text
FIXED
```

---

# 🔄 Self-Healing Workflow

The repair loop can be summarized as:

```text
                 ┌──────────────┐
                 │ Error Input  │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Project      │
                 │ Analysis     │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Root Cause   │
                 │ Analysis     │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Test         │
                 │ Generation   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Fix Planning │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Security     │
                 │ Review       │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Human        │
                 │ Approval     │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Git          │
                 │ Checkpoint   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Apply Patch  │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Docker       │
                 │ Sandbox      │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Run Tests    │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Validation   │
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Tests Pass?  │
                 └──────┬───────┘
                    YES │ NO
                        │
              ┌─────────┴─────────┐
              ↓                   ↓
          Final Report          Retry
                                  │
                                  ↓
                           Maximum Attempts?
                                  │
                                  ↓
                               Rollback
```

---

# 🛡️ Safety Design

The system uses multiple safeguards before modifying a project.

### Protected paths

Examples include:

```text
.git
.env
venv
.venv
__pycache__
node_modules
```

### Protected files

Examples include:

```text
settings.py
manage.py
requirements.txt
```

### Additional controls

* Human approval
* Patch size limits
* AST validation
* Security review
* Git checkpoints
* Docker sandbox
* Network-disabled execution
* Maximum repair iterations
* Rollback capability

These mechanisms are intended to reduce the risk of uncontrolled AI-generated code modifications.

---

# 🧪 Testing

Run the existing test suite using:

```powershell
pytest
```

For more detailed output:

```powershell
pytest -v
```

Django checks:

```powershell
python manage.py check
```

---

# 📊 Evaluation

The project is designed to be evaluated using different categories of software errors, including:

* Logic errors
* Incorrect operators
* Incorrect conditions
* Missing imports
* Incorrect variables
* Type errors
* Attribute errors
* Index errors
* Name errors
* Syntax errors

Potential evaluation metrics include:

```text
Repair Success Rate
Average Repair Iterations
Test Pass Rate
Average Repair Time
Rollback Rate
Security Block Rate
```

---

# 🔒 Security Considerations

This project is designed as a controlled developer-assistance system rather than an unrestricted autonomous coding system.

Important safety mechanisms include:

```text
Human approval
      +
Patch validation
      +
Security review
      +
Git checkpoint
      +
Sandboxed execution
      +
Automated testing
      +
Rollback
```

The system should be run in an appropriately isolated environment, especially when analyzing or executing untrusted projects.

---

# ⚠️ Current Limitations

The current implementation has several practical limitations:

* Repair quality depends on the local LLM.
* Complex architectural bugs may require human intervention.
* Generated tests may not always capture the intended behavior.
* Some errors may require domain-specific knowledge.
* Docker provides an additional execution boundary but should not be treated as an absolute security guarantee.
* The system currently focuses primarily on Python/Django-oriented workflows.
* Human approval remains an important part of the repair process.

---

# 🚧 Future Improvements

Possible future development includes:

* Larger evaluation benchmark
* More programming language support
* Advanced repository indexing
* Improved code retrieval
* Better patch ranking
* More sophisticated test generation
* GitHub integration
* Pull request generation
* CI/CD integration
* More advanced sandbox isolation
* Streaming agent execution
* Real-time dashboard updates
* Repair history visualization
* Developer feedback learning
* Automated evaluation reports

---

# 📌 Project Status

Current development phases:

```text
Phase 1  — Core Repair Engine                 ✅
Phase 2  — Self-Healing Retry Loop             ✅
Phase 3  — Developer Intelligence              ✅
Phase 4  — Security & Patch Review             ✅
Phase 5  — Automated Test Generation           ✅
Phase 6  — Multi-Agent Architecture            ✅
Phase 7  — ChromaDB Project Memory             ✅
Phase 8  — Docker Sandbox                      ✅
Phase 9  — Professional Developer Dashboard    ✅
Phase 10 — Evaluation & Documentation          🚧
```

---

# 🎯 Project Goal

The goal of this project is to demonstrate how modern AI-agent architectures can assist developers with software debugging and automated repair while maintaining:

* Human oversight
* Code safety
* Test-driven validation
* Secure execution
* Project memory
* Reproducibility
* Rollback capability

The project combines **LLM-based reasoning, agent orchestration, software testing, code analysis, security validation, vector memory, Git operations, and sandboxed execution** into a single developer-focused system.

---

# 👨‍💻 Author

**Aswanikrishna**


