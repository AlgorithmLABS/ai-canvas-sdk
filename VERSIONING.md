# Versioning

ai-canvas-sdk 는 **태그 기반 버전 관리** + **`setuptools-scm`** 으로 운영합니다. pyproject.toml 에는 static version 이 없으며, 빌드 시점의 `git describe` 결과가 곧 패키지 버전입니다.

## 핵심 원칙

1. **버전의 source of truth = git tag**. pyproject.toml/`__init__.py` 에 static version 이 없음.
2. **dev 빌드 = 브랜치 ref 직접 소비**. dev 자동 태그는 폐기 — 소비자 (back / dag / custom-node-executor) 는 `git+https://...@dev` ref 로 source clone 해서 install.
3. **main 머지 + 수동 tag = 정식 릴리즈**. `vX.Y.Z` 태그가 release.yml 을 trigger 해서 GitHub Release 생성.

## 브랜치와 태그 형태

| 브랜치 | 태그 | 소비 방식 | 예시 |
|---|---|---|---|
| `dev`  | (태그 없음) | `git+https://...@dev` 브랜치 ref clone | dev gke / 로컬 dev |
| `main` | `vX.Y.Z`    | annotated tag, GitHub Release | `v0.1.2` |

`X.Y.Z` 는 SemVer:
- `MAJOR` — 공개 API (`CustomNode`, `NodeSchema`, `Parameter` 등) 호환 깨짐
- `MINOR` — 하위 호환 기능 추가
- `PATCH` — 버그 수정, 내부 리팩터, 문서·CI

## dev 빌드

dev 브랜치는 정식 릴리즈 태그 없이 운영합니다. setuptools-scm 가 빌드 시 가장 가까운 stable 태그(또는 `fallback_version = '0.0.0+unknown'`)를 사용하므로 dev wheel 의 버전 문자열은 정확하지 않을 수 있으나, 소비자 (ai-canvas-back / ai-canvas-dag / ai-canvas-custom-node-executor) 는 `git+https://github.com/AlgorithmLABS/ai-canvas-sdk.git@dev` 브랜치 ref 로 source clone 해서 install 하므로 wheel metadata version 은 의미가 없습니다.

dev 태그 자동 생성 (`dev-tag.yml`, `vX.Y.Z.devN`) 은 다음 이유로 폐기됨:
- 다운스트림 누구도 `@vX.Y.Z.devN` 으로 핀하지 않음 — 모두 branch ref 사용 (org grep 0건)
- 매 push 마다 setuptools-scm / setuptools deprecation warning 노이즈
- 옛 dev 태그가 newer commit 의 의존성 변경을 반영 못 해 build 실패 사례 (PR #28 numpy 핀 완화 commit 에 dev tag 안 붙어 옛 `v0.1.2.dev0` 으로 resolve → dag-backend numpy 충돌)

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

- **빌드 시**: `git describe` → `vX.Y.Z` 에서 leading `v` 제거하고 PEP 440 버전으로 사용. stable tag 위가 아니면 `vX.Y.Z.dev{distance}` 형태 합성
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
