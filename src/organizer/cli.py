# =============================================================================
# Local File Organizer - CLI Component
# =============================================================================
"""
Command-Line Interface for the Smart File Organizer.

Commands:
- scan: Scan directory and show files
- plan: Generate execution plan
- execute: Execute plan (dry-run by default)
- info: Show configuration and status

AI Backends:
- --local: Use Ollama (offline, private)
- --gemini: Use Google Gemini API
- --openai: Use OpenAI API

Safety Features:
- Dry-run by default (--apply required for execution)
- Human-readable plan preview (Markdown)
- Execution manifest for audit/rollback
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Literal

import click

from src.organizer.models import FileRecord, Classification, PlanItem, VALID_CATEGORIES
from src.organizer.scanner import Scanner
from src.organizer.extractor import Extractor
from src.organizer.rules import RuleEngine, Rule, load_rules_from_yaml
from src.organizer.llm import LLMClassifier, OllamaClient
from src.organizer.planner import Planner
from src.organizer.executor import Executor


# =============================================================================
# Version and Configuration
# =============================================================================

__version__ = "1.0.0"

# Default paths
DEFAULT_RULES_PATH = Path("configs/rules.yaml")
DEFAULT_OUTPUT_DIR = Path("plans")
DEFAULT_LOG_DIR = Path("logs")

# AI Backend types
AIBackend = Literal["local", "gemini", "openai", "rules-only"]


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# =============================================================================
# AI Backend Factory
# =============================================================================

def get_ai_classifier(backend: AIBackend, model: Optional[str] = None):
    """
    Get AI classifier based on backend selection.
    
    Args:
        backend: AI backend to use (local, gemini, openai, rules-only)
        model: Optional model name override
    
    Returns:
        Classifier instance or None for rules-only
    """
    if backend == "rules-only":
        return None
    
    if backend == "local":
        # Use Ollama with model override
        return LLMClassifier(backend="ollama", model=model)
    
    if backend == "gemini":
        # Import Gemini analyzer from V1
        try:
            from src.ai_analyzer import AIAnalyzer
            from src.settings_manager import SettingsManager
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise click.ClickException(
                    "GOOGLE_API_KEY not set. Run: set GOOGLE_API_KEY=your_key"
                )
            
            # Create settings manager with API key
            settings = SettingsManager()
            settings.set_setting("google_api_key", api_key)
            if model:
                settings.set_setting("ai.gemini_model", model)
            
            return AIAnalyzer(settings_manager=settings)
        except ImportError as e:
            raise click.ClickException(f"Gemini analyzer not available: {e}")
    
    if backend == "openai":
        # Import OpenAI analyzer from V1
        try:
            from src.openai_analyzer import OpenAIAnalyzer
            from src.settings_manager import SettingsManager
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise click.ClickException(
                    "OPENAI_API_KEY not set. Run: set OPENAI_API_KEY=your_key"
                )
            
            # Create settings manager with API key
            settings = SettingsManager()
            settings.set_setting("openai_api_key", api_key)
            if model:
                settings.set_setting("ai.openai_model", model)
            
            return OpenAIAnalyzer(settings_manager=settings)
        except ImportError as e:
            raise click.ClickException(f"OpenAI analyzer not available: {e}")
    
    raise click.ClickException(f"Unknown backend: {backend}")


def detect_default_backend() -> AIBackend:
    """
    Detect the best available backend.
    
    Priority:
    1. Local (Ollama) if running
    2. Gemini if API key set
    3. OpenAI if API key set
    4. Rules-only as fallback
    """
    # Check Ollama
    try:
        client = OllamaClient()
        if client.health_check():
            return "local"
    except Exception:
        pass
    
    # Check Gemini
    if os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    
    # Check OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    
    # Fallback to rules-only
    return "rules-only"


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# =============================================================================
# CLI Group
# =============================================================================

@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--local", "backend", flag_value="local", help="Use Ollama (local, offline)")
@click.option("--gemini", "backend", flag_value="gemini", help="Use Google Gemini API")
@click.option("--openai", "backend", flag_value="openai", help="Use OpenAI API")
@click.option("--rules-only", "backend", flag_value="rules-only", help="Use only rules, no AI")
@click.option("--model", "-m", help="Model name (e.g., qwen2.5:14b, gpt-4, gemini-pro)")
@click.option('--batch-size', type=int, default=None,
              help='Override auto-detected batch size for GPU utilization')
@click.option('--max-concurrent', type=int, default=None,
              help='Override max concurrent LLM requests')
@click.option('--gpu-tier', type=click.Choice(['ultra_high_end', 'high_end', 'upper_mid_range', 
                                                'mid_range', 'low_end', 'cpu']),
              help='Force specific GPU tier (auto-detected if not specified)')
@click.version_option(__version__, "--version", "-V")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool, backend: Optional[str], model: Optional[str], 
        batch_size: int, max_concurrent: int, gpu_tier: str) -> None:
    """
    Smart File Organizer - AI-powered file organization.
    
    Supports multiple AI backends:
    
    \b
      --local     Use Ollama (offline, private) [DEFAULT if available]
      --gemini    Use Google Gemini API (requires GOOGLE_API_KEY)
      --openai    Use OpenAI API (requires OPENAI_API_KEY)
      --rules-only Use only classification rules, no AI
    
    Dry-run by default - use --apply flag to execute operations.
    
    \b
    Examples:
      organize scan ~/Documents --local
      organize plan ~/Downloads --gemini --model gemini-1.5-pro
      organize execute plan.json --apply
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["backend"] = backend or detect_default_backend()
    ctx.obj["model"] = model
    ctx.obj["batch_size"] = batch_size
    ctx.obj["max_concurrent"] = max_concurrent
    ctx.obj["gpu_tier"] = gpu_tier
    setup_logging(verbose, quiet)


