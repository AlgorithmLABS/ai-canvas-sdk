# Custom Node CI 등록 가이드 (GitHub Actions / GitLab CI)

AI Canvas 커스텀 노드를 **Git 레포에 push/merge 하면 CI가 자동으로 backend 에 등록**하는
Flow A(push 모델) 설정 가이드입니다.

## 동작 개요

```
push / merge → 연결된 레포의 기본 브랜치(예: main)
  └─ CI 잡 실행 (러너가 자기 권한으로 레포 checkout)
       └─ pip install ai-canvas-sdk
            └─ ai-canvas-sdk register --changed --base <before> --head <sha>
                 ├─ POST {BASE_URL}/admin/custom-node-ci/token      (client_id/secret → 단기 토큰)
                 ├─ POST {BASE_URL}/admin/custom-node-ci/register   (노드 source_code + deps)
                 └─ GET  {BASE_URL}/admin/custom-node-ci/tasks/{id} (완료까지 폴링)
```

- **backend 는 GitLab/GitHub 에 접속하지 않습니다(인바운드 없음).** 레포 읽기는 CI 러너가
  자신의 native 권한으로 수행하고, SDK 가 노드 소스를 읽어 backend API 로 **push** 합니다.
  → private 레포여도 되고, backend 쪽에 git 자격증명(SA/PAT/deploy key)이 필요 없습니다.
- 인증은 git 자격증명이 아니라 **AI Canvas OAuth client_id/secret**(CI 시크릿에 저장)으로 합니다.

## 1. 사전 준비 (admin)

1. AI Canvas admin → **"Custom Node CI 연결"** 페이지에서 연결을 생성합니다
   (provider, repo_url, `backend_base_url`, default_branch).
2. 생성 직후 **1회성**으로 노출되는 `client_id` / `client_secret` 을 복사합니다
   (이후 조회 응답에는 secret 이 포함되지 않습니다).
