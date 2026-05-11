# Versioning

ai-canvas-sdk 는 **태그 기반 버전 관리** + **`setuptools-scm`** 으로 운영합니다. pyproject.toml 에는 static version 이 없으며, 빌드 시점의 `git describe` 결과가 곧 패키지 버전입니다.

## 핵심 원칙

1. **버전의 source of truth = git tag**. pyproject.toml/`__init__.py` 에 static version 이 없음.
2. **dev 빌드 = 브랜치 ref 직접 소비**. devN incrementing 자동 태그는 폐기 (`dev-tag.yml` 삭제). 다만 매 stable 릴리즈마다 다음 minor 의 `vX.Y+1.0.dev0` lightweight tag 하나만 dev HEAD 에 anchor 로 생성됨 (setuptools-scm 표시 정합성용). 소비자 (back / dag / cne 등) 는 변함없이 `git+https://...@dev` ref 로 source clone.
3. **main 머지 + 수동 tag = 정식 릴리즈**. `vX.Y.Z` 태그가 release.yml 을 trigger 해서 GitHub Release 생성.

## 브랜치와 태그 형태

| 브랜치 | 태그 | 소비 방식 | 예시 |
|---|---|---|---|
| `dev`  | `vX.Y+1.0.dev0` (anchor 전용) | `git+https://...@dev` 브랜치 ref clone. 매 stable 릴리즈마다 다음 minor 의 `.dev0` 한 개를 anchor 로 생성 — setuptools-scm 가 그 위에서 `.dev{distance}` 합성 | `v0.2.0.dev0` |
| `main` | `vX.Y.Z`    | annotated tag, GitHub Release | `v0.1.2` |

`X.Y.Z` 는 SemVer:
- `MAJOR` — 공개 API (`CustomNode`, `NodeSchema`, `Parameter` 등) 호환 깨짐
- `MINOR` — 하위 호환 기능 추가
- `PATCH` — 버그 수정, 내부 리팩터, 문서·CI

## dev 빌드

dev 브랜치는 정식 릴리즈마다 **다음 minor 의 `.dev0` lightweight tag** (예: `v0.1.2` 릴리즈 → `v0.2.0.dev0`) 가 그 시점의 dev HEAD 에 생성됩니다. `release.yml` 의 release job 이 stable tag push 직후 자동 수행 (해당 사이클의 `.dev0` 이 이미 있으면 skip — 멱등).

목적은 다운스트림 dev 빌드 시 `setuptools-scm` 의 anchor 가 옛 stable tag 로 떨어지는 문제 해소. stable tag (`vX.Y.Z`) 는 main 위에만 있어 dev 의 ancestor 가 아니라, `git describe` 가 한참 옛 태그까지 거슬러 올라갑니다. `.dev0` anchor 가 dev ancestor 로 존재하면 `guess-next-dev` 의 `_bump_dev` 가 `.dev0` 을 strip 한 뒤 `.dev{distance}` 만 다시 붙여 `0.2.0.dev3+g<sha>` 같은 깨끗한 PEP 440 dev version 이 나옵니다.

**`.devN` (N>=1) 은 생성하지 않습니다** — `_bump_dev` 가 N>=1 을 ValueError 로 거부하기 때문이고, 옛 `dev-tag.yml` (incrementing devN) 자동화가 실패하던 사유가 정확히 이것입니다.

dev wheel 의 metadata version 은 여전히 기능적 의미는 없습니다 — 다운스트림은 모두 `git+https://...@dev` 브랜치 ref clone 으로 가져갑니다. anchor 의 역할은 빌드 로그·Slack 표시상의 사람 가독성입니다.

옛 incrementing devN 자동화 (`dev-tag.yml`, `vX.Y.Z.devN`) 폐기 사유:
- 다운스트림 누구도 `@vX.Y.Z.devN` 으로 핀하지 않음 — 모두 branch ref 사용 (org grep 0건)
- 매 push 마다 setuptools-scm / setuptools deprecation warning 노이즈
- 옛 dev 태그가 newer commit 의 의존성 변경을 반영 못 해 build 실패 사례 (PR #28 numpy 핀 완화 commit 에 dev tag 안 붙어 옛 `v0.1.2.dev0` 으로 resolve → dag-backend numpy 충돌)
- `_bump_dev` 가 N>=1 거부 — 즉 setuptools-scm 의 의도된 사용 패턴은 dev0 한 개뿐

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

- **빌드 시**: `git describe` → `vX.Y.Z` 에서 leading `v` 제거하고 PEP 440 버전으로 사용
- **stable 태그 위 (main, exact tag)**: `0.1.2` 와 같이 그대로 사용
- **`.dev0` anchor 위 N commits 뒤 (dev)**: `guess-next-dev` 가 `.dev0` 을 `_bump_dev` 로 strip 후 `.dev{distance}` 재포맷 → `0.2.0.dev3+g<sha>` 같은 깨끗한 dev version. `.dev0` anchor 가 매 stable 릴리즈마다 다음 minor 로 갱신되므로 anchor 가 옛 stable 까지 거슬러 올라가지 않음
- **`_version.py`**: `ai_canvas_sdk/_version.py` 가 빌드 시 자동 생성 (gitignored). `__init__.py` 가 이걸 읽어 `__version__` 노출
- **`fallback_version`**: git history 가 없는 환경에선 `0.0.0+unknown`

## DAG / back / cne 측 핀 형태

```toml
# prod 환경 (정식 릴리즈)
"ai-canvas-sdk @ git+https://github.com/.../ai-canvas-sdk.git@main"
# 또는 specific tag pin
"ai-canvas-sdk @ git+https://github.com/.../ai-canvas-sdk.git@v0.1.2"

# dev 환경 (dev 브랜치 HEAD)
"ai-canvas-sdk @ git+https://github.com/.../ai-canvas-sdk.git@dev"
```