# =============================================================================
# Scan Command
# =============================================================================

@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file for scan results (JSON)")
@click.option("--min-size", type=int, default=1024, help="Minimum file size in bytes")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.pass_context
def scan(
    ctx: click.Context,
    directory: Path,
    output: Optional[Path],
    min_size: int,
    verbose: bool,
) -> None:
    """
    Scan a directory for files to organize.
    
    Shows statistics about found files and optionally saves results.
    """
    verbose = verbose or ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)
    
    if not quiet:
        click.echo(f"Scanning: {directory}")
    
    scanner = Scanner(min_file_size=min_size)
    
    try:
        records = list(scanner.scan(directory))
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    
    # Show results
    if not quiet:
        click.echo(f"\nFound {len(records)} files")
        click.echo(f"  Scanned: {scanner.stats['files_scanned']}")
        click.echo(f"  Excluded: {scanner.stats['files_excluded']}")
        click.echo(f"  Directories excluded: {scanner.stats['directories_excluded']}")
        click.echo(f"  Total size: {scanner.stats['total_size_bytes']:,} bytes")
    
    if verbose:
        click.echo("\nFiles found:")
        for record in records[:20]:  # Limit to first 20
            click.echo(f"  {record.path.name} ({record.size:,} bytes)")
        if len(records) > 20:
            click.echo(f"  ... and {len(records) - 20} more")
    
    # Save output if requested
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "scanned_at": datetime.now().isoformat(),
            "directory": str(directory),
            "stats": scanner.stats,
            "files": [
                {
                    "path": str(r.path),
                    "size": r.size,
                    "extension": r.extension,
                    "sha256": r.sha256,
                }
                for r in records
            ],
        }
        output.write_text(json.dumps(data, indent=2))
        if not quiet:
            click.echo(f"\nResults saved to: {output}")


# =============================================================================
# Plan Command
# =============================================================================

@cli.command()
@click.argument('source_dir', type=click.Path(exists=True))
@click.option('--local', 'backend_local', is_flag=True, 
              help='Use Ollama (local AI) - config from settings.yaml')
@click.option('--gemini', 'backend_gemini', is_flag=True,
              help='Use Google Gemini - requires GOOGLE_API_KEY')
@click.option('--openai', 'backend_openai', is_flag=True,
              help='Use OpenAI GPT - requires OPENAI_API_KEY')
@click.option('--rules-only', is_flag=True,
              help='Use only rule-based classification (no AI)')
@click.option('--model', type=str, default=None,
              help='Override default model from settings.yaml')
@click.option('--batch-size', type=int, default=None,
              help='Override batch size (Ollama: auto-detected, Cloud: 5)')
@click.option('--max-concurrent', type=int, default=None,
              help='Override max concurrent requests')
@click.option('--gpu-tier', type=click.Choice(['ultra_high_end', 'high_end', 'upper_mid_range', 
                                                'mid_range', 'low_end', 'cpu']),
              help='Force GPU tier for Ollama (auto-detected by default)')
