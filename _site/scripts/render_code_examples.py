#!/usr/bin/env python3

from __future__ import annotations

import ast
import base64
import io
import json
import os
import re
import runpy
import shutil
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import nbformat
import yaml
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = ROOT / "assets" / "code"
OUTPUT_DIR = ROOT / "assets" / "generated" / "code"
MANIFEST_PATH = ROOT / "_data" / "code_examples.yml"
RUNS_PATH = ROOT / "_data" / "code_example_runs.yml"
PAGE_RUN_DIRS = [ROOT, ROOT / "_posts"]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "code-example"


def relative_url(path: Path) -> str:
    return "/" + path.relative_to(ROOT).as_posix()


def title_from_python_source(script_path: Path, source: str) -> str:
    try:
        module = ast.parse(source)
        docstring = ast.get_docstring(module)
        if docstring:
            return docstring.strip().splitlines()[0].strip()
    except SyntaxError:
        pass
    return script_path.stem.replace("_", " ").replace("-", " ").title()


def title_from_notebook(notebook_path: Path, notebook: nbformat.NotebookNode) -> str:
    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            lines = [line.strip() for line in cell.source.splitlines() if line.strip()]
            for line in lines:
                if line.startswith("#"):
                    return line.lstrip("#").strip()
            if lines:
                return lines[0]
    return notebook_path.stem.replace("_", " ").replace("-", " ").title()


def fresh_output_dir(slug: str) -> Path:
    output_dir = OUTPUT_DIR / slug
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_result(
    *,
    example_type: str,
    title: str,
    source_path: Path,
    source_code: str,
    plots: list[str],
    stdout: str,
    stderr: str,
    success: bool,
    markdown_blocks: list[str],
    params: dict | None,
) -> dict:
    return {
        "type": example_type,
        "title": title,
        "source_url": relative_url(source_path),
        "source_code": source_code.rstrip(),
        "plots": plots,
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
        "success": success,
        "markdown_blocks": markdown_blocks,
        "params": params or {},
    }


def render_python_script(script_path: Path, *, slug: str, title: str | None = None, params: dict | None = None) -> dict:
    source = script_path.read_text(encoding="utf-8")
    title = title or title_from_python_source(script_path, source)
    output_dir = fresh_output_dir(slug)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    plot_urls: list[str] = []
    plot_index = 0

    def save_open_figures() -> None:
        nonlocal plot_index
        for figure_number in list(plt.get_fignums()):
            figure = plt.figure(figure_number)
            plot_index += 1
            output_path = output_dir / f"plot-{plot_index}.png"
            figure.savefig(output_path, dpi=160, bbox_inches="tight")
            plot_urls.append(relative_url(output_path))
            plt.close(figure)

    original_cwd = Path.cwd()
    original_show = plt.show
    original_sys_path = list(sys.path)
    original_env = os.environ.get("CODE_EXAMPLE_PARAMS")
    error_text = ""
    success = True

    def patched_show(*_args, **_kwargs) -> None:
        save_open_figures()

    try:
        os.chdir(script_path.parent)
        sys.path.insert(0, str(script_path.parent))
        if params:
          os.environ["CODE_EXAMPLE_PARAMS"] = json.dumps(params)
        elif "CODE_EXAMPLE_PARAMS" in os.environ:
          del os.environ["CODE_EXAMPLE_PARAMS"]
        plt.show = patched_show
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            runpy.run_path(
                str(script_path),
                run_name="__main__",
                init_globals={"CODE_EXAMPLE_PARAMS": params or {}},
            )
        save_open_figures()
    except Exception:
        success = False
        error_text = traceback.format_exc()
        save_open_figures()
    finally:
        plt.show = original_show
        plt.close("all")
        sys.path[:] = original_sys_path
        if original_env is None:
            os.environ.pop("CODE_EXAMPLE_PARAMS", None)
        else:
            os.environ["CODE_EXAMPLE_PARAMS"] = original_env
        os.chdir(original_cwd)

    stderr_text = stderr_buffer.getvalue().strip()
    if error_text:
        stderr_text = f"{stderr_text}\n\n{error_text}".strip()

    return build_result(
        example_type="python",
        title=title,
        source_path=script_path,
        source_code=source,
        plots=plot_urls,
        stdout=stdout_buffer.getvalue(),
        stderr=stderr_text,
        success=success,
        markdown_blocks=[],
        params=params,
    )


