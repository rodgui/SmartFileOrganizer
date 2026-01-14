# Local-First Mode Quick Reference

Este documento é um guia rápido para desenvolver e usar o **modo Local-First** do SmartFileOrganizer.

## Documentação Completa

- **Arquitetura Detalhada**: [docs/plan_architecture_local.md](docs/plan_architecture_local.md)
- **Guia do Usuário**: [README_LOCAL.md](README_LOCAL.md)
- **Regras para AI Agents**: [.github/copilot-instructions.md](.github/copilot-instructions.md)
- **Cursor Rules**: [.cursor/rules/300_Local_First_Ollama.mdc](.cursor/rules/300_Local_First_Ollama.mdc)

## Comandos Essenciais

### Setup Inicial

```powershell
# 1. Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Instalar e iniciar Ollama
# Baixar de https://ollama.com
ollama serve  # Iniciar servidor local

# 4. Baixar modelo LLM
ollama pull llama3.2  # ou mistral, phi3, etc.
```

### Executar Organizador

```powershell
# Dry-run (gera plano sem executar)
python -m src.organizer.cli scan C:\Users\$env:USERNAME\Downloads --plan

# Executar com aplicação das mudanças
python -m src.organizer.cli scan C:\Users\$env:USERNAME\Downloads --plan --apply

# Com configuração customizada
python -m src.organizer.cli scan C:\Downloads --config configs/rules.yaml --plan --apply

# Limitar número de arquivos (segurança)
python -m src.organizer.cli scan C:\Downloads --plan --apply --max-items 100

# Forçar reclassificação (ignorar cache)
python -m src.organizer.cli scan C:\Downloads --plan --force
```

## Estrutura de Arquivos

```
SmartFileOrganizer/
├── src/organizer/          # Código do modo Local-First
│   ├── cli.py             # Interface de linha de comando
│   ├── scanner.py         # Varredura de diretórios
│   ├── extractor.py       # Extração de conteúdo
│   ├── rule_engine.py     # Regras determinísticas
│   ├── llm_classifier.py  # Classificação via Ollama
│   ├── planner.py         # Geração de planos
│   ├── executor.py        # Execução segura
│   └── state_manager.py   # Cache de estado
├── configs/               # Configurações
│   ├── rules.yaml         # Regras de classificação
│   └── categories.yaml    # Estrutura de categorias
├── plans/                 # Planos gerados (output)
├── logs/                  # Logs de execução (output)
└── state/                 # Cache SQLite/JSON (output)
```

## Estrutura de Diretórios de Destino

Padrão (configurável em `configs/categories.yaml`):

```
Documentos/
├── 01_Trabalho/
│   └── <Area>/<Projeto>/<Ano>/
├── 02_Financas/
│   └── <Tipo>/<Ano>/      # Faturas, Impostos, Contratos
├── 03_Estudos/
│   └── <Tema>/<Ano>/      # Python, ML, DevOps
├── 04_Livros/
│   └── <AutorOuTema>/
├── 05_Pessoal/
│   ├── Midia/
│   │   ├── Imagens/<Ano>/
│   │   ├── Videos/<Ano>/
│   │   └── Audio/<Ano>/
│   └── <Tema>/<Ano>/
└── 90_Inbox_Organizar/    # Baixa confiança
```

**Convenção de nomes**: `YYYY-MM-DD__Categoria__Assunto.ext`

## Configuração

### Variables de Ambiente

```powershell
# Opcional: customizar endpoint Ollama
$env:OLLAMA_BASE_URL = "http://localhost:11434"
```

### Arquivo de Configuração (configs/rules.yaml)

```yaml
scanner:
  exclude_dirs:
    - .git
    - node_modules
    - .venv
  exclude_extensions:
    - .exe
    - .dll
    - .sys

extractor:
  max_excerpt_kb: 8  # Limite de texto extraído

classifier:
  min_confidence: 85  # Threshold para classificação
  model: "llama3.2"   # Modelo Ollama

organizer:
  base_path: "C:\\Users\\USERNAME\\Documents"
  categories:
    - 01_Trabalho
    - 02_Financas
    - 03_Estudos
    - 04_Livros
    - 05_Pessoal

executor:
  max_items_per_run: 500  # Limite de segurança
```