def plan(source_dir: str, backend_local: bool, backend_gemini: bool, backend_openai: bool,
         rules_only: bool, model: str, batch_size: int, max_concurrent: int, gpu_tier: str):
    """Generate organization plan using specified AI backend."""
    
    from pathlib import Path
    from .scanner import scan_directory
    from .extractor import extract_content
    from .rules import apply_rules, load_rules
    from .llm import LLMClassifier
    from .planner import generate_plan
    from ..settings_manager import get_settings_manager
    
    # Determine backend from flags
    backend = _determine_backend(backend_local, backend_gemini, backend_openai)
    
    logger.info(f"🎯 Backend: {backend.upper()}")
    logger.info(f"📁 Source: {source_dir}")
    
    # Load settings
    settings = get_settings_manager()
    
    # Initialize LLM (or skip if rules-only)
    llm = None
    if not rules_only:
        llm_kwargs = {}
        if batch_size:
            llm_kwargs["batch_size"] = batch_size
        if max_concurrent:
            llm_kwargs["max_concurrent"] = max_concurrent
        if gpu_tier:
            llm_kwargs["gpu_tier"] = gpu_tier
        
        llm = LLMClassifier(backend=backend, model=model, **llm_kwargs)
    
    # Run pipeline
    source_path = Path(source_dir).resolve()
    
    # 1. Scan
    files = scan_directory(source_path)
    logger.info(f"📊 Found {len(files)} files")
    
    # 2. Extract content
    for file_record in files:
        extract_content(file_record)
    
    # 3. Apply rules
    rules = load_rules()
    classified = []
    needs_llm = []
    
    for file_record in files:
        rule_result = apply_rules(file_record, rules)
        if rule_result and rule_result.confidence >= 85:
            classified.append(rule_result)
        else:
            needs_llm.append(file_record)
    
    logger.info(f"✅ Rules: {len(classified)}, 🤖 LLM needed: {len(needs_llm)}")
    
    # 4. Classify with LLM (batch processing)
    if needs_llm and llm:
        import asyncio
        batch_results = asyncio.run(llm.classify_batch(needs_llm))
        classified.extend(batch_results)
    
    # 5. Generate plan
    output_plan = Path("plans") / f"plan_{source_path.name}_{datetime.now():%Y%m%d_%H%M%S}.json"
    plan = generate_plan(classified, output_plan)
    
    logger.info(f"📝 Plan saved: {output_plan}")
    logger.info(f"✨ Total: {len(classified)} files classified")


def _determine_backend(local: bool, gemini: bool, openai: bool) -> str:
    """
    Determine backend from CLI flags.
    
    Priority: --local > --gemini > --openai > settings.yaml default
    """
    if local:
        return "ollama"
    elif gemini:
        return "gemini"
    elif openai:
        return "openai"
    else:
        # Use default from settings.yaml
        settings = get_settings_manager()
        default = settings.get_default_backend()
        logger.info(f"No backend flag specified, using default: {default}")
        return default


# =============================================================================
# Execute Command
# =============================================================================

@cli.command()
@click.argument("plan_file", type=click.Path(exists=True, path_type=Path))
@click.option("--apply", is_flag=True, help="Actually execute operations (default is dry-run)")
@click.option("--log-dir", type=click.Path(path_type=Path), default=DEFAULT_LOG_DIR, help="Directory for execution logs")
@click.pass_context
def execute(
    ctx: click.Context,
    plan_file: Path,
    apply: bool,
    log_dir: Path,
) -> None:
    """
    Execute a previously generated plan.
    
    By default, runs in dry-run mode (no actual changes).
    Use --apply to actually execute the operations.
    """
    quiet = ctx.obj.get("quiet", False)
    verbose = ctx.obj.get("verbose", False)
    
    # Load plan
    try:
        plan_data = json.loads(plan_file.read_text())
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid plan file: {e}", err=True)
        raise SystemExit(1)
    
    base_path = Path(plan_data.get("base_path", "."))
    
    # Convert plan items
    plan_items = []
    for item in plan_data.get("items", []):
        plan_items.append(PlanItem(
            action=item["action"],
            src=Path(item["src"]),
            dst=Path(item["dst"]) if item.get("dst") else None,
            reason=item.get("reason", ""),
            confidence=item.get("confidence", 0),
            rule_id=item.get("rule_id"),
            llm_used=item.get("llm_used", False),
        ))
    
    if not plan_items:
        click.echo("No items in plan.")
        return
    
    # Show mode
    if apply:
        if not quiet:
            click.echo("Executing plan (APPLY MODE - files will be modified)")
    else:
        if not quiet:
            click.echo("Executing plan (DRY-RUN MODE - no changes will be made)")
    
    # Execute
    dry_run = not apply
    executor = Executor(base_path, dry_run=dry_run, log_dir=log_dir)
    results = executor.execute_plan(plan_items)
    
    # Show results
    if not quiet:
        click.echo(f"\nExecution {'completed' if apply else 'simulated'}:")
        click.echo(f"  Total: {executor.stats['total_executed']}")
        click.echo(f"  Successful: {executor.stats['successful']}")
        click.echo(f"  Failed: {executor.stats['failed']}")
        
        if verbose:
            click.echo("\nDetails:")
            for result in results:
                status_icon = "✓" if result.status in ("success", "dry-run", "skipped") else "✗"
                click.echo(f"  {status_icon} {result.plan_item.action}: {result.plan_item.src.name}")
                if result.error:
                    click.echo(f"      Error: {result.error}")
    
    # Save manifest
    if apply:
        manifest_path = executor.save_manifest()
        if not quiet:
            click.echo(f"\nManifest saved: {manifest_path}")
    
    # Exit code based on failures
    if executor.stats["failed"] > 0:
        raise SystemExit(1)