3. `backend_base_url` 은 SDK 가 호출할 **API 루트 origin** 입니다
   (예: 운영 `https://api.ai-canvas.io`). 자세한 제약은 아래 [base_url](#7-인증--base_url) 참고.

## 2. 레포 노드 레이아웃

top-level 폴더 1개 = 노드 1개:

```
<node-name>/
  main.py     # NodeSchema(name="<node-name>") — 폴더명과 반드시 일치
  req.txt     # (선택) pip 의존성 목록. 없으면 무의존성으로 처리.
```

- **폴더명 == `NodeSchema.name`** 이어야 합니다. CLI 가 `main.py` 를 **정적(AST) 분석**으로
  이름을 추출해 검증하며, 불일치 시 해당 노드는 실패합니다.
- 노드 식별자는 `NodeSchema.name` 입니다. 같은 이름의 재등록은 **버전 업서트**로 동작합니다.

## 3. `register` 명령

| 옵션 | 설명 |
|---|---|
| `<target>` (위치 인자) | 단일 노드 폴더 경로 (`--changed` 미사용 시) |
| `--changed` | git diff 로 변경된 top-level 노드 폴더만 등록 |
| `--base <sha>` | diff base 커밋 SHA. 비었거나 all-zero 면 전체 등록 |
| `--head <sha>` | diff head 커밋 SHA (기본 `HEAD`) |
| `--repo-root <dir>` | 레포 루트 (기본 `.`) |
| `--base-url <url>` | backend base URL (env `AI_CANVAS_BASE_URL`) |
| `--client-id <id>` | OAuth client id (env `AI_CANVAS_CLIENT_ID`) |
| `--client-secret <secret>` | OAuth client secret (env `AI_CANVAS_CLIENT_SECRET`) |
| `--poll-interval <sec>` | 상태 폴링 간격(기본 3초) |
| `--poll-timeout <sec>` | 상태 폴링 타임아웃(기본 600초) |

CI 에서는 보통 환경변수(`AI_CANVAS_BASE_URL` / `AI_CANVAS_CLIENT_ID` / `AI_CANVAS_CLIENT_SECRET`)로 넘깁니다.

## 4. GitHub Actions

### 4-1. 시크릿 등록
레포 **Settings → Secrets and variables → Actions → New repository secret**:
- `AI_CANVAS_CLIENT_ID`
- `AI_CANVAS_CLIENT_SECRET`

### 4-2. 워크플로 파일
`.github/workflows/register-custom-nodes.yml` (전체 템플릿: [`docs/ci/github-actions.yml`](./github-actions.yml)):

```yaml
name: Register custom nodes
on:
  push:
    branches: [main]
jobs:
  register:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # diff base 해석을 위해 전체 히스토리 필요
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install ai-canvas-sdk
        run: pip install "ai-canvas-sdk @ git+https://github.com/algorithmlabs/ai-canvas-sdk@main"
      - name: Register changed custom nodes
        env:
          AI_CANVAS_BASE_URL: "https://<your-ai-canvas-backend>"
          AI_CANVAS_CLIENT_ID: ${{ secrets.AI_CANVAS_CLIENT_ID }}
          AI_CANVAS_CLIENT_SECRET: ${{ secrets.AI_CANVAS_CLIENT_SECRET }}
        run: ai-canvas-sdk register --changed --base "${{ github.event.before }}" --head "${{ github.sha }}" --repo-root .
```

## 5. GitLab CI

### 5-1. 변수 등록
프로젝트 **Settings → CI/CD → Variables** (둘 다 **Masked** 권장):
- `AI_CANVAS_CLIENT_ID`
- `AI_CANVAS_CLIENT_SECRET`

### 5-2. `.gitlab-ci.yml`
(전체 템플릿: [`docs/ci/.gitlab-ci.yml`](./.gitlab-ci.yml)):

```yaml
register_custom_nodes:
  stage: deploy
  image: python:3.11
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
  variables:
    GIT_DEPTH: "0"
    AI_CANVAS_BASE_URL: "https://<your-ai-canvas-backend>"
  script:
    - pip install "ai-canvas-sdk @ git+https://github.com/algorithmlabs/ai-canvas-sdk@main"
    - ai-canvas-sdk register --changed --base "$CI_COMMIT_BEFORE_SHA" --head "$CI_COMMIT_SHA" --repo-root .
```

## 6. 트리거 동작 & 엣지 케이스

- **변경 감지**: `git diff <base>..<head>` 로 바뀐 top-level 폴더만 등록(전체 재등록 X).
- **최초 push / base 가 all-zero / base 해석 불가**: 모든 노드 폴더를 등록(업서트라 안전).
  - GitHub: 최초 push 시 `github.event.before` 가 `0000...`.
  - GitLab: 신규 브랜치/최초 파이프라인에서 `CI_COMMIT_BEFORE_SHA` 가 all-zero 일 수 있음.
- **삭제된 폴더**: 로그만 남기고 **자동 해제하지 않습니다**(git revert/rename 사고로 노드가
  대량 삭제되는 것을 막는 v1 안전장치). 노드 제거는 admin 에서 **별도로** 수행하세요.
- **git diff 오류**: 조용히 넘어가지 않고 **명시적으로 실패**합니다(silent exit 0 금지).
- **멀티노드**: 전부 시도한 뒤 집계합니다. 하나라도 실패하면 어떤 노드가 왜 실패했는지 출력하고
  `exit 1`, **전부 성공해야 `exit 0`**.
- **PR 을 "여는" 것만으로는 트리거되지 않습니다.** push/merge(기본 브랜치로의 push)에서만 실행됩니다.

## 7. 인증 & base_url

- 토큰은 **단기 TTL**(기본 15분)입니다. 멀티노드 폴링이 길어져 만료되면 CLI 가 **자동 재발급(401 재시도)** 합니다.
- `AI_CANVAS_BASE_URL` 은 반드시 `http://` 또는 `https://` 로 시작해야 합니다(아니면 조기 종료).
- **CI 러너에서 네트워크로 닿는 주소**여야 합니다. GitHub/GitLab 호스티드 러너는 인터넷에 있으므로
  **공개적으로 접근 가능한 URL**(예: `https://api.ai-canvas.io`)이 필요합니다.
  `localhost`/사내 전용 주소는 **self-hosted 러너**에서만 동작합니다.

## 8. Machine vs Admin (M-A)

- CI 로 등록된 노드는 `source=ci` 로 태깅됩니다.
- **CI 등록은 admin 이 직접 업로드한 노드(`source=admin`)를 덮어쓰지 않습니다(거부).**
  admin 수동 경로는 모든 노드를 덮어쓸 수 있습니다.

## 9. SDK 설치 버전 고정

예시는 `@main` 을 사용하지만, **운영에서는 릴리스 태그로 고정**하는 것을 권장합니다(재현성):

```
pip install "ai-canvas-sdk @ git+https://github.com/algorithmlabs/ai-canvas-sdk@vX.Y.Z"
```

## 10. 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `ai-canvas-sdk: error: argument command: invalid choice: 'register'` | 설치된 SDK 가 `register` 미지원 버전 → `register` 포함 버전/태그로 설치 |
| `HTTP 401` (재시도 후에도) | client_id/secret 또는 토큰 문제 → CI 시크릿 값 확인 |
| `HTTP 403` | scope 불일치 → 연결의 scope/권한 확인 |
| `HTTP 503 (gRPC UNAVAILABLE)` | backend 의 CNE(custom node executor) 미가동 → backend 운영자에게 문의 |
| 폴더명 불일치 실패 | 폴더명을 `NodeSchema.name` 과 동일하게 맞추기 |
| base_url 스킴 오류 | `AI_CANVAS_BASE_URL` 을 `http(s)://` 로 시작하게 설정 |
| 변경했는데 등록 안 됨 | 기본 브랜치(main)로의 push/merge 인지, `fetch-depth/GIT_DEPTH` 가 0(전체 히스토리)인지 확인 |
