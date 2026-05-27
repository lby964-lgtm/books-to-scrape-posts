# Books to Scrape 자동 업로드 과제

Books to Scrape 사이트에서 책 정보를 크롤링하고, GitHub 블로그에 올릴 수 있는 Markdown 글로 변환한 뒤, 5분마다 1개씩 자동으로 `git push`하는 예제입니다.

## 프로세스 순서

1. `https://books.toscrape.com/`에 접속해 첫 5권의 상세 페이지 정보를 수집합니다.
2. 수집 데이터를 `data/books.json`으로 저장합니다.
3. 저장된 데이터를 GitHub 블로그 포스트 형식의 `.md` 파일로 변환합니다.
4. `scripts/upload_one.sh`가 다음 순번의 글 1개만 `git add`, `git commit`, `git push`합니다.
5. 로컬에서는 `scripts/run_scheduler.sh`, GitHub에서는 `.github/workflows/upload-books.yml`이 위 작업을 5분 간격으로 반복해 총 5글을 순차 업로드합니다.

## 파일 구조

```text
.
├── README.md
├── requirements.txt
├── .github/workflows/upload-books.yml
├── src
│   ├── crawl_books.py
│   └── generate_markdown.py
└── scripts
    ├── run_pipeline_once.sh
    ├── run_scheduler.sh
    └── upload_one.sh
```

## 실행 방법

Python 표준 라이브러리만 사용하므로 별도 패키지는 필요하지 않습니다.

```bash
python src/crawl_books.py --count 5
python src/generate_markdown.py
```

5분마다 1개씩 자동 업로드하려면 Git 저장소 안에서 아래 명령을 실행합니다.

```bash
bash scripts/run_scheduler.sh
```

테스트할 때 5분을 기다리지 않으려면 간격을 줄일 수 있습니다.

```bash
INTERVAL_SECONDS=10 bash scripts/run_scheduler.sh
```

## Git 설정

처음 실행 전 GitHub 원격 저장소와 사용자 정보를 설정합니다.

```bash
git remote add origin https://github.com/<github-id>/<repo-name>.git
git config user.name "<github-id>"
git config user.email "<email>"
```

이미 첫 번째 글을 수동으로 올린 상태에서 두 번째 글부터 자동 업로드하려면 아래처럼 상태 파일을 지정할 수 있습니다.

```bash
echo 1 > .upload_state
bash scripts/run_scheduler.sh
```

`.upload_state`는 로컬 업로드 순번만 저장하며 Git에는 커밋하지 않습니다.

## GitHub Actions 자동화

`.github/workflows/upload-books.yml`은 5분마다 실행되며 `scripts/upload_one.sh`를 호출합니다. 이 워크플로는 이미 커밋된 `posts/*.md` 개수를 기준으로 다음 글 1개만 생성하고 푸시합니다.
