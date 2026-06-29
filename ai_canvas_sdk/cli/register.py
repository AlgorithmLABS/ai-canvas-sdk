"""``ai-canvas-sdk register``: CI push 경로로 custom node 를 backend 에 등록한다.

흐름 (Flow A push):
  1. client_id/client_secret 로 단기 TTL bearer 토큰 획득 (POST /admin/custom-node-ci/token)
  2. 등록할 top-level 노드 폴더 결정 (단일 target, 또는 --changed git diff)
  3. 폴더마다: main.py 의 NodeSchema.name == 폴더명 검증 → req.txt 파싱 → 등록 요청
     (POST /admin/custom-node-ci/register) → 작업 polling (GET .../tasks/{id})
     → 폴링 중 401 이면 재인증
  4. 모든 폴더 성공 시 exit 0, 하나라도 실패하면 exit 1 (폴더별 결과 리포트)

레포 레이아웃은 ``<folder>/main.py`` + ``<folder>/req.txt`` (req.txt 는 선택).
node identity 는 main.py 의 NodeSchema.name 이며 폴더는 그룹/위치만 제공한다.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ai_canvas_sdk.cli.utils import git_changes

TOKEN_PATH = "/admin/custom-node-ci/token"
REGISTER_PATH = "/admin/custom-node-ci/register"
TASK_PATH = "/admin/custom-node-ci/tasks/{task_id}"

DEFAULT_POLL_INTERVAL = 3.0
DEFAULT_POLL_TIMEOUT = 600.0
_MAX_REAUTH = 3
_HTTP_TIMEOUT = 30.0  # urlopen connect/read 타임아웃(초) — 백엔드 hang 시 폴링 루프와 무관하게 read 중단

TERMINAL_OK = "completed"
TERMINAL_FAIL = {"failed", "deleted"}


class RegisterError(Exception):
    """등록 경로에서 발생하는 복구 불가 오류."""

class RegisterHTTPError(RegisterError):
    """HTTP 에러 상태 코드를 포함하는 등록 오류(예: 401 → 토큰 재발급 재시도)."""

    def __init__(self, message: str, status: int, body: dict):
        super().__init__(message)
        self.status = status
        self.body = body


# --------------------------------------------------------------------------- #
# argparse
# --------------------------------------------------------------------------- #
def setup_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "register",
        help="custom node 를 backend 에 등록 (CI push 경로)",
        description="custom node 폴더(들)을 backend CI 등록 엔드포인트로 등록한다.",
    )
    parser.add_argument("target", nargs="?", help="단일 노드 폴더 경로 (--changed 미사용 시)")
    parser.add_argument("--changed", action="store_true", help="git diff 로 변경된 top-level 노드 폴더만 등록")
    parser.add_argument("--base", help="diff base 커밋 SHA (--changed). 비었거나 all-zero 면 전체 등록")
    parser.add_argument("--head", help="diff head 커밋 SHA (--changed, default HEAD)")
    parser.add_argument("--repo-root", default=".", help="레포 루트 (default: 현재 디렉터리)")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("AI_CANVAS_BASE_URL"),
        help="backend base URL (env AI_CANVAS_BASE_URL)",
    )
    parser.add_argument(
        "--client-id",
        default=os.environ.get("AI_CANVAS_CLIENT_ID"),
        help="SSO client id (env AI_CANVAS_CLIENT_ID)",
    )
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("AI_CANVAS_CLIENT_SECRET"),
        help="SSO client secret (env AI_CANVAS_CLIENT_SECRET)",
    )
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help="폴링 간격(초)")
    parser.add_argument("--poll-timeout", type=float, default=DEFAULT_POLL_TIMEOUT, help="폴링 타임아웃(초)")
    parser.set_defaults(func=run_register)
    return parser


# --------------------------------------------------------------------------- #
# HTTP (stdlib urllib — 런타임 의존성 추가 없음)
# --------------------------------------------------------------------------- #
def _send(req: urllib.request.Request) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:  # noqa: S310 (신뢰된 backend base URL)
            raw = resp.read().decode("utf-8")
            status = getattr(resp, "status", None) or resp.getcode()
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                # 200 인데 바디가 비-JSON(프록시 HTML 에러 페이지/불완전 응답 등) — traceback 대신 보존.
                parsed = {"detail": raw}
            return int(status), parsed
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if hasattr(e, "read") else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        return int(e.code), parsed
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        # 네트워크 오류/타임아웃은 uncaught traceback 으로 새지 않고 RegisterError 로 변환한다
        # (다중노드 집계가 중단되지 않도록).
        raise RegisterError(f"네트워크 오류 ({req.full_url}): {e}") from e


def _post_form(url: str, fields: dict) -> tuple[int, dict]:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return _send(req)


def _post_json(url: str, payload: dict, token: str) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    return _send(req)


def _get(url: str, token: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, method="GET", headers={"Authorization": f"Bearer {token}"})
    return _send(req)


def acquire_token(base_url: str, client_id: str, client_secret: str) -> str:
    status, body = _post_form(
        base_url.rstrip("/") + TOKEN_PATH,
        {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
    )
    token = body.get("access_token")
    if status != 200 or not token:
        raise RegisterError(f"토큰 발급 실패 (HTTP {status}): {body.get('detail', body)}")
    return token


def register_node(base_url: str, token: str, source_code: str, dependencies: list[str]) -> str:
    status, body = _post_json(
        base_url.rstrip("/") + REGISTER_PATH,
        {"source_code": source_code, "dependencies": dependencies},
        token,
    )
    if status not in (200, 201):
        raise RegisterHTTPError(f"등록 요청 실패 (HTTP {status}): {body.get('detail', body)}", status, body)
    # backend 가 즉시 FAILED 를 돌려줄 수 있다(예: M-A admin-소스 거부).
    st = str(body.get("status") or "").lower()
    if st in TERMINAL_FAIL:
        raise RegisterError(f"등록 거부: {body.get('errorMessage') or body}")
    task_id = body.get("taskId") or body.get("task_id")
    if not task_id:
        raise RegisterError(f"등록 응답에 taskId 가 없습니다: {body}")
    return task_id


def poll_task(base_url: str, token: str, task_id: str, *, interval: float, timeout: float, reauth) -> str:
    url = base_url.rstrip("/") + TASK_PATH.format(task_id=task_id)
    deadline = time.monotonic() + timeout
    reauth_count = 0
    while True:
        status, body = _get(url, token)
        if status == 401:
            if reauth_count >= _MAX_REAUTH:
                raise RegisterError("상태 조회 인증 반복 실패 (401)")
            reauth_count += 1
            token = reauth()
            continue
        if status != 200:
            raise RegisterError(f"상태 조회 실패 (HTTP {status}): {body.get('detail', body)}")
        st = str(body.get("status") or "").lower()
        if st == TERMINAL_OK:
            return st
        if st in TERMINAL_FAIL:
            raise RegisterError(f"등록 실패 (status={st}): {body.get('errorMessage') or ''}")
        if time.monotonic() >= deadline:
            raise RegisterError(f"등록 타임아웃 ({timeout}s, 마지막 status={st or 'unknown'})")
        time.sleep(interval)


# --------------------------------------------------------------------------- #
# 노드 폴더 처리
# --------------------------------------------------------------------------- #
def parse_requirements(req_path: Path) -> list[str]:
    """req.txt 를 pip 의존성 목록으로 파싱한다. 파일이 없으면 빈 리스트."""
    if not req_path.is_file():
        return []
    deps: list[str] = []
    for raw in req_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # pip 옵션/참조 라인(-r, -e, --hash 등)은 패키지 스펙이 아니므로 건너뛴다.
        if line.startswith("-"):
            continue
        # 인라인 주석 제거 (URL 의 #fragment 보존 위해 ' #' 만)
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        if line:
            deps.append(line)
    return deps


def extract_node_name(main_py: Path) -> str | None:
    """main.py 에서 NodeSchema(name=...) 의 name 리터럴을 **정적(AST)** 으로 추출한다.

    노드 모듈을 exec-load 하지 않으므로 CI 러너에 노드의 third-party 의존성이 설치돼
    있지 않아도 동작한다(미설치가 거짓 실패가 되지 않음). name 이 문자열 리터럴이 아니라
    동적으로 계산되는 경우 ``None`` 을 반환하고, 호출자는 폴더명 검증을 건너뛴 뒤 backend
    (CNE 스키마 추출)에 식별자 검증을 위임한다.
    """
    try:
        tree = ast.parse(main_py.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return None

    # 가장 먼저 발견되는 NodeSchema(...) 호출의 name 문자열 리터럴을 찾는다.
    # NodeSchema 의 첫 positional 필드가 name 이므로 positional / keyword 둘 다 인식한다.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            func_name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else None)
            if func_name == "NodeSchema":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    return node.args[0].value
                for kw in node.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        return kw.value.value
    return None


def register_one_folder(
    folder: Path,
    *,
    base_url: str,
    get_token,
    reauth,
    interval: float,
    timeout: float,
) -> None:
    """단일 노드 폴더를 등록한다. 실패 시 RegisterError 를 던진다."""
    main_py = folder / "main.py"
    if not main_py.is_file():
        raise RegisterError(f"main.py 가 없습니다: {folder}")

    node_name = extract_node_name(main_py)
    if node_name is None:
        # name 을 정적으로 확정할 수 없음(동적 계산 등) — 폴더명 검증을 건너뛰고 backend(CNE
        # 스키마 추출)에 식별자 검증을 위임한다. 거짓 실패를 만들지 않는다.
        print(f"[WARN] {folder.name}: NodeSchema.name 을 정적으로 확정할 수 없어 폴더명 검증을 건너뜁니다(backend 가 검증).")
    elif folder.name != node_name:
        raise RegisterError(
            f"폴더명('{folder.name}')과 NodeSchema.name('{node_name}')이 일치하지 않습니다. "
            f"폴더명을 노드 이름과 동일하게 맞추세요."
        )

    dependencies = parse_requirements(folder / "req.txt")
    source_code = main_py.read_text(encoding="utf-8")

    try:
        task_id = register_node(base_url, get_token(), source_code, dependencies)
    except RegisterHTTPError as e:
        if e.status != 401:
            raise
        # 앞선 노드의 긴 폴링 동안 단기 TTL 토큰이 만료된 경우 → 재발급 후 1회 재시도.
        print("[INFO] 등록 요청 중 401 — 토큰 재발급 후 재시도합니다.")
        task_id = register_node(base_url, reauth(), source_code, dependencies)
    poll_task(base_url, get_token(), task_id, interval=interval, timeout=timeout, reauth=reauth)


def _resolve_folders(args: argparse.Namespace) -> list[Path]:
    repo_root = args.repo_root
    if args.changed:
        if git_changes.is_unresolved_base(args.base):
            print("[INFO] base SHA 미해석(최초 push 등) — 모든 top-level 노드 폴더를 등록합니다.")
            return [Path(repo_root) / name for name in git_changes.all_node_folders(repo_root)]
        try:
            paths = git_changes.changed_paths(repo_root, args.base, args.head or "HEAD")
        except git_changes.GitDiffError as e:
            # 절대 silent 하게 넘어가지 않는다 — loud 하게 실패시킨다.
            raise RegisterError(f"git diff 실패 — 변경 폴더를 확정할 수 없습니다: {e}") from e
        changed_dirs = git_changes.top_level_dirs(paths)
        node_folders = set(git_changes.all_node_folders(repo_root))
        resolved: list[Path] = []
        for d in changed_dirs:
            if d in node_folders:
                resolved.append(Path(repo_root) / d)
            else:
                # 삭제된 폴더(작업트리에 main.py 없음) 또는 노드 폴더 아님 → 로그 후 skip (자동 해제 안 함)
                print(f"[INFO] 건너뜀(노드 폴더 아님/삭제됨, main.py 없음): {d}")
        return resolved
    # 단일 폴더 모드
    if not args.target:
        raise RegisterError("등록할 폴더를 지정하거나 --changed 를 사용하세요.")
    return [Path(args.target)]


def run_register(args: argparse.Namespace) -> int:
    base_url, client_id, client_secret = args.base_url, args.client_id, args.client_secret
    missing = [
        name
        for name, value in (
            ("--base-url/AI_CANVAS_BASE_URL", base_url),
            ("--client-id/AI_CANVAS_CLIENT_ID", client_id),
            ("--client-secret/AI_CANVAS_CLIENT_SECRET", client_secret),
        )
        if not value
    ]
    if missing:
        print(f"[ERROR] 필수 값 누락: {', '.join(missing)}", file=sys.stderr)
        return 2

    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        print("[ERROR] --base-url 은 http:// 또는 https:// 로 시작해야 합니다.", file=sys.stderr)
        return 2

    token_box: dict[str, str | None] = {"value": None}

    def get_token() -> str:
        if token_box["value"] is None:
            token_box["value"] = acquire_token(base_url, client_id, client_secret)
        return token_box["value"]

    def reauth() -> str:
        token_box["value"] = acquire_token(base_url, client_id, client_secret)
        return token_box["value"]

    try:
        folders = _resolve_folders(args)
    except RegisterError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    if not folders:
        print("[INFO] 등록할 변경된 노드 폴더가 없습니다.")
        return 0


    results: list[tuple[str, bool, str]] = []
    for folder in folders:
        label = folder.name or str(folder)
        try:
            register_one_folder(
                folder,
                base_url=base_url,
                get_token=get_token,
                reauth=reauth,
                interval=args.poll_interval,
                timeout=args.poll_timeout,
            )
            results.append((label, True, "completed"))
            print(f"[OK] {label}")
        except RegisterError as e:
            results.append((label, False, str(e)))
            print(f"[FAIL] {label}: {e}", file=sys.stderr)

    failed = [r for r in results if not r[1]]
    if failed:
        print(f"\n[ERROR] {len(failed)}/{len(results)} 노드 폴더 등록 실패:", file=sys.stderr)
        for name, _, msg in failed:
            print(f"  - {name}: {msg}", file=sys.stderr)
        return 1

    print(f"\n[OK] {len(results)}개 노드 폴더 모두 등록 완료.")
    return 0
