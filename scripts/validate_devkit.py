#!/usr/bin/env python3
"""Validate the portable Godot AI DevKit without third-party dependencies."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKILL_SIZE_LIMIT = 16 * 1024
EXPECTED_GODOT_PROMPTER_SKILLS = 54
EXPECTED_OFFLINE_DOCS = 1593
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(path: Path, errors: list[str]) -> dict[str, str]:
    text = read_text(path)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        return {}

    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path.relative_to(ROOT)}: unclosed YAML frontmatter")
        return {}

    fields: dict[str, str] = {}
    for line in lines[1:closing_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")

    for required in ("name", "description"):
        value = fields.get(required, "")
        if not value:
            errors.append(f"{path.relative_to(ROOT)}: empty {required}")
        if re.search(r"\b(?:TODO|TBD)\b|\[TODO", value, re.IGNORECASE):
            errors.append(f"{path.relative_to(ROOT)}: placeholder in {required}")

    if path != ROOT / "SKILL.md" and fields.get("name") != path.parent.name:
        errors.append(
            f"{path.relative_to(ROOT)}: name '{fields.get('name', '')}' "
            f"does not match directory '{path.parent.name}'"
        )

    size = path.stat().st_size
    if size > SKILL_SIZE_LIMIT:
        errors.append(
            f"{path.relative_to(ROOT)}: {size} bytes exceeds "
            f"{SKILL_SIZE_LIMIT}-byte Skill budget"
        )
    return fields


def maintained_markdown_files() -> list[Path]:
    files = list(ROOT.glob("*.md"))
    files.extend(ROOT.glob("references/*.md"))
    files.extend(ROOT.glob("skills/**/*.md"))
    return sorted(set(path.resolve() for path in files))


def validate_links(files: list[Path], errors: list[str]) -> set[Path]:
    referenced: set[Path] = set()
    for source in files:
        for raw_target in LINK_RE.findall(read_text(source)):
            target = raw_target.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if " " in target and not target.startswith(("http://", "https://")):
                target = target.split(" ", 1)[0]
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue

            target = unquote(target.split("#", 1)[0])
            resolved = (source.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(
                    f"{source.relative_to(ROOT)}: relative link escapes package: {raw_target}"
                )
                continue

            referenced.add(resolved)
            if not resolved.exists():
                errors.append(
                    f"{source.relative_to(ROOT)}: broken relative link: {raw_target}"
                )
    return referenced


def validate_reference_reachability(referenced: set[Path], errors: list[str]) -> None:
    reference_files = list(ROOT.glob("references/*.md"))
    reference_files.extend(ROOT.glob("skills/*/references/*.md"))
    for path in sorted(reference_files):
        if path.resolve() not in referenced:
            errors.append(f"{path.relative_to(ROOT)}: orphan reference document")


def validate_counts(errors: list[str]) -> tuple[int, int, int]:
    skill_files = sorted(ROOT.glob("skills/*/SKILL.md"))
    godot_prompter = [path for path in skill_files if path.parent.name != "gdmcp"]
    offline_docs = list((ROOT / "references" / "godot-4.7-docs").glob("*.md"))

    if len(godot_prompter) != EXPECTED_GODOT_PROMPTER_SKILLS:
        errors.append(
            f"GodotPrompter Skill count is {len(godot_prompter)}, "
            f"expected {EXPECTED_GODOT_PROMPTER_SKILLS}"
        )
    if len(offline_docs) != EXPECTED_OFFLINE_DOCS:
        errors.append(
            f"offline Godot document count is {len(offline_docs)}, "
            f"expected {EXPECTED_OFFLINE_DOCS}"
        )

    readme = read_text(ROOT / "README.md")
    declared_count = re.search(r"共\s*(\d+)\s*个 Skill", readme)
    if not declared_count or int(declared_count.group(1)) != len(godot_prompter):
        errors.append("README GodotPrompter Skill count does not match package contents")

    total_skill_entries = len(skill_files) + 1
    return total_skill_entries, len(godot_prompter), len(offline_docs)


def validate_mcp_release(errors: list[str]) -> str:
    release = json.loads(read_text(ROOT / "addons" / "godot_mcp" / "cli_release.json"))
    version = str(release.get("version", ""))
    plugin_cfg = read_text(ROOT / "addons" / "godot_mcp" / "plugin.cfg")
    plugin_version = re.search(r'^version="([^"]+)"', plugin_cfg, re.MULTILINE)
    if not plugin_version or plugin_version.group(1) != version:
        errors.append("Godot MCP plugin.cfg version does not match cli_release.json")

    for relative in ("README.md", "THIRD_PARTY_NOTICES.md"):
        if version not in read_text(ROOT / relative):
            errors.append(f"{relative}: missing Godot MCP version {version}")

    executable = ROOT / ".gdmcp" / "bin" / "gdmcp.exe"
    if not executable.is_file():
        errors.append(".gdmcp/bin/gdmcp.exe: missing bundled Windows CLI")
        return version

    notices = read_text(ROOT / "THIRD_PARTY_NOTICES.md")
    expected_hash = re.search(
        r"Bundled `gdmcp\.exe` SHA-256: `([0-9a-fA-F]{64})`", notices
    )
    actual_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
    if not expected_hash:
        errors.append("THIRD_PARTY_NOTICES.md: missing bundled gdmcp.exe SHA-256")
    elif actual_hash != expected_hash.group(1).lower():
        errors.append(".gdmcp/bin/gdmcp.exe: SHA-256 does not match third-party notice")
    return version


def main() -> int:
    errors: list[str] = []
    required = (
        "README.md",
        "AGENTS.md",
        "SKILL.md",
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
    )
    for relative in required:
        if not (ROOT / relative).exists():
            errors.append(f"missing required package entry: {relative}")

    total_skills, godot_prompter_skills, offline_docs = validate_counts(errors)
    for skill in [ROOT / "SKILL.md", *sorted(ROOT.glob("skills/*/SKILL.md"))]:
        parse_frontmatter(skill, errors)

    markdown_files = maintained_markdown_files()
    referenced = validate_links(markdown_files, errors)
    validate_reference_reachability(referenced, errors)
    mcp_version = validate_mcp_release(errors)

    if errors:
        print("Godot AI DevKit validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Godot AI DevKit validation passed: "
        f"{total_skills} Skill entries "
        f"({godot_prompter_skills} GodotPrompter + gdmcp + root), "
        f"{offline_docs} offline docs, Godot-MCP-Native {mcp_version}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
