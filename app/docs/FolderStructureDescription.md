app/
│
├── environment.yml
├── main.py
├── Makefile
│
├── api/                     # API 엔드포인트 관련 코드
│   ├── routes/              # API 라우팅
│   ├── controllers/         # API 컨트롤러
│   ├── middlewares/         # API 미들웨어 (에러 핸들링 등)
│   └── exceptions/          # 예외처리 클래스 및 핸들러
│
├── db/                      # 데이터베이스 연결 관련
│   ├── connection/          # DB 연결 설정
│   ├── models/              # DB 모델 정의
│   ├── migrations/          # DB 마이그레이션 
│   └── repositories/        # DB 작업 추상화 계층
│
├── data/                    # 데이터 처리 관련
│   ├── postgresql/          # PostgreSQL 쿼리 및 데이터 액세스
│   ├── preprocessing/       # 데이터 전처리 로직
│   │   └── filtering/       # 질문 필터 분별 로직
│   └── embedding/           # 임베딩 처리 로직
│
├── vectordb/             # 벡터 저장소 관련
│   ├── config/              # 벡터 저장소 설정
│   ├── indexing/            # 인덱싱 작업 관리
│   ├── search/              # 유사도 검색 구현
│   └── metadata/            # 메타데이터 관리
│
├── llm/                     # LLM 관련
│   ├── models/              # LLM 모델 설정
│   ├── prompts/             # 프롬프트 템플릿
│   ├── context/             # 컨텍스트 관리
│   └── evaluation/          # 모델 평가 관련 코드
│
├── postprocessing/          # 후처리 로직
│   ├── ranking/             # 랭킹 알고리즘
│   ├── filtering/           # 결과 필터링
│   ├── threshold/           # Threshold 필터링
│   └── validation/          # 응답 검증 로직
│
├── cache/                   # 캐시 시스템 (유사 질문 등의 결과 캐싱)
│
├── monitoring/              # 시스템 모니터링
│   ├── logging/             # 로깅 시스템
│   ├── analytics/           # 응답 품질 모니터링
│   └── feedback/            # 사용자 피드백 반영 시스템
│
├── docs/                    # API 문서화
│   ├── openapi/             # OpenAPI (Swagger) 문서
│   ├── postman/             # Postman API Collection
│   └── guides/              # 개발자 가이드 및 README
│
├── config/                  # 시스템 설정
│   ├── env/                 # 환경 설정
│   ├── settings/            # 앱 설정
│   └── secrets/             # 민감한 정보 관리 (gitignore 포함)
│
├── utils/                   # 유틸리티 함수
│
├── services/                # 비즈니스 로직
│   ├── similarity/          # 유사도 검색 서비스
│   ├── chat/                # 챗봇 서비스
│   ├── indexing/            # 인덱싱 서비스
│   ├── feedback/            # 응답 피드백 처리
│   └── recommendation/      # 추천 시스템 (필요할 경우 추가)
│
├── scripts/                 # 유틸리티 스크립트
│   ├── indexing/            # 인덱싱 스크립트
│   ├── data_import/         # 데이터 임포트 스크립트
│   ├── evaluation/          # 시스템 평가 스크립트
│   └── monitoring/          # 시스템 자동 모니터링
│
├── docker/                  # Docker 관련 파일
│   ├── Dockerfile           # 백엔드 도커파일
│   └── docker-compose.yml   # 도커 컴포즈 설정
│
└── .github/                 # GitHub Actions 관련 (CI/CD)
    ├── workflows/           # CI/CD 워크플로우 설정
    ├── pull_request_template.md # PR 템플릿
    └── issue_template.md    # 이슈 템플릿
