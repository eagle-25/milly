# Milly E-Commerce API

Django 기반의 API 서버입니다. 헥사고날 아키텍처를 적용하여 확장 가능하고 테스트 가능한 구조로 설계되었습니다.

## 기술 스택

- **Framework**: Django 5.2.7
- **Database**: SQLite (test시 사용), MySQL (실제 동작시 사용)
- **Package Manager**: uv
- **Code Quality**: Ruff (linting & formatting), mypy (type checking)
- **Containerization**: Docker, Docker Compose


## 프로젝트 구조

```
milly/
├── src/                          
│   ├── common/                  # Django 프로젝트 설정
│   │   ├── settings.py          
│   │   ├── settings_test.py     # 테스트시 사용하는 settings 파일
│   │   ├── urls.py              
│   │   ├── middlewares/         # 커스텀 미들웨어
│   │   └── exceptions.py        
│   │
│   ├── commerce/                
│   │   ├── domain/              
│   │   │   ├── entities.py      
│   │   │   └── exceptions.py    
│   │   │
│   │   ├── app/                 
│   │   │   ├── usecases.py      
│   │   │   ├── services.py      # 도메인 서비스 (복잡한 비즈니스 로직)
│   │   │   └── ports/           # 포트 (인터페이스)
│   │   │       └── interfaces.py
│   │   │
│   │   ├── adapter/             # 어댑터 레이어 (포트 구현체)
│   │   │   ├── web/             # 웹 어댑터
│   │   │   │   ├── views.py     # API 뷰
│   │   │   │   └── dtos.py      # 데이터 전송 객체
│   │   │   │
│   │   │   └── persistence/     # 영속성 어댑터
│   │   │       └── django_orm/  # Django ORM 구현
│   │   │           ├── models.py
│   │   │           └── django_orm_persistence_adpater.py
│   │   │
│   │   ├── tests.py             # E2E 테스트
│   │   └── factories.py         # 테스트 팩토리
│   │
│   ├── manage.py                # Django 관리 스크립트
│   └── conftest.py              # pytest 설정
│
├── pyproject.toml               # 프로젝트 설정
├── docker-compose.yml           # 도커 컴포즈
├── Dockerfile                   # 도커 이미지
└── Makefile                     # 빌드 스크립트
```

## 아키텍처 특징

### 헥사고날 아키텍처 (포트-어댑터)
- **도메인 중심 설계**: 비즈니스 로직을 도메인 레이어에 집중
- **의존성 역전**: 인터페이스를 통한 계층 간 결합도 감소
- **테스트 용이성**: 각 레이어별 독립적인 테스트 가능

### 동시성 제어
- **낙관적 잠금**: 버전 기반 충돌 감지
- **재시도 메커니즘**: 충돌 시 자동 재시도 (exponential backoff)
- **트랜잭션**: 원자성 보장


