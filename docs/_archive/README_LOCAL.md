<!-- README.md -->
# Local File Organizer (Windows) — Regras + LLM Local (Ollama)

Organizador local-first para Windows que:
- Indexa e extrai conteúdo (quando aplicável)
- Classifica e sugere nomes/pastas com **LLM local via Ollama**
- Gera **plano (dry-run)** e só executa com `--apply`
- Mantém auditoria (planos, manifestos, logs)

## Requisitos
- Windows 10/11
- Python 3.11+ (recomendado)
- Ollama instalado e rodando localmente

## Setup rápido

### 1) Ambiente Python
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
