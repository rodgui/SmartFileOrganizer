# Rules Configuration

Configure classification rules for deterministic file organization.

## Rules File Location

Default: `configs/rules.yaml`

Custom: `python organize.py plan <dir> --rules /path/to/rules.yaml`

## Rule Structure

```yaml
rules:
  - rule_id: unique_identifier
    pattern: "*.{ext1,ext2}"        # Required: file extension pattern
    category: "01_Trabalho"         # Required: target category
    subcategory: "Subfolder"        # Optional: subfolder within category
    confidence: 95                  # Required: confidence score (0-100)
    description: "Human readable"   # Optional: description
    keywords: ["word1", "word2"]    # Optional: content keywords
    min_size_mb: 1.0               # Optional: minimum file size
    max_size_mb: 100.0             # Optional: maximum file size
```

## Pattern Syntax

### Single Extension
```yaml
pattern: "*.pdf"
```

### Multiple Extensions
```yaml
pattern: "*.{jpg,jpeg,png,gif}"
```

### Case Insensitive
Patterns are matched case-insensitively.

## Categories

| Category | Description |
|----------|-------------|
| `01_Trabalho` | Work documents, projects |
| `02_Financas` | Financial documents, invoices |
| `03_Estudos` | Study materials, courses |
| `04_Livros` | eBooks, reading materials |
| `05_Pessoal` | Personal files, photos, media |
| `90_Inbox_Organizar` | Low confidence, needs review |

## Example Rules

### Images

```yaml
- rule_id: images_photos
  pattern: "*.{jpg,jpeg,png,gif,webp,heic}"
  category: "05_Pessoal"
  subcategory: "Midia/Imagens"
  confidence: 95
  description: "Photo files"
```

### Videos

```yaml
- rule_id: videos_general
  pattern: "*.{mp4,mkv,avi,mov,wmv}"
  category: "05_Pessoal"
  subcategory: "Midia/Videos"
  confidence: 90
  description: "Video files"
```

### Documents with Keywords

```yaml
- rule_id: finance_invoices
  pattern: "*.{pdf,xml}"
  category: "02_Financas"
  subcategoria: "Notas_Fiscais"
  confidence: 90
  keywords:
    - "invoice"
    - "fatura"
    - "nota fiscal"
    - "nfe"
  description: "Invoice documents"
```

### Size-Based Rules

```yaml
- rule_id: large_videos
  pattern: "*.{mp4,mkv}"
  category: "05_Pessoal"
  subcategory: "Midia/Videos/Grandes"
  confidence: 85
  min_size_mb: 1000  # Files > 1GB
  description: "Large video files"
```

## Complete Example

```yaml
# configs/rules.yaml

rules:
  # Images
  - rule_id: images_photos
    pattern: "*.{jpg,jpeg,png,gif,bmp,webp,heic,heif}"
    category: "05_Pessoal"
    subcategory: "Midia/Imagens"
    confidence: 95
    description: "Photo and image files"

  - rule_id: images_raw
    pattern: "*.{raw,cr2,nef,arw,dng}"
    category: "05_Pessoal"
    subcategory: "Midia/Imagens/RAW"
    confidence: 95
    description: "RAW camera files"

  # Audio
  - rule_id: audio_music
    pattern: "*.{mp3,flac,wav,aac,ogg,m4a}"
    category: "05_Pessoal"
    subcategory: "Midia/Audio"
    confidence: 90
    description: "Music files"

  # Video
  - rule_id: video_general
    pattern: "*.{mp4,mkv,avi,mov,wmv,webm}"
    category: "05_Pessoal"
    subcategory: "Midia/Video"
    confidence: 90
    description: "Video files"

  # Work Documents
  - rule_id: work_contracts
    pattern: "*.{pdf,docx}"
    category: "01_Trabalho"
    subcategory: "Contratos"
    confidence: 85
    keywords:
      - "contrato"
      - "contract"
      - "agreement"
    description: "Contract documents"

  - rule_id: work_presentations
    pattern: "*.{pptx,ppt,key}"
    category: "01_Trabalho"
    subcategory: "Apresentacoes"
    confidence: 90
    description: "Presentation files"

  # Finance
  - rule_id: finance_invoices
    pattern: "*.{pdf,xml}"
    category: "02_Financas"
    subcategory: "Notas_Fiscais"
    confidence: 90
    keywords:
      - "invoice"
      - "fatura"
      - "nota fiscal"
      - "nfe"
      - "danfe"
    description: "Invoice documents"

  - rule_id: finance_bank
    pattern: "*.{pdf,csv,ofx}"
    category: "02_Financas"
    subcategory: "Extratos"
    confidence: 85
    keywords:
      - "extrato"
      - "statement"
      - "bank"
    description: "Bank statements"

  # Books
  - rule_id: books_ebooks
    pattern: "*.{epub,mobi,azw,azw3}"
    category: "04_Livros"
    confidence: 95
    description: "eBook files"

  # Archives (low confidence - need review)
  - rule_id: archives
    pattern: "*.{zip,rar,7z,tar,gz}"
    category: "90_Inbox_Organizar"
    subcategory: "Arquivos_Compactados"
    confidence: 70
    description: "Compressed archives"
```

## Rule Priority

Rules are evaluated in order. **First match wins**.

Place more specific rules before general ones:

```yaml
rules:
  # Specific: invoices with keywords
  - rule_id: finance_invoices
    pattern: "*.pdf"
    category: "02_Financas"
    keywords: ["invoice", "fatura"]
    confidence: 90

  # General: any PDF
  - rule_id: documents_pdf
    pattern: "*.pdf"
    category: "01_Trabalho"
    confidence: 70
```

## Confidence Levels

| Level | Range | Description |
|-------|-------|-------------|
| High | 90-100 | Extension-based, very confident |
| Medium | 70-89 | Pattern + keywords match |
| Low | 50-69 | Fallback, needs review |

Files with confidence below threshold go to `90_Inbox_Organizar`.

## Keyword Matching

Keywords are matched against:
1. `content_excerpt` (extracted text)
2. Filename

Match is case-insensitive and partial.

```yaml
keywords:
  - "invoice"  # Matches "Invoice", "INVOICE", "invoice_2024.pdf"
```

## Testing Rules

```bash
# Preview classification without moving
python organize.py plan ~/TestDir --rules-only -v

# Check specific file
python organize.py scan ~/TestDir -v
```

## Debugging

Enable verbose mode to see rule matching:

```bash
python organize.py -v plan ~/Documents
```

Output includes:
- Which rule matched
- Confidence score
- Why other rules didn't match

## See Also

- [CLI Usage](../user-guide/CLI_USAGE.md)
- [Categories](CATEGORIES.md)
- [Architecture](../developer/ARCHITECTURE.md)