# =============================================================================
# Info Command
# =============================================================================

@cli.command()
def info():
    """Show system configuration and available backends."""
    import os
    from ..settings_manager import get_settings_manager
    from .gpu_detector import get_detector
    
    click.echo("🔍 Smart File Organizer - System Info\n")
    
    # Settings
    settings = get_settings_manager()
    click.echo(f"⚙️  Settings: {settings.settings_file}")
    click.echo(f"   Default backend: {settings.get_default_backend()}\n")
    
    # Ollama
    ollama_config = settings.get_backend_config("ollama")
    click.echo("🖥️  Ollama (Local AI)")
    click.echo(f"   URL: {ollama_config.get('base_url')}")
    click.echo(f"   Model: {ollama_config.get('default_model')}")
    
    # GPU detection
    detector = get_detector()
    vram_gb = detector.detect_vram()
    if vram_gb:
        tier = detector.get_tier(vram_gb)
        gpu_config = detector.get_config(tier=tier)
        click.echo(f"   GPU: ✅ {vram_gb:.1f}GB VRAM ({tier})")
        click.echo(f"   Recommended: batch={gpu_config['batch_size']}, "
                   f"concurrent={gpu_config['max_concurrent']}")
    else:
        click.echo("   GPU: ❌ Not detected (CPU mode)")
    
    # Gemini
    click.echo("\n☁️  Google Gemini")
    gemini_config = settings.get_backend_config("gemini")
    click.echo(f"   Model: {gemini_config.get('default_model')}")
    click.echo(f"   API Key: {'✅ Set' if os.getenv('GOOGLE_API_KEY') else '❌ Not set'}")
    
    # OpenAI
    click.echo("\n☁️  OpenAI")
    openai_config = settings.get_backend_config("openai")
    click.echo(f"   Model: {openai_config.get('default_model')}")
    click.echo(f"   API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

async def plan_async(
    source_dir: Path,
    rules: List[Rule],
    llm_classifier: LLMClassifier,
    output_plan: Path
):
    """
    Gera plano de organização com processamento em batch
    """
    # Scan
    files = scan_directory(source_dir)
    logger.info(f"Encontrados {len(files)} arquivos")
    
    # Extract content
    for file_record in files:
        extract_content(file_record)
    
    # Classify: primeiro por regras, depois LLM em batch
    classified = []
    needs_llm = []

    for file_record in files:
        rule_result = apply_rules(file_record, rules)
        if rule_result and rule_result.confidence >= 85:
            classified.append(rule_result)
        else:
            needs_llm.append(file_record)
    
    logger.info(f"Regras: {len(classified)}, LLM necessário: {len(needs_llm)}")
    
    # 🔥 Processa LLM em batches
    if needs_llm:
        batch_size = 8  # Ajuste conforme VRAM disponível
        for i in range(0, len(needs_llm), batch_size):
            batch = needs_llm[i:i+batch_size]
            logger.info(f"Processando batch {i//batch_size + 1}/{(len(needs_llm)+batch_size-1)//batch_size}")
            
            batch_results = await llm_classifier.classify_batch(batch)
            classified.extend(batch_results)
    
    # Generate plan
    plan = generate_plan(classified, output_plan)
    logger.info(f"Plano salvo: {output_plan}")
    
    return plan

