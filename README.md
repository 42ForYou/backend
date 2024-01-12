# backend

## 실행

- `docker compose up`: 서버 시작
- `docker compose exec -it <컨테이너 이름> /bin/bash`: <컨테이너 이름>에 접속하여 셸 시작

# 개발

## IDE 지원

이 프로젝트는 Postgre와의 의존성으로 인해 Docker로 구동하는 것을 권장한다. 그럼에도 불구하고 IDE의 구문 자동 완성, 구문 하이라이팅 등의 지원이 필요할 시 시스템 또는 virtualenv python 인터프리터를 구성할 수 있다.

이때 `psycopg2`을 설치하기 위해 컴파일러 등 빌드 환경이 필요하다.

> 예: Debian 기반 배포판의 경우 `sudo apt install build-essential`

### virtualenv 구성

`.gitignore`에서 무시하도록 설정된 `.venv`를 virtualenv의 디렉토리로 활용한다.

```bash
python3 -m venv .venv  # .venv 디렉토리 내 virtualenv 구성
source ./.venv/bin/activate  # virtualenv 활성화
### 필요한 작업 수행 후 ... ###
deactivate  # virtualenv 비활성화
```

### Python 패키지 설치

시스템 인터프리터를 사용한다면 `python3 -m pip` 등의 구문으로 포함된 `pip`를 호출하고, virtualenv 사용 시 단순히 `pip`를 호출하면 된다.

```bash
# 시스템 인터프리터
python3 -m pip install -r requirements.txt
# virtualenv
pip install -r requirements.txt
```
