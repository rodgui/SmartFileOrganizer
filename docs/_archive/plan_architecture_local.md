<!-- plano_de_arquitetura.md -->
# Plano de Arquitetura — Organizador Local de Arquivos com LLM (Ollama) — Windows

## 1) Escopo e objetivos
### Objetivo
Organizar `Downloads` e `Documentos` (e futuramente OneDrive) usando:
- **Regras determinísticas** para casos óbvios
- **LLM local** para classificação/nomeação semântica
- Execução **segura** com `dry-run` + aprovação explícita

### Não objetivos (MVP)
- Apagar arquivos
- OCR de imagens (pode entrar depois)
- UI completa (CLI primeiro)

## 2) Requisitos
### Funcionais
- Indexar arquivos e extrair metadados
- Extrair texto para PDF/DOCX/PPTX/XLSX (quando aplicável)
- Classificar via Ollama (JSON estrito)
- Gerar plano (JSON/MD)
- Executar plano com `--apply` (movendo/renomeando)
- Conflito de nomes tratado automaticamente (sem sobrescrita)

### Não funcionais
- Idempotência
- Auditoria (logs)
- Baixo risco
- Performance aceitável em grandes diretórios (cache)

## 3) Componentes
### 3.1 Scanner
- Varre diretórios-alvo recursivamente
- Aplica exclusões (pastas e extensões sensíveis)
- Produz `FileRecord[]`

### 3.2 Extractor
- Estratégias por tipo:
  - PDF: extrair 3–5 primeiras páginas (ou N primeiros caracteres)
  - DOCX: texto do documento
  - PPTX: títulos e texto dos slides
  - XLSX: nomes de abas + primeiras linhas (limitado)
  - Imagens: EXIF básico (sem OCR)
  - ZIP: lista de nomes internos (sem descompactar no MVP)
- Gera `content_excerpt` curto (ex.: 2–8KB)

### 3.3 Rule Engine (determinístico)
- Mapeia extensões e padrões para categoria/ação
- Exemplo:
  - `.jpg/.png/.heic` -> `05_Pessoal/Midia/Imagens/<Ano>/`
  - `.zip` -> `Arquivos_Compactados/<Ano>/`
  - livros PDF detectados por heurística -> `04_Livros/`
- Regras têm IDs e justificativas (`rule_id`)

### 3.4 LLM Classifier (Ollama)
- Chamado somente se:
  - regra não determinou categoria com confiança alta
  - ou quando precisa de nomeação semântica
- Prompt exige JSON estrito:
  - `categoria`, `subcategoria`, `assunto`, `ano`, `nome_sugerido`, `confianca`, `racional`
- Validação e retry:
  - Se JSON inválido: re-prompt “corrija para JSON”
  - Se campos ausentes: re-prompt “inclua campos faltantes”
- Threshold:
  - `>= 85` apto a mover/renomear
  - `< 85` envia para `90_Inbox_Organizar` ou `SKIP`

### 3.5 Planner
- Constrói plano idempotente:
  - `PlanItem{action, src, dst, reason, confidence, rule_id, llm_used}`
- Resolve conflitos:
  - se `dst` existe: `_v2`, `_v3`… ou sufixo hash curto
- Gera:
  - `plans/plan_YYYYMMDD_HHMMSS.json`
  - `plans/plan_YYYYMMDD_HHMMSS.md`

### 3.6 Executor
- Por padrão: simula (dry-run)
- Com `--apply`:
  - cria diretórios destino
  - move/renomeia com tratamento robusto
  - registra `executed_manifest.json` com status por item
- Nunca sobrescreve

### 3.7 Cache/State
- `state/index.sqlite` (ou JSON no MVP)
- Chaves:
  - `path`, `sha256`, `mtime`, `size`
- Evita reclassificar arquivos inalterados

## 4) Fluxo de dados (pipeline)
1. `scan` -> `FileRecord[]`
2. `extract` -> `FileRecord(content_excerpt)`
3. `rules` -> `Classification?` (alta confiança)
4. `llm` -> `Classification` (quando necessário)
5. `plan` -> `PlanItem[]` + `plan.md/json`
6. `apply` -> execução + manifest + logs

## 5) Estrutura de diretórios alvo (padrão)
Base (exemplo):
- `Documentos/01_Trabalho/<Area>/<Projeto>/<Ano>/`
- `Documentos/02_Financas/<Tipo>/<Ano>/`
- `Documentos/03_Estudos/<Tema>/<Ano>/`
- `Documentos/04_Livros/<AutorOuTema>/`
- `Documentos/05_Pessoal/<Tema>/<Ano>/`
- `Documentos/90_Inbox_Organizar/`

Padrão de nome:
- `YYYY-MM-DD__Categoria__Assunto.ext`
- Se data não existir: `YYYY-00-00__...`
- Sanitização Windows: remover caracteres inválidos e limitar comprimento

## 6) OneDrive (fase 2)
- Não operar diretamente “na nuvem”
- Fluxo:
  1) OneDrive sincroniza para pasta local
  2) copiar/ingestar para `90_Inbox_Organizar`
  3) pipeline gera plano
  4) mover para árvore final (OneDrive sincroniza)

## 7) Observabilidade e auditoria
- Logs:
  - `logs/run_YYYYMMDD_HHMMSS.log` (texto)
  - opcional `logs/run_...jsonl`
- Manifest:
  - `plans/executed_YYYYMMDD_HHMMSS.json` com status por item

## 8) Segurança operacional
- Proteções:
  - lista de extensões/pastas proibidas para ação
  - limite de itens por execução (ex.: `--max-items 500` no MVP)
  - modo “quarentena”: enviar incertos para inbox
- Reversão:
  - manter `executed_manifest` com `src` original para possível rollback

## 9) Roadmap
### MVP
- Scanner + extractor básico (PDF/DOCX)
- Rules + LLM classifier
- Planner + executor (MOVE + RENAME)
- Dry-run default

### Próximo
- PPTX/XLSX extractor melhor
- Embeddings (dedup e agrupamento)
- UI simples (Streamlit)
- OCR opcional

