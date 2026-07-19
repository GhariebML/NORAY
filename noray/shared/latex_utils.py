"""
NORAY — LaTeX Compilation & PDF Inspection Utilities

Handles CV and cover letter compilation, PDF verification,
and artifact cleanup. Shared by career_agent and scholarship_agent.
"""

import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass

from noray.config import CV_DIR, COVER_LETTERS_DIR


@dataclass
class CompileResult:
    """Result of a LaTeX compilation attempt."""
    success: bool
    pdf_path: Path | None = None
    errors: list[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


def compile_cv(tex_path: Path, output_dir: Path | None = None) -> CompileResult:
    """
    Compile a CV LaTeX file using lualatex.
    
    Args:
        tex_path: Path to the .tex file
        output_dir: Output directory (defaults to same directory as .tex)
    
    Returns:
        CompileResult with success status, pdf path, and any errors
    """
    if output_dir is None:
        output_dir = tex_path.parent

    return _compile_latex(tex_path, output_dir, engine="lualatex")


def compile_cover_letter(tex_path: Path, output_dir: Path | None = None) -> CompileResult:
    """
    Compile a cover letter LaTeX file using xelatex.
    
    Args:
        tex_path: Path to the .tex file
        output_dir: Output directory (defaults to same directory as .tex)
    
    Returns:
        CompileResult with success status, pdf path, and any errors
    """
    if output_dir is None:
        output_dir = tex_path.parent

    return _compile_latex(tex_path, output_dir, engine="xelatex")


def _compile_latex(tex_path: Path, output_dir: Path, engine: str) -> CompileResult:
    """Internal: compile a LaTeX file with the specified engine."""
    if not tex_path.exists():
        return CompileResult(success=False, errors=[f"File not found: {tex_path}"])

    # Check if engine is available
    engine_path = shutil.which(engine)
    if not engine_path:
        return CompileResult(
            success=False,
            errors=[f"{engine} not found. Install TeX Live or MiKTeX."]
        )

    cmd = [
        engine_path,
        "-interaction=nonstopmode",
        f"-output-directory={output_dir}",
        str(tex_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=tex_path.parent,
        )

        pdf_name = tex_path.stem + ".pdf"
        pdf_path = output_dir / pdf_name

        errors = []
        warnings = []

        if result.returncode != 0:
            # Parse errors from log
            for line in result.stdout.split("\n"):
                if line.startswith("!") or "Error" in line:
                    errors.append(line.strip())
            if not errors:
                errors = [f"Compilation failed with exit code {result.returncode}"]

        # Parse warnings
        for line in result.stdout.split("\n"):
            if "Warning" in line:
                warnings.append(line.strip())

        success = result.returncode == 0 and pdf_path.exists()

        return CompileResult(
            success=success,
            pdf_path=pdf_path if success else None,
            errors=errors,
            warnings=warnings,
        )

    except subprocess.TimeoutExpired:
        return CompileResult(success=False, errors=["Compilation timed out (60s)"])
    except Exception as e:
        return CompileResult(success=False, errors=[str(e)])


def cleanup_build_artifacts(directory: Path, keep_pdf: bool = True) -> list[str]:
    """
    Remove LaTeX build artifacts (.aux, .log, .out, .fls, .fdb_latexmk).
    
    Args:
        directory: Directory to clean
        keep_pdf: If True, keep .pdf files
    
    Returns:
        List of removed file names
    """
    extensions_to_remove = {".aux", ".log", ".out", ".fls", ".fdb_latexmk", ".synctex.gz"}
    removed = []

    for f in directory.iterdir():
        if f.is_file() and f.suffix in extensions_to_remove:
            f.unlink()
            removed.append(f.name)

    return removed


def get_pdf_page_count(pdf_path: Path) -> int | None:
    """
    Get the number of pages in a PDF file.
    Returns None if unable to determine.
    """
    try:
        # Try using PyMuPDF (fitz) if available
        import fitz
        doc = fitz.open(str(pdf_path))
        count = len(doc)
        doc.close()
        return count
    except ImportError:
        pass

    try:
        # Fallback: use pdfinfo if available
        result = subprocess.run(
            ["pdfinfo", str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.split("\n"):
            if line.startswith("Pages:"):
                return int(line.split(":")[-1].strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


def validate_cv_layout(pdf_path: Path) -> dict:
    """
    Validate CV PDF layout.
    Returns a dict with validation results.
    """
    pages = get_pdf_page_count(pdf_path)

    return {
        "pdf_exists": pdf_path.exists(),
        "page_count": pages,
        "is_two_pages": pages == 2 if pages is not None else None,
        "errors": [] if pages == 2 else [f"CV is {pages} pages, expected exactly 2"] if pages else ["Could not determine page count"],
    }


def validate_cover_letter_layout(pdf_path: Path) -> dict:
    """
    Validate cover letter PDF layout.
    Returns a dict with validation results.
    """
    pages = get_pdf_page_count(pdf_path)

    return {
        "pdf_exists": pdf_path.exists(),
        "page_count": pages,
        "is_one_page": pages == 1 if pages is not None else None,
        "errors": [] if pages == 1 else [f"Cover letter is {pages} pages, expected exactly 1"] if pages else ["Could not determine page count"],
    }
