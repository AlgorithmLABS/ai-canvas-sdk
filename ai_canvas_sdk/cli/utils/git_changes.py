"""git diff 기반 변경 top-level 노드 폴더 탐지 (register --changed 용).

CI 워크플로가 넘긴 before/after SHA 로 변경된 파일을 구하고, 그 파일들이 속한
top-level 폴더 집합을 돌려준다. 노드는 레포 루트의 ``<folder>/main.py`` 레이아웃을 가정한다.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitDiffError(Exception):
    """git diff 실행/해석 실패."""


def is_unresolved_base(base: str | None) -> bool:
    """base SHA 가 비었거나 all-zero(최초 push의 github.event.before)면 True.

    이 경우 호출자는 '모든 노드 폴더 등록' 폴백을 택한다(절대 silent skip 아님).
    """
    if not base:
        return True
    b = base.strip()
    return b == "" or (len(b) > 0 and set(b) == {"0"})


def _run_git(repo_root: str, args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", repo_root, *args],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:  # git 미설치
        raise GitDiffError(f"git executable not found: {e}") from e
    if proc.returncode != 0:
        raise GitDiffError(f"git {' '.join(args)} failed (exit {proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def changed_paths(repo_root: str, base: str, head: str) -> list[str]:
    """base..head 사이 변경된 파일 경로 목록 (repo-root 상대)."""
    out = _run_git(repo_root, ["diff", "--name-only", base, head])
    return [line.strip() for line in out.splitlines() if line.strip()]


def top_level_dirs(paths: list[str]) -> list[str]:
    """변경 파일 경로들을 top-level 폴더 집합으로 매핑(중복 제거, 정렬).

    레포 루트 바로 아래 파일(폴더 밖 변경)은 무시한다.
    """
    dirs: set[str] = set()
    for p in paths:
        parts = Path(p).parts
        if len(parts) >= 2:  # 폴더 안의 파일만
            dirs.add(parts[0])
    return sorted(dirs)


def all_node_folders(repo_root: str) -> list[str]:
    """레포 루트 바로 아래에서 ``main.py`` 를 가진 top-level 폴더 이름 목록."""
    root = Path(repo_root)
    if not root.is_dir():
        return []
    return sorted(d.name for d in root.iterdir() if d.is_dir() and (d / "main.py").is_file())
