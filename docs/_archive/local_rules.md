Abaixo está um **DOCUMENTO UNIFICADO DE ESPECIFICAÇÃO TÉCNICA + ARQUITETURA + REGRAS DE IMPLEMENTAÇÃO**, pronto para ser enviado **diretamente ao CODEx, Claude Code ou outro agente de geração de repositório**.
O texto já está no formato ideal para **“crie o repositório e implemente”**, sem ambiguidade.

---

```markdown
# Local File Organizer — Regras Determinísticas + LLM Local (Ollama) — Windows

## 0. Instrução ao Agente de Código (LEIA PRIMEIRO)
Você deve:
- Criar um **repositório Python completo e funcional**
- Seguir **rigorosamente** esta especificação
- Priorizar **segurança, dry-run, idempotência e rastreabilidade**
- Implementar um **CLI utilizável** no Windows
- Não fazer suposições fora deste documento

Objetivo final: um organizador local de arquivos que usa **LLM local (Ollama)** apenas para **classificação semântica**, enquanto **regras determinísticas controlam ações no filesystem**.

---

## 1. Objetivo do Sistema

Organizar arquivos locais (Downloads, Documentos e futuramente OneDrive) de forma:
- Segura (sem apagar, sem sobrescrever)
- Reversível (planos e manifestos)
- Escalável
- Determinística + semântica

O sistema **NUNCA** deve mover arquivos sem:
1. Gerar um plano (`dry-run`)
2. Validar conflitos
3. Receber `--apply`

---

## 2. Ambiente Alvo

- SO: Windows 10/11
- Python: 3.11+
- Hardware:
  - GPU: RTX 5080
  - RAM: 64GB
  - CPU: Ryzen 5700X3D
  - Disco: NVMe
- LLM Runtime: Ollama (local)

Modelo padrão:
- `qwen2.5:14b`

---

## 3. Princípios Invioláveis (Guardrails)

1. **Nunca apagar arquivos**
2. **Dry-run é o padrão**
3. **Nunca sobrescrever arquivos**
4. **Conflitos de nome devem ser versionados** (`_v2`, `_v3` ou hash curto)
5. **Pastas e extensões sensíveis nunca sofrem ação**
6. **LLM nunca decide ação direta**, apenas classificação
7. **Toda execução gera logs e manifestos**
8. Código deve ser **idempotente**

---

## 4. Arquitetura em Camadas (Obrigatória)

Pipeline obrigatória:

```

Scanner
→ Extractor
→ Rule Engine
→ LLM Classifier (Ollama)
→ Planner
→ Executor

```

Cada camada deve ser **isolada**, testável e substituível.

---

## 5. Estrutura do Repositório (OBRIGATÓRIA)

```

local-file-organizer/
│
├─ src/
│  └─ organizer/
│     ├─ **init**.py
│     ├─ cli.py               # Entry point
│     ├─ scanner.py
│     ├─ extractor.py
│     ├─ rules.py
│     ├─ llm.py
│     ├─ planner.py
│     ├─ executor.py
│     ├─ models.py            # Dataclasses / domain models
│     ├─ utils.py
│
├─ configs/
│  ├─ categories.yaml
│  ├─ rules.yaml
│
├─ plans/
├─ logs/
├─ state/
│
├─ tests/
│
├─ copilot_rules.md
├─ README.md
└─ pyproject.toml

````

---

## 6. Modelo de Domínio (OBRIGATÓRIO)

### FileRecord
```python
path: Path
size: int
mtime: datetime
ctime: datetime
sha256: str
extension: str
mime: str
content_excerpt: str | None
````

### Classification

```python
category: str
subcategory: str
subject: str
year: int
suggested_name: str
confidence: int
rationale: str
```

### PlanItem

```python
action: Literal["MOVE", "RENAME", "COPY", "SKIP"]
src: Path
dst: Path | None
reason: str
confidence: int
rule_id: str | None
llm_used: bool
```

---

## 7. Scanner

Responsabilidades:

* Varredura recursiva
* Exclusões obrigatórias:

  * Pastas: `.git`, `.ssh`, `.terraform`, `.vscode`, `node_modules`
  * Arquivos < 1KB
  * Extensões executáveis

Produz: `List[FileRecord]`

---

## 8. Extractor

Extração **limitada e segura**:

* PDF: primeiras 3–5 páginas
* DOCX: texto completo
* PPTX: títulos e textos dos slides
* XLSX: nomes das abas + primeiras linhas
* ZIP: apenas lista interna
* Imagens: EXIF (sem OCR no MVP)

Nunca extrair mais de **8KB de texto** por arquivo.

---

## 9. Rule Engine (Determinístico)

Regras têm precedência sobre LLM.

Exemplos:

* `.jpg .png .heic` → `05_Pessoal/Midia/Imagens/<Ano>`
* `.zip` → `Arquivos_Compactados/<Ano>`
* PDFs com palavras-chave de livros → `04_Livros`

Cada regra deve ter:

* `rule_id`
* `description`
* `confidence_override` (opcional)

---

## 10. LLM Classifier (Ollama)

Chamado **somente quando regras não forem suficientes**.

### Prompt (OBRIGATÓRIO)

* Solicitar **JSON estrito**
* Sem markdown
* Sem texto extra

Campos obrigatórios:

```json
{
  "categoria": "",
  "subcategoria": "",
  "assunto": "",
  "ano": 2025,
  "nome_sugerido": "",
  "confianca": 0,
  "racional": ""
}
```

### Regras

* Validar JSON
* Retry se inválido
* `confidence < 85` → não mover

---

## 11. Planner

Responsabilidades:

* Gerar plano idempotente
* Resolver conflitos
* Nunca sobrescrever
* Criar:

  * `plan_YYYYMMDD_HHMMSS.json`
  * `plan_YYYYMMDD_HHMMSS.md`

---

## 12. Executor

* Dry-run por padrão
* Executa somente com `--apply`
* Cria diretórios destino
* Registra manifesto de execução:

  * `executed_YYYYMMDD_HHMMSS.json`
* Nunca remove arquivos

---

## 13. CLI (Obrigatório)

Comando principal:

```bash
python -m organizer run \
  --roots "C:\Users\...\Downloads" "C:\Users\...\Documents" \
  --out ./plans \
  --apply
```

Flags:

* `--model`
* `--confidence-threshold` (default 85)
* `--max-items`
* `--dry-run` (default true)

---

## 14. Estrutura de Pastas Destino

```
Documentos/
  01_Trabalho/<Area>/<Projeto>/<Ano>
  02_Financas/<Tipo>/<Ano>
  03_Estudos/<Tema>/<Ano>
  04_Livros/<AutorOuTema>
  05_Pessoal/<Tema>/<Ano>
  90_Inbox_Organizar
```

---

## 15. Logs e Auditoria

* `logs/run_YYYYMMDD_HHMMSS.log`
* Logs claros, sequenciais e auditáveis
* Nenhuma ação sem registro

---

## 16. OneDrive (Fase 2)

Nunca operar direto em paths cloud.

Fluxo:

1. OneDrive sync → local
2. Copiar para `90_Inbox_Organizar`
3. Rodar pipeline
4. Aplicar plano

---

## 17. Critérios de Aceitação

O repositório será considerado correto se:

* Executar dry-run sem mover arquivos
* Gerar planos válidos
* Aplicar plano somente com `--apply`
* Nunca sobrescrever arquivos
* Classificar corretamente PDFs, DOCX e imagens
* Operar de forma determinística

---

## 18. Licença

Sugestão: MIT ou Apache-2.0

```
