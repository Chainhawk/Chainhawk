# Chainhawk

스마트 컨트랙트 멀티 분석 통합 플랫폼 (Phase 0)

- Semgrep을 Docker로 실행하여 스마트 컨트랙트 정적 분석 결과를 통합 출력하는 Python 기반 PoC

## 실행 방법

1. 의존성 설치: `pip install -r requirements.txt`
2. Semgrep 도커 이미지 빌드: `docker build -f docker/semgrep.Dockerfile -t chainhawk-semgrep .`
3. CLI 실행: `python -m chainhawk.cli --help`