## 주요 테스트 케이스
- 상품 생성
- [재고 수정 + 동시성 제어](https://github.com/eagle-25/milly/blob/aa1773b3d26829e0b4bed4af915529068a403e8b/src/commerce/tests.py#L172)
- 할인 적용
- 쿠폰 생성
- 기타 예외상황

## 고민
### 에러 핸들링 코드 반복 최소화
- As-is: DomainException -> Catch -> Status 코드 설정이 반환되는 문제가 있었음
- To-be: Status Code를 설정하는 공통 Exception 정의 후, 해당 Exception 발생시 Custom Middleware에서 일정한 형식과 사전에 정의된 StatusCode로 응답 반환하도록 개발

### 영속성 계층 분리

- 원자성 보장, 낙관적 잠금을 서비스 레이어서 처리할지, 영속성 어댑터에서 처리할지 고민이였음

- DB와 같은 외부 의존성의 Context가 비즈니스 로직에 침투하는 것은 Clean Code 관점에서 올바르지 않다고 판단해 영속성 어댑터에 반영.

### 동시성 처리 (낙관적 vs 비관적)
- 재고 수정시 동시성 문제 발생 가능. 비관적 잠금은 DB 성능에 영향을 줄 수 있으므로 낙관적 잠금 사용. 재시도 하는 상황 대비해 Retry 적용. 
- Retry Delay는 지수적으로 증가하되, 약간의 분산(jitter)을 주어 retry시 트래픽 몰리는 현상 억제함.

### 재고 데이터 저장 방식

- 하나의 Row만 수정하는 경우, 수정 이력을 추적하기 어려움. 따라서 Event를 쌓는 방식으로 개발함.

- 만약 Event쌓기만 한다면, 최종 재고 현황을 파악하려면 모든 Event 값을 확인해야 하는 문제가 있음.

- Event Row에 변경후 값을 포함해 마지막 version의 row만 조회하면 현재 재고값을 가져올 수 있도록 처리


## 프로젝트 실행 방법

### 개발 환경 설정
```bash
# 의존성 설치
make install

# 코드 품질 검사
make check

# 테스트 실행
make test
```

### Docker 실행
```bash
# 서비스 시작
make up

# 서비스 종료  
make down
```


### 의존성 관리

```bash
# 운영 의존성 추가
uv add <package-name>

# 개발 의존성 추가
uv add --dev <package-name>

# 의존성 제거
uv remove <package-name>
```

## API 스펙

### 1. 상품 관리

#### 상품 생성
- **POST** `/commerce/products/`
- **Request Body:**
```json
{
  "name": "상품명",
  "description": "상품 설명",
  "price": 10000.0,
  "stock": 100
}
```
- **cURL 예제:**
```bash
curl -X POST http://0.0.0.0:8000/commerce/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "테스트 상품",
    "description": "이것은 테스트 상품입니다",
    "price": 10000.0,
    "stock": 100
  }'
```
- **Response:**
```json
{
  "id": "PROD1234ab",
  "name": "상품명",
  "description": "상품 설명", 
  "price": 10000.0,
  "stock_count": 100
}
```

#### 상품 목록 조회
- **GET** `/commerce/products/`
- **Query Parameters:**
  - `product_name` (optional): 상품명 필터
  - `page_size` (default: 30): 페이지 크기
  - `page_index` (default: 1): 페이지 번호
- **cURL 예제:**
```bash
# 전체 상품 목록 조회
curl -X GET http://0.0.0.0:8000/commerce/products/

# 필터 및 페이지네이션 적용 
curl -G -X GET "http://0.0.0.0:8000/commerce/products/" \
  --data-urlencode "product_name=테스트" \
  --data-urlencode "page_size=10" \
  --data-urlencode "page_index=1"
```
- **Response:**
```json
{
  "products": [
    {
      "id": "PROD1234ab",
      "name": "상품명",
      "description": "상품 설명",
      "price": 10000.0,
      "stock_count": 100,
      "discount_amount": 1000.0,
      "final_price": 9000.0
    }
  ]
}
```

#### 상품 상세 조회
- **GET** `/commerce/products/{product_id}/`
- **cURL 예제:**
```bash
curl -X GET http://0.0.0.0:8000/commerce/products/<your-product-id>/
```
- **Response:**
```json
{
  "product": {
    "id": "PROD1234ab",
    "name": "상품명",
    "description": "상품 설명",
    "price": 10000.0,
    "created_at": "2025-11-20T05:36:02.148Z",
    "updated_at": "2025-11-20T05:36:02.148Z"
  },
  "product_discount_amount": 1000.0,
  "cupon_discount_amount": 500.0,
  "total_amount": 8500.0
}
```

### 2. 재고 관리

#### 재고 수정
- **POST** `/commerce/products/{product_id}/stock/`
- **Request Body:**
```json
{
  "change": 50
}
```
- **cURL 예제:**
```bash
curl -X POST http://0.0.0.0:8000/commerce/products/<your-product-id>/stock/ \
  -H "Content-Type: application/json" \
  -d '{"change": 50}'
```
- **Response:**
```json
{
  "new_stock_count": 150
}
```
- **참고:** 동시성 제어를 위한 낙관적 잠금 적용, 충돌 시 자동 재시도

### 3. 할인 관리

#### 상품 할인 설정
- **POST** `/commerce/products/{product_id}/discounts/`
- **Request Body:**
```json
{
  "percentage": 20.0
}
```
- **cURL 예제:**
```bash
curl -X POST http://0.0.0.0:8000/commerce/products/<your-product-id>/discounts/ \
  -H "Content-Type: application/json" \
  -d '{"percentage": 20.0}'
```
- **Response:**
```json
{
  "discount_id": "DISC1234ab",
  "product_id": "PROD1234ab",
  "percentage": 20.0,
  "is_active": true
}
```
- **참고:** 새 할인 생성 시 기존 할인은 자동으로 비활성화됨

### 4. 쿠폰 관리

#### 쿠폰 생성
- **POST** `/commerce/coupons/`
- **인증 필요**: 로그인한 사용자만 쿠폰 생성 가능
- **Request Body:**
```json
{
  "code": "DISCOUNT20",
  "discount_percentage": 20.0,
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_to": "2024-12-31T23:59:59Z"
}
```
- **cURL 예제:**
```bash
curl -X POST http://0.0.0.0:8000/commerce/coupons/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "DISCOUNT20",
    "discount_percentage": 20.0,
    "valid_from": "2024-01-01T00:00:00Z",
    "valid_to": "2024-12-31T23:59:59Z"
  }'
```
- **Response:**
```json
{
  "cupon_id": "CUPON1234ab",
  "user_id": "1",
  "code": "DISCOUNT20", 
  "discount_percentage": 20.0
}
```
