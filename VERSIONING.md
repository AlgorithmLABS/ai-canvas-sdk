# Versioning

ai-canvas-sdk 는 **태그 기반 버전 관리** + **`setuptools-scm`** 으로 운영합니다. pyproject.toml 에는 static version 이 없으며, 빌드 시점의 `git describe` 결과가 곧 패키지 버전입니다.

## 핵심 원칙

1. **버전의 source of truth = git tag**. pyproject.toml/`__init__.py` 에 static version 이 없음.
2. **dev 머지 = 자동 dev 태그**. push 마다 `vX.Y.Z.devN` lightweight tag 가 자동 생성됨.
3. **main 머지 + 수동 tag = 정식 릴리즈**. `vX.Y.Z` 태그가 release.yml 을 trigger 해서 GitHub Release 생성.

## 브랜치와 태그 형태

| 브랜치 | 태그 | 의미 | 예시 |
|---|---|---|---|
| `dev`  | `vX.Y.Z.devN` | dev 스냅샷, dev-tag.yml 자동 생성, lightweight tag | `v0.1.2.dev3` |
| `main` | `vX.Y.Z`      | 정식 릴리즈, 수동 태그, GitHub Release 생성 | `v0.1.2` |

`X.Y.Z` 는 SemVer:
- `MAJOR` — 공개 API (`CustomNode`, `NodeSchema`, `Parameter` 등) 호환 깨짐
- `MINOR` — 하위 호환 기능 추가
- `PATCH` — 버그 수정, 내부 리팩터, 문서·CI

## Bootstrap 권장

이 레포는 기존 태그가 없으므로 dev-tag.yml 의 base = `0.0.1` 로 시작 → 첫 dev tag 가 `v0.0.1.dev0` 이 됨. pyproject 가 가리키던 `0.1.1` 과의 연속성을 원하면 main HEAD 에 수동 seed:

```bash
git checkout main && git pull
git tag -a v0.1.1 -m "Bootstrap release after setuptools-scm migration"
git push origin v0.1.1
# → release.yml trigger
# 그 다음 dev push 부터는 v0.1.2.dev0 부터 시작
```

## dev 채널 — 자동화

`dev` 에 push 가 일어나면 `.github/workflows/dev-tag.yml` 이 자동으로:

1. 다음 dev 태그 계산
2. `v{base}.dev{N}` 태그 생성 + push

**개발자가 손댈 것 없음.** PR 머지 → 30 초 후 새 dev 태그.

## main 정식 릴리즈 절차

```bash
# 1) dev 에서 release 브랜치 cut
git checkout dev && git pull
git checkout -b release/0.1.2

# 2) (옵션) CHANGELOG.md 갱신 후 commit
git push -u origin release/0.1.2

# 3) PR: release/0.1.2 → main, 머지

# 4) main HEAD 에 정식 태그
git checkout main && git pull
git tag -a v0.1.2 -m "Release 0.1.2"
git push origin v0.1.2
# → release.yml: setuptools-scm 으로 wheel 빌드 + GitHub Release
```

## setuptools-scm 동작

- **빌드 시**: `git describe` → `vX.Y.Z.devN` 또는 `vX.Y.Z` 에서 leading `v` 제거하고 PEP 440 버전으로 사용
- **`_version.py`**: `ai_canvas_sdk/_version.py` 가 빌드 시 자동 생성 (gitignored). `__init__.py` 가 이걸 읽어 `__version__` 노출
- **`fallback_version`**: git history 가 없는 환경에선 `0.0.0+unknown`

## DAG 측 핀 형태 (cutover 후)

DAG `pyproject.toml` 의 `[project.optional-dependencies] custom-nodes` 에:

```toml
"ai-canvas-sdk @ git+https://github.com/.../ai-canvas-sdk.git@v0.1.2"
```
