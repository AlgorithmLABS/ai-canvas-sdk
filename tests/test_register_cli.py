"""G002 — ai-canvas-sdk register CLI 테스트.

검증: req.txt 파싱, 변경-폴더 git diff 탐지(+edge), git-diff 오류 loud 실패,
폴더명==NodeSchema.name 검증, 토큰 획득, 등록 요청 shape, 폴링(종결/실패/타임아웃),
401 재인증, 다중노드 부분실패 exit code, 필수값 누락 exit code.

HTTP 는 urllib.request.urlopen 을 가짜로 교체해 검증한다(실 backend 불필요).
git diff 는 임시 실제 git 레포로 검증한다(git 필요; 없으면 skip).
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import urllib.error
from pathlib import Path

import pytest

from ai_canvas_sdk.cli import register as reg
from ai_canvas_sdk.cli.utils import git_changes


# --------------------------------------------------------------------------- #
# Fake HTTP
# --------------------------------------------------------------------------- #
class _FakeResp:
    def __init__(self, status: int, body: dict):
        self.status = status
        self._raw = json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def getcode(self) -> int:
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeHttp:
    """urllib.request.urlopen 대체. URL suffix 별 응답 큐/단건을 라우팅하고 요청을 기록한다."""

    def __init__(self):
        self.routes: dict[str, list] = {}
        self.requests: list = []

    def add(self, path_suffix: str, status: int, body: dict, *, times: int = 1):
        self.routes.setdefault(path_suffix, [])
        for _ in range(times):
            self.routes[path_suffix].append((status, body))

    def __call__(self, req, *args, **kwargs):
        self.requests.append(req)
        url = req.full_url if hasattr(req, "full_url") else str(req)
        for suffix, queue in self.routes.items():
            if url.endswith(suffix) or suffix in url:
                if not queue:
                    raise AssertionError(f"no more fake responses for {suffix}")
                status, body = queue.pop(0)
                if status == 401 or status >= 400:
                    err = urllib.error.HTTPError(url, status, "err", {}, io.BytesIO(json.dumps(body).encode()))
                    raise err
                return _FakeResp(status, body)
        raise AssertionError(f"unexpected URL: {url}")


@pytest.fixture
def fake_http(monkeypatch):
    f = FakeHttp()
    monkeypatch.setattr("urllib.request.urlopen", f)
    return f


# --------------------------------------------------------------------------- #
# Node fixture helper (uses real custom_node; no pandas)
# --------------------------------------------------------------------------- #
def _write_node(folder: Path, schema_name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "main.py").write_text(
        "from ai_canvas_sdk.custom_node import CustomNode, NodeSchema, NodeData\n"
        "class MyNode(CustomNode):\n"
        "    def get_schema(self):\n"
        f"        return NodeSchema(name={schema_name!r}, data=NodeData(input_ports=[], output_ports=[], params=[]))\n"
        "    def run(self, inputs, parameters, ctx):\n"
        "        return {}\n",
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- #
# parse_requirements
# --------------------------------------------------------------------------- #
def test_parse_req_txt_present(tmp_path):
    req = tmp_path / "req.txt"
    req.write_text(
        "# comment line\n\nnetworkx==3.2\npandas>=2.0  # inline comment\n   \nrequests\n",
        encoding="utf-8",
    )
    assert reg.parse_requirements(req) == ["networkx==3.2", "pandas>=2.0", "requests"]


def test_parse_req_txt_absent(tmp_path):
    assert reg.parse_requirements(tmp_path / "missing.txt") == []


# --------------------------------------------------------------------------- #
# git changed-folder detection
# --------------------------------------------------------------------------- #
def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise AssertionError(f"git {args} failed: {out.stderr}")
    return out.stdout.strip()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_changed_folder_detection(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write_node(repo / "node_a", "node_a")
    _write_node(repo / "node_b", "node_b")
    (repo / "rootfile.txt").write_text("x", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")

    # change node_a, delete node_b, add a root-level file (out-of-folder)
    (repo / "node_a" / "main.py").write_text(
        (repo / "node_a" / "main.py").read_text(encoding="utf-8") + "\n# touched\n", encoding="utf-8"
    )
    shutil.rmtree(repo / "node_b")
    (repo / "rootfile2.txt").write_text("y", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "head")
    head = _git(repo, "rev-parse", "HEAD")

    paths = git_changes.changed_paths(str(repo), base, head)
    dirs = git_changes.top_level_dirs(paths)
    assert "node_a" in dirs and "node_b" in dirs  # both appear in the diff
    # only node_a remains a real node folder; node_b deleted; rootfiles ignored
    assert git_changes.all_node_folders(str(repo)) == ["node_a"]

    args = argparse.Namespace(changed=True, base=base, head=head, repo_root=str(repo), target=None)
    resolved = reg._resolve_folders(args)
    assert [p.name for p in resolved] == ["node_a"]


def test_is_unresolved_base():
    assert git_changes.is_unresolved_base(None)
    assert git_changes.is_unresolved_base("")
    assert git_changes.is_unresolved_base("0" * 40)
    assert not git_changes.is_unresolved_base("abc123")


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_first_push_zero_base_registers_all(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write_node(repo / "node_a", "node_a")
    _write_node(repo / "node_b", "node_b")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    args = argparse.Namespace(changed=True, base="0" * 40, head="HEAD", repo_root=str(repo), target=None)
    resolved = sorted(p.name for p in reg._resolve_folders(args))
    assert resolved == ["node_a", "node_b"]


def test_git_diff_error_fails_loud(tmp_path):
    # non-git directory -> changed_paths raises GitDiffError
    with pytest.raises(git_changes.GitDiffError):
        git_changes.changed_paths(str(tmp_path), "deadbeef", "HEAD")
    # _resolve_folders surfaces it as a loud RegisterError (caller returns non-zero, never silent)
    args = argparse.Namespace(changed=True, base="deadbeef", head="HEAD", repo_root=str(tmp_path), target=None)
    with pytest.raises(reg.RegisterError):
        reg._resolve_folders(args)


# --------------------------------------------------------------------------- #
# folder == NodeSchema.name validation
# --------------------------------------------------------------------------- #
def test_folder_name_matches_schema_name_ok(tmp_path, monkeypatch):
    folder = tmp_path / "good_node"
    _write_node(folder, "good_node")
    monkeypatch.setattr(reg, "register_node", lambda *a, **k: "task-1")
    monkeypatch.setattr(reg, "poll_task", lambda *a, **k: "completed")
    # should not raise
    reg.register_one_folder(folder, base_url="http://x", get_token=lambda: "t", reauth=lambda: "t", interval=0, timeout=1)


def test_folder_name_mismatch_fails(tmp_path, monkeypatch):
    folder = tmp_path / "wrong_folder"
    _write_node(folder, "actual_node_name")
    called = {"n": 0}
    monkeypatch.setattr(reg, "register_node", lambda *a, **k: called.__setitem__("n", called["n"] + 1) or "t")
    with pytest.raises(reg.RegisterError, match="일치하지 않"):
        reg.register_one_folder(folder, base_url="http://x", get_token=lambda: "t", reauth=lambda: "t", interval=0, timeout=1)
    assert called["n"] == 0  # mismatch detected before any register call


# --------------------------------------------------------------------------- #
# HTTP: token / register / poll / reauth
# --------------------------------------------------------------------------- #
def test_cli_login(fake_http):
    fake_http.add(reg.TOKEN_PATH, 200, {"access_token": "tok-123", "token_type": "bearer", "expires_in": 900})
    assert reg.acquire_token("http://api", "cid", "sec") == "tok-123"


def test_cli_login_bad_credentials(fake_http):
    fake_http.add(reg.TOKEN_PATH, 401, {"detail": "Invalid client credentials"})
    with pytest.raises(reg.RegisterError):
        reg.acquire_token("http://api", "cid", "bad")


def test_register_request_shape(fake_http):
    fake_http.add(reg.REGISTER_PATH, 200, {"taskId": "abc", "status": "pending"})
    task_id = reg.register_node("http://api", "tok", "print('x')", ["pandas==2.0"])
    assert task_id == "abc"
    sent = fake_http.requests[-1]
    assert sent.method == "POST"
    assert sent.full_url.endswith(reg.REGISTER_PATH)
    assert sent.headers["Authorization"] == "Bearer tok"
    payload = json.loads(sent.data.decode())
    assert payload == {"source_code": "print('x')", "dependencies": ["pandas==2.0"]}


def test_register_immediate_failed_is_rejected(fake_http):
    # backend M-A refusal returns 200 + status=failed
    fake_http.add(reg.REGISTER_PATH, 200, {"taskId": "abc", "status": "failed", "errorMessage": "admin-managed"})
    with pytest.raises(reg.RegisterError, match="거부"):
        reg.register_node("http://api", "tok", "src", [])


def test_poll_loop_terminal_completed(fake_http):
    suffix = reg.TASK_PATH.format(task_id="abc")
    fake_http.add(suffix, 200, {"status": "pending"})
    fake_http.add(suffix, 200, {"status": "installing"})
    fake_http.add(suffix, 200, {"status": "completed"})
    assert reg.poll_task("http://api", "tok", "abc", interval=0, timeout=5, reauth=lambda: "tok") == "completed"


def test_poll_loop_failed(fake_http):
    suffix = reg.TASK_PATH.format(task_id="abc")
    fake_http.add(suffix, 200, {"status": "failed", "errorMessage": "boom"})
    with pytest.raises(reg.RegisterError, match="실패"):
        reg.poll_task("http://api", "tok", "abc", interval=0, timeout=5, reauth=lambda: "tok")


def test_poll_loop_timeout(fake_http):
    suffix = reg.TASK_PATH.format(task_id="abc")
    fake_http.add(suffix, 200, {"status": "pending"}, times=5)
    with pytest.raises(reg.RegisterError, match="타임아웃"):
        reg.poll_task("http://api", "tok", "abc", interval=0, timeout=0, reauth=lambda: "tok")


def test_reauth_on_401(fake_http):
    suffix = reg.TASK_PATH.format(task_id="abc")
    fake_http.add(suffix, 401, {"detail": "expired"})
    fake_http.add(suffix, 200, {"status": "completed"})
    calls = {"n": 0}

    def reauth():
        calls["n"] += 1
        return "fresh-token"

    assert reg.poll_task("http://api", "tok", "abc", interval=0, timeout=5, reauth=reauth) == "completed"
    assert calls["n"] == 1


# --------------------------------------------------------------------------- #
# run_register orchestration: exit codes + multi-node aggregation
# --------------------------------------------------------------------------- #
def _base_args(**over):
    defaults = dict(
        target=None,
        changed=False,
        base=None,
        head=None,
        repo_root=".",
        base_url="http://api",
        client_id="cid",
        client_secret="sec",
        poll_interval=0.0,
        poll_timeout=5.0,
    )
    defaults.update(over)
    return argparse.Namespace(**defaults)


def test_exit_code_missing_credentials():
    args = _base_args(base_url=None)
    assert reg.run_register(args) == 2


def test_exit_code_all_success(tmp_path, monkeypatch):
    _write_node(tmp_path / "node_a", "node_a")
    monkeypatch.setattr(reg, "register_one_folder", lambda *a, **k: None)
    args = _base_args(target=str(tmp_path / "node_a"))
    assert reg.run_register(args) == 0


def test_multinode_partial_failure_exit_code(tmp_path, monkeypatch):
    _write_node(tmp_path / "node_a", "node_a")
    _write_node(tmp_path / "node_b", "node_b")
    attempted: list[str] = []

    def fake_register_one(folder, **kwargs):
        attempted.append(folder.name)
        if folder.name == "node_b":
            raise reg.RegisterError("node_b failed")

    monkeypatch.setattr(reg, "register_one_folder", fake_register_one)
    # --changed with zero base -> all folders (node_a, node_b)
    args = _base_args(changed=True, base="0" * 40, repo_root=str(tmp_path))
    rc = reg.run_register(args)
    assert rc == 1  # one folder failed
    assert sorted(attempted) == ["node_a", "node_b"]  # all attempted, not fail-fast

# --------------------------------------------------------------------------- #
# G002 fix coverage: AST name extraction (no exec), reauth cap, network errors,
# requirements option lines
# --------------------------------------------------------------------------- #
def test_extract_node_name_static_literal(tmp_path):
    folder = tmp_path / "lit_node"
    _write_node(folder, "lit_node")
    assert reg.extract_node_name(folder / "main.py") == "lit_node"


def test_extract_node_name_dynamic_returns_none(tmp_path):
    folder = tmp_path / "dyn_node"
    folder.mkdir()
    (folder / "main.py").write_text(
        "from ai_canvas_sdk.custom_node import CustomNode, NodeSchema, NodeData\n"
        "NAME = 'x' + '_node'\n"
        "class MyNode(CustomNode):\n"
        "    def get_schema(self):\n"
        "        return NodeSchema(name=NAME, data=NodeData(input_ports=[], output_ports=[], params=[]))\n"
        "    def run(self, inputs, parameters, ctx):\n"
        "        return {}\n",
        encoding="utf-8",
    )
    assert reg.extract_node_name(folder / "main.py") is None


def test_dynamic_name_skips_validation_and_proceeds(tmp_path, monkeypatch):
    folder = tmp_path / "dyn_node"
    folder.mkdir()
    (folder / "main.py").write_text(
        "from ai_canvas_sdk.custom_node import CustomNode, NodeSchema, NodeData\n"
        "class MyNode(CustomNode):\n"
        "    def get_schema(self):\n"
        "        return NodeSchema(name=type(self).__name__, data=NodeData(input_ports=[], output_ports=[], params=[]))\n"
        "    def run(self, inputs, parameters, ctx):\n"
        "        return {}\n",
        encoding="utf-8",
    )
    called = {"register": 0}
    monkeypatch.setattr(reg, "register_node", lambda *a, **k: called.__setitem__("register", 1) or "t")
    monkeypatch.setattr(reg, "poll_task", lambda *a, **k: "completed")
    # name 정적 확정 불가 → 검증 생략하고 등록 진행 (거짓 실패 없음)
    reg.register_one_folder(folder, base_url="http://x", get_token=lambda: "t", reauth=lambda: "t", interval=0, timeout=1)
    assert called["register"] == 1


def test_does_not_exec_node_with_missing_deps(tmp_path):
    """노드가 미설치 third-party 모듈을 import 해도 AST 추출은 동작한다(거짓 실패 방지)."""
    folder = tmp_path / "heavy_node"
    folder.mkdir()
    (folder / "main.py").write_text(
        "import definitely_not_installed_pkg_xyz  # noqa\n"
        "from ai_canvas_sdk.custom_node import CustomNode, NodeSchema, NodeData\n"
        "class MyNode(CustomNode):\n"
        "    def get_schema(self):\n"
        "        return NodeSchema(name='heavy_node', data=NodeData(input_ports=[], output_ports=[], params=[]))\n"
        "    def run(self, inputs, parameters, ctx):\n"
        "        return {}\n",
        encoding="utf-8",
    )
    # exec 했다면 ModuleNotFoundError 가 났을 것. AST 라서 이름을 정상 추출한다.
    assert reg.extract_node_name(folder / "main.py") == "heavy_node"


def test_parse_req_txt_skips_pip_option_lines(tmp_path):
    req = tmp_path / "req.txt"
    req.write_text("-r base.txt\n-e .\n--hash=sha256:abc\nnumpy==2.0\n", encoding="utf-8")
    assert reg.parse_requirements(req) == ["numpy==2.0"]


def test_poll_reauth_cap_exhausted(fake_http):
    suffix = reg.TASK_PATH.format(task_id="abc")
    fake_http.add(suffix, 401, {"detail": "expired"}, times=reg._MAX_REAUTH + 2)
    with pytest.raises(reg.RegisterError, match="인증"):
        reg.poll_task("http://api", "tok", "abc", interval=0, timeout=5, reauth=lambda: "fresh")


def test_network_error_becomes_register_error(monkeypatch):
    import urllib.error

    def boom(*a, **k):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(reg.RegisterError, match="네트워크"):
        reg.acquire_token("http://api", "cid", "sec")


def test_extract_node_name_positional(tmp_path):
    folder = tmp_path / "pos_node"
    folder.mkdir()
    (folder / "main.py").write_text(
        "from ai_canvas_sdk.custom_node import CustomNode, NodeSchema, NodeData\n"
        "class MyNode(CustomNode):\n"
        "    def get_schema(self):\n"
        "        return NodeSchema('pos_node', NodeData(input_ports=[], output_ports=[], params=[]))\n"
        "    def run(self, inputs, parameters, ctx):\n"
        "        return {}\n",
        encoding="utf-8",
    )
    assert reg.extract_node_name(folder / "main.py") == "pos_node"
