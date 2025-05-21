# Chainhawk

스마트 컨트랙트 멀티 분석 통합 플랫폼 (Phase 0)

- Semgrep, ITYfuzz, Halmos 등 다양한 분석기를 통합하여 스마트 컨트랙트 취약점 분석 결과를 한 번에 출력하는 Python 기반 PoC
- 현재는 Semgrep을 Docker로 실행하여 정적 분석을 지원하며, 향후 ITYfuzz, Halmos 등 동적/퍼징 분석기도 통합 예정
- Solidity용 커스텀 룰셋을 자유롭게 추가 가능

## 주요 특징

- Semgrep, ITYfuzz, Halmos 등 다양한 분석기 통합 지원 (확장 구조)
- 분석기는 Docker 컨테이너에서 안전하게 실행
- 여러 개의 `.yaml` 룰셋을 한 번에 적용 (Semgrep)
- 분석 결과를 CLI에서 한글로 보기 쉽게 출력
- Solidity 등 다양한 언어 지원 (룰셋/분석기 확장에 따라)

## 설치 및 실행 방법

1. 의존성 설치  
   ```bash
   pip install -r requirements.txt
   ```

2. Semgrep Docker 이미지 빌드  
   ```bash
   docker build -f docker/semgrep.Dockerfile -t chainhawk-semgrep .
   ```

3. 분석 실행  
   ```bash
   python -m chainhawk.cli -t Sample/ReentrancyVuln.sol -r semgrep_rules/solidity/security
   ```

   - `-t` : 분석할 스마트 컨트랙트 파일 경로
   - `-r` : Semgrep 룰셋 디렉터리(폴더 내 모든 `.yaml` 룰 자동 적용)
   - `-d` : (선택) 디버그 모드

## 커스텀 룰셋 추가 방법 (Semgrep)

1. `semgrep_rules/solidity/security/` 폴더에 새로운 `.yaml` 파일을 추가
2. 예시:
   ```yaml
   rules:
     - id: detect-transfer-function
       message: "transfer 함수 발견"
       pattern: |
         function transfer(
       languages: [solidity]
       severity: INFO
   ```

3. 분석 시 해당 폴더 내 모든 룰셋이 자동 적용됨

## 예시

```bash
python -m chainhawk.cli -t Sample/ReentrancyVuln.sol -r semgrep_rules/solidity/security
```

## 향후 지원 예정

- ITYfuzz: 퍼징 기반 스마트 컨트랙트 취약점 탐지기
- Halmos: 동적 분석 기반 스마트 컨트랙트 취약점 탐지기
- 분석기별 Dockerfile 및 통합 CLI 지원 예정

## 참고

- Semgrep 공식 문서: https://semgrep.dev/docs/
- Solidity 보안 가이드: https://docs.soliditylang.org/en/latest/security-considerations.html
- Semgrep rules : https://github.com/Decurity/semgrep-smart-contracts