# Plano de Implementação - SmartFileOrganizer GUI

## Diagnóstico Atual

### Problema Principal Identificado: Incompatibilidade de Campos
A GUI espera campos diferentes dos retornados pelo `FileAnalyzer`:

| GUI Espera | FileAnalyzer Retorna |
|------------|---------------------|
| `size` | `file_size` |
| `filename` | `file_name` |
| `path` | `file_path` |
| `file_type` | `file_type` ✅ |
| `category` | `ai_analysis.category` |
| `keywords` | `ai_analysis.keywords` |
| `summary` | `ai_analysis.summary` |

---

## Plano por Aba

### 🟢 ABA 1: MAIN (Scan/Organize)

**Status:** Parcialmente funcional - campos incompatíveis

**Problemas:**
1. ❌ `update_file_list()` - busca `size` mas deveria buscar `file_size`
2. ❌ `update_file_list()` - busca `filename` mas deveria buscar `file_name`
3. ❌ `search_files()` - mesmos problemas de campos
4. ❌ `show_file_details()` - busca `size`, `filename`, `path`
5. ❌ Treeview tem colunas erradas (Category, Type, Size) vs dados

**Correções Necessárias:**
```python
# Em update_file_list():
file.get("file_size", 0)  # ao invés de "size"
file.get("file_name", "")  # ao invés de "filename"
file.get("file_path", "")  # ao invés de "path"

# Para category/keywords/summary:
ai_analysis = file.get("ai_analysis", {})
category = ai_analysis.get("category", "Unclassified")
keywords = ai_analysis.get("keywords", [])
```

**Prioridade:** 🔴 ALTA

---

### 🟢 ABA 2: SETTINGS

**Status:** Funcional após correções recentes

**Problemas Resolvidos:**
- ✅ Widgets não estavam com layout (pack/grid)
- ✅ AI Settings tab adicionada
- ✅ Provider Google/OpenAI/Ollama configurável

**Pendente:**
1. ⚠️ Validação de API keys antes de salvar
2. ⚠️ Feedback visual quando settings são salvos

**Prioridade:** 🟡 MÉDIA

---

### 🟢 ABA 3: RULES

**Status:** Não verificado completamente

**Funções a Verificar:**
- `_create_rules_tab()`
- `browse_rules_file()`
- `load_rules()`
- `save_rules()`
- `add_rule()`, `edit_rule()`, `delete_rule()`

**Prioridade:** 🟡 MÉDIA

---

### 🟢 ABA 4: IMAGES

**Status:** Não verificado completamente

**Funções a Verificar:**
- `_create_images_tab()`
- Configurações de análise de imagem
- Thumbnails e EXIF extraction

**Prioridade:** 🟢 BAIXA

---

### 🟢 ABA 5: BATCH

**Status:** Não verificado completamente

**Funções a Verificar:**
- `_create_batch_tab()`
- Configurações de processamento em lote
- Pause/Resume functionality

**Prioridade:** 🟢 BAIXA

---

### 🟢 ABA 6: OCR

**Status:** Não implementado (comentado)

**Pendente:**
- Criar `_create_ocr_tab()`
- Integrar com `ocr_service.py`

**Prioridade:** 🟢 BAIXA

---

### 🟢 ABA 7: DUPLICATES

**Status:** Parcialmente funcional

**Problemas:**
1. ⚠️ `consume_queue()` não trata mensagem "duplicates"
2. ⚠️ `show_duplicate_details()` pode ter campos incompatíveis

**Prioridade:** 🟡 MÉDIA

---

### 🟢 ABA 8: SEARCH

**Status:** Parcialmente funcional

**Problemas:**
1. ⚠️ `consume_queue()` não trata mensagem "search_results"
2. ⚠️ `show_search_result_details()` pode ter campos incompatíveis

**Prioridade:** 🟡 MÉDIA

---

### 🟢 ABA 9: TAGS

**Status:** Não verificado completamente

**Funções a Verificar:**
- Tag management
- Tag application to files

**Prioridade:** 🟢 BAIXA

---

## Ordem de Implementação Recomendada

### Fase 1: Correções Críticas (AGORA)
1. **Corrigir mapeamento de campos em `update_file_list()`**
2. **Corrigir mapeamento de campos em `search_files()`**
3. **Corrigir mapeamento de campos em `show_file_details()`**
4. **Ajustar colunas do Treeview**

### Fase 2: Handlers de Queue (PRÓXIMO)
1. Adicionar handler para "duplicates" em `consume_queue()`
2. Adicionar handler para "search_results" em `consume_queue()`
3. Adicionar handler para "index_results" em `consume_queue()`

### Fase 3: Validações e UX (DEPOIS)
1. Validação de API keys
2. Feedback visual melhorado
3. Mensagens de erro mais claras

### Fase 4: Features Faltantes (FUTURO)
1. OCR tab implementation
2. Advanced batch processing UI
3. Report generation

---

## Correção Imediata

O arquivo `gui.py` precisa de uma função helper para normalizar os dados:

```python
def _normalize_file_data(self, file_info):
    """Normalize file data from FileAnalyzer to GUI format"""
    ai_analysis = file_info.get("ai_analysis", {})
    return {
        "filename": file_info.get("file_name", ""),
        "path": file_info.get("file_path", ""),
        "size": file_info.get("file_size", 0),
        "file_type": file_info.get("file_type", "Unknown"),
        "category": ai_analysis.get("category", "Unclassified"),
        "keywords": ai_analysis.get("keywords", []),
        "summary": ai_analysis.get("summary", ""),
        "theme": ai_analysis.get("theme", ""),
        "metadata": file_info.get("metadata", {}),
        # Preserve original data
        "_original": file_info
    }
```
