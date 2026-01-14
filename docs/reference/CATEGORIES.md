# File Categories Reference

Complete reference for file categorization in Smart File Organizer.

## Category Structure

Files are organized into a hierarchical structure:

```
Documentos/
├── 01_Trabalho/        # Work-related
│   ├── Projetos/       # Project files
│   ├── Relatorios/     # Reports
│   └── Apresentacoes/  # Presentations
│
├── 02_Financas/        # Financial
│   ├── Impostos/       # Tax documents
│   ├── Recibos/        # Receipts
│   └── Extratos/       # Bank statements
│
├── 03_Estudos/         # Educational
│   ├── Cursos/         # Course materials
│   ├── Livros/         # Study books
│   └── Anotacoes/      # Notes
│
├── 04_Livros/          # eBooks
│   ├── Ficcao/         # Fiction
│   ├── Tecnico/        # Technical
│   └── Outros/         # Other
│
├── 05_Pessoal/         # Personal
│   ├── Documentos/     # Personal docs
│   ├── Midia/          # Media files
│   │   ├── Fotos/      # Photos
│   │   ├── Videos/     # Videos
│   │   └── Musicas/    # Music
│   └── Outros/         # Other personal
│
└── 90_Inbox_Organizar/ # Needs review
    └── [unclassified]  # Low confidence
```

## Category Descriptions

### 01_Trabalho (Work)

Files related to professional activities.

| Subcategory | Description | Examples |
|-------------|-------------|----------|
| `Projetos` | Project documentation | specs, requirements, designs |
| `Relatorios` | Business reports | quarterly, annual, analysis |
| `Apresentacoes` | Presentations | slides, pitches, demos |
| `Contratos` | Contracts | agreements, terms, licenses |
| `Comunicacoes` | Communications | memos, announcements |

**Detection Triggers:**
- Keywords: "relatório", "projeto", "cliente", "contrato"
- File patterns: `*_report.pdf`, `project_*.docx`
- Content: business terminology, company names

### 02_Financas (Financial)

Financial and accounting documents.

| Subcategory | Description | Examples |
|-------------|-------------|----------|
| `Impostos` | Tax documents | IR, declarations, receipts |
| `Recibos` | Receipts | purchases, payments |
| `Extratos` | Statements | bank, credit card |
| `Notas_Fiscais` | Invoices | NFe, invoices |
| `Orcamentos` | Budgets | estimates, quotes |

**Detection Triggers:**
- Keywords: "imposto", "recibo", "nota fiscal", "R$"
- File patterns: `*_nfe.pdf`, `extrato_*.pdf`
- Content: currency amounts, CNPJ/CPF numbers

### 03_Estudos (Educational)

Learning and educational materials.

| Subcategory | Description | Examples |
|-------------|-------------|----------|
| `Cursos` | Course materials | lectures, exercises |
| `Apostilas` | Study guides | tutorials, manuals |
| `Anotacoes` | Notes | class notes, summaries |
| `Certificados` | Certificates | completion, awards |
| `Pesquisas` | Research | papers, articles |

**Detection Triggers:**
- Keywords: "curso", "aula", "exercício", "capítulo"
- File patterns: `aula_*.pdf`, `modulo_*.docx`
- Content: educational structure, questions

### 04_Livros (eBooks)

Digital books and long-form reading.

| Subcategory | Description | Examples |
|-------------|-------------|----------|
| `Ficcao` | Fiction | novels, stories |
| `Tecnico` | Technical | programming, engineering |
| `Negocios` | Business | management, marketing |
| `Autoajuda` | Self-help | personal development |
| `Outros` | Other | various genres |

**Detection Triggers:**
- File extensions: `.epub`, `.mobi`, `.azw`
- Content structure: chapters, ISBN, author credits
- Metadata: book-related markers

### 05_Pessoal (Personal)

Personal files and media.

| Subcategory | Description | Examples |
|-------------|-------------|----------|
| `Documentos` | Personal docs | IDs, contracts |
| `Midia/Fotos` | Photographs | family, events, travel |
| `Midia/Videos` | Videos | recordings, memories |
| `Midia/Musicas` | Music | albums, playlists |
| `Outros` | Other | misc personal files |

**Detection Triggers:**
- Extensions: `.jpg`, `.png`, `.mp4`, `.mp3`
- EXIF data: camera info, dates
- Content: personal names, locations

### 90_Inbox_Organizar (Inbox)

Files requiring manual review.

**When files go here:**
- AI confidence < 85%
- Rule engine couldn't classify
- Conflicting signals in content
- File type not recognized
- Content extraction failed

**Recommended action:**
1. Review files manually
2. Add rules for common patterns
3. Re-run classification after updates

## Naming Convention

Files are renamed to a standard format:

```
YYYY-MM-DD__Categoria__Assunto.ext
```

### Examples

| Original | Organized |
|----------|-----------|
| `scan001.pdf` | `2024-03-15__Financas__Nota_Fiscal_Amazon.pdf` |
| `IMG_1234.jpg` | `2024-01-20__Pessoal__Foto_Aniversario.jpg` |
| `doc.docx` | `2024-02-10__Trabalho__Relatorio_Q1.docx` |

### Name Sanitization

Invalid characters are removed/replaced:
- `< > : " / \ | ? *` → removed
- Spaces → `_` (underscore)
- Accents → preserved (UTF-8)
- Max length: 200 characters

## Year Organization

Files are organized by year within subcategories:

```
02_Financas/
├── Recibos/
│   ├── 2022/
│   ├── 2023/
│   └── 2024/
```

**Year Detection:**
1. From filename: `relatorio_2024.pdf`
2. From content: dates found in text
3. From metadata: creation date
4. Fallback: current year

## Confidence Levels

| Confidence | Action | Destination |
|------------|--------|-------------|
| 95-100% | Auto-classify | Target category |
| 85-94% | Auto-classify | Target category |
| 70-84% | Ask for review | Target (with flag) |
| < 70% | Skip/Inbox | `90_Inbox_Organizar` |

## Customization

### Custom Categories

Add categories in `configs/rules.yaml`:

```yaml
categories:
  # Add custom category
  06_Projetos_Especiais:
    description: "Special project files"
    subcategories:
      - ProjectA
      - ProjectB
    patterns:
      - "project_a_*"
      - "project_b_*"
```

### Category Mapping

Override default mappings:

```yaml
mappings:
  # Route all .psd files to design
  "*.psd": "01_Trabalho/Design"
  
  # Route specific filenames
  "invoice_*": "02_Financas/Notas_Fiscais"
```

## Related Documentation

- [Rules Configuration](RULES_CONFIG.md) - Customize classification rules
- [AI Backends](AI_BACKENDS.md) - Configure AI classification
- [CLI Usage](../user-guide/CLI_USAGE.md) - Command reference