## Fluxo de Trabalho

1. **Scan** → Varre diretórios e gera `FileRecord[]`
2. **Extract** → Extrai conteúdo (2-8KB) de cada arquivo
3. **Classify**:
   - Tenta **regras determinísticas** primeiro
   - Se ambíguo, chama **LLM Ollama** para classificação semântica
   - Se confiança < 85%, roteia para `90_Inbox_Organizar`
4. **Plan** → Gera plano executável:
   - `plans/plan_YYYYMMDD_HHMMSS.json` (máquina)
   - `plans/plan_YYYYMMDD_HHMMSS.md` (humano)
5. **Review** → Usuário revisa `plan.md` antes de executar
6. **Execute** (com `--apply`) → Move/renomeia arquivos:
   - Cria diretórios destino
   - Resolve conflitos (versiona com `_v2`, `_v3`)
   - Gera `executed_manifest.json`
   - Registra em `logs/run_YYYYMMDD_HHMMSS.log`

## Segurança e Garantias

✅ **Nunca apaga** arquivos (apenas MOVE/COPY/RENAME/SKIP)  
✅ **Dry-run obrigatório** (precisa de `--apply` explícito)  
✅ **Idempotente** (rodar 2x é seguro)  
✅ **Auditável** (planos + manifestos + logs)  
✅ **Sem sobrescrita** (conflitos resolvidos automaticamente)  
✅ **Pastas protegidas** (`.git`, `node_modules`, etc. ignoradas)  

## Testes

```powershell
# Executar todos os testes
pytest tests/

# Testes específicos do modo local
pytest tests/test_local_organizer.py -v

# Com cobertura
pytest --cov=src.organizer tests/
```

## Troubleshooting

### Ollama não está rodando

```powershell
# Verificar se Ollama está ativo
curl http://localhost:11434/api/tags

# Se não responder, iniciar Ollama
ollama serve
```

### Modelo não encontrado

```powershell
# Listar modelos instalados
ollama list

# Baixar modelo faltante
ollama pull llama3.2
```

### Permissões negadas

- Executar PowerShell como **Administrador**
- Verificar permissões das pastas de destino
- Checar se arquivos não estão abertos em outros programas

### JSON inválido do LLM

- O sistema retenta automaticamente (max 3x)
- Se persistir, arquivos vão para `90_Inbox_Organizar`
- Verificar logs em `logs/run_*.log` para detalhes

## Desenvolvimento

### Adicionar Nova Regra Determinística

Editar `configs/rules.yaml`:

```yaml
- rule_id: PDF_BOOKS
  pattern: "*.pdf"
  min_size_mb: 5
  keywords_in_filename:
    - livro
    - book
  category: "04_Livros"
  confidence: 95
```

### Customizar Estrutura de Categorias

Editar `configs/categories.yaml`:

```yaml
categories:
  "06_Projetos":
    subcategories:
      - "OpenSource"
      - "Cliente_A"
      - "Cliente_B"
    organize_by: ["project", "year"]
```

### Modificar Extração de Conteúdo

Editar `src/organizer/extractor.py`:

```python
def extract_pdf(self, file_path: Path) -> str:
    """Extrair primeiras N páginas de PDF."""
    with pdfplumber.open(file_path) as pdf:
        pages = pdf.pages[:5]  # Ajustar número de páginas
        text = "\n".join(page.extract_text() for page in pages)
        return text[:8000]  # Truncar para 8KB
```

## Recursos Adicionais

- **Ollama Documentation**: https://ollama.com/docs
- **Modelos Recomendados**:
  - `llama3.2` (melhor qualidade, mais lento)
  - `phi3` (rápido, menor consumo de memória)
  - `mistral` (bom equilíbrio)
- **Community Support**: [GitHub Issues](https://github.com/whoisdsmith/SmartFileOrganizer/issues)

## Próximos Passos

- [ ] Implementar OCR para imagens (pytesseract)
- [ ] Adicionar UI Streamlit para visualização de planos
- [ ] Suporte a embeddings para deduplicação semântica
- [ ] Integração com OneDrive (sincronização bidirecional)
- [ ] Melhorar extração de XLSX (fórmulas, gráficos)