def render_notebook(notebook_path: Path, *, slug: str, title: str | None = None, params: dict | None = None) -> dict:
    output_dir = fresh_output_dir(slug)
    notebook = nbformat.read(notebook_path, as_version=4)
    title = title or title_from_notebook(notebook_path, notebook)

    executed_notebook = nbformat.from_dict(notebook)
    if params:
        param_cell = nbformat.v4.new_code_cell(
            source=(
                "CODE_EXAMPLE_PARAMS = "
                + json.dumps(params, sort_keys=True)
            ),
            id="injected-params",
        )
        executed_notebook.cells.insert(0, param_cell)

    client = NotebookClient(
        executed_notebook,
        timeout=120,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )

    success = True
    error_text = ""
    try:
        executed = client.execute()
    except Exception:
        success = False
        error_text = traceback.format_exc()
        executed = notebook

    markdown_blocks: list[str] = []
    source_chunks: list[str] = []
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    plot_urls: list[str] = []
    plot_index = 0

    for cell in executed.cells:
        if cell.cell_type == "markdown":
            content = cell.source.strip()
            if content:
                markdown_blocks.append(content)
            continue

        if cell.cell_type != "code":
            continue

        source = cell.source.strip()
        if source:
            source_chunks.append(source)

        for output in cell.get("outputs", []):
            output_type = output.get("output_type")
            if output_type == "stream":
                text = "".join(output.get("text", ""))
                if output.get("name") == "stderr":
                    stderr_chunks.append(text.rstrip())
                else:
                    stdout_chunks.append(text.rstrip())
            elif output_type in {"display_data", "execute_result"}:
                data = output.get("data", {})
                png_data = data.get("image/png")
                if png_data:
                    plot_index += 1
                    output_path = output_dir / f"plot-{plot_index}.png"
                    output_path.write_bytes(base64.b64decode(png_data))
                    plot_urls.append(relative_url(output_path))
                text_data = data.get("text/plain")
                if text_data:
                    stdout_chunks.append("".join(text_data).rstrip())
            elif output_type == "error":
                traceback_lines = output.get("traceback", [])
                if traceback_lines:
                    stderr_chunks.append("\n".join(traceback_lines))
                else:
                    stderr_chunks.append(f"{output.get('ename', 'Error')}: {output.get('evalue', '')}".strip())

    if error_text:
        stderr_chunks.append(error_text.rstrip())

    source_chunks = [chunk for chunk in source_chunks if "CODE_EXAMPLE_PARAMS =" not in chunk]

    return build_result(
        example_type="notebook",
        title=title,
        source_path=notebook_path,
        source_code="\n\n".join(source_chunks),
        plots=plot_urls,
        stdout="\n".join(chunk for chunk in stdout_chunks if chunk),
        stderr="\n\n".join(chunk for chunk in stderr_chunks if chunk),
        success=success,
        markdown_blocks=markdown_blocks,
        params=params,
    )


def load_run_specs() -> list[dict]:
    if not RUNS_PATH.exists():
        return []
    data = yaml.safe_load(RUNS_PATH.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError(f"{RUNS_PATH} must contain a list of run definitions.")
    return data


def parse_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, remainder = text.split("---\n", 1)
    if "\n---\n" not in remainder:
        return {}
    front_matter, _ = remainder.split("\n---\n", 1)
    data = yaml.safe_load(front_matter) or {}
    return data if isinstance(data, dict) else {}


def load_page_run_specs() -> list[dict]:
    specs: list[dict] = []
    for base_dir in PAGE_RUN_DIRS:
        if not base_dir.exists():
            continue
        for path in sorted(base_dir.glob("*.md")):
            front_matter = parse_front_matter(path)
            page_runs = front_matter.get("code_example_runs") or []
            if not isinstance(page_runs, list):
                raise ValueError(f"{path} code_example_runs must be a list.")
            for spec in page_runs:
                if not isinstance(spec, dict):
                    raise ValueError(f"{path} contains an invalid code_example_runs entry.")
                spec_copy = dict(spec)
                spec_copy.setdefault("_declared_in", path.relative_to(ROOT).as_posix())
                specs.append(spec_copy)
    return specs


def default_run_specs() -> list[dict]:
    specs: list[dict] = []
    for source_path in sorted(CODE_DIR.iterdir()):
        if source_path.suffix in {".py", ".ipynb"}:
            specs.append({"slug": slugify(source_path.stem), "source": source_path.name})
    return specs


def render_from_spec(spec: dict) -> tuple[str, dict]:
    source_name = spec["source"]
    source_path = CODE_DIR / source_name
    if not source_path.exists():
        raise FileNotFoundError(f"Missing code example source: {source_path}")

    slug = slugify(spec.get("slug", Path(source_name).stem))
    title = spec.get("title")
    params = spec.get("params") or {}

    if source_path.suffix == ".py":
        result = render_python_script(source_path, slug=slug, title=title, params=params)
    elif source_path.suffix == ".ipynb":
        result = render_notebook(source_path, slug=slug, title=title, params=params)
    else:
        raise ValueError(f"Unsupported code example source type: {source_path.suffix}")

    return slug, result


def main() -> int:
    CODE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict] = {}
    global_specs = load_run_specs()
    page_specs = load_page_run_specs()
    run_specs = global_specs + page_specs if (global_specs or page_specs) else default_run_specs()
    for spec in run_specs:
        slug, result = render_from_spec(spec)
        if slug in manifest:
            origin = spec.get("_declared_in", RUNS_PATH.relative_to(ROOT).as_posix())
            raise ValueError(f"Duplicate code example slug '{slug}' declared in {origin}.")
        manifest[slug] = result

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        yaml.safe_dump(manifest, sort_keys=True, allow_unicode=False),
        encoding="utf-8",
    )
    print(f"Rendered {len(manifest)} code example(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
