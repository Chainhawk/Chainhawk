# Chainhawk

스마트 컨트랙트 멀티 분석 통합 플랫폼 (Phase 1)

- Semgrep, ITYfuzz, Halmos 등 다양한 분석기를 통합하여 스마트 컨트랙트 취약점 분석 결과를 한 번에 출력하는 Python 기반 플랫폼
- 현재 Semgrep(정적 분석)과 ITYfuzz(퍼징 기반 동적 분석)를 완전 지원하며, 향후 Halmos 등 추가 분석기도 통합 예정
- Foundry 프로젝트와 완전 통합되어 실제 블록체인 환경에서 동적 분석 수행
- Solidity용 커스텀 룰셋을 자유롭게 추가 가능 (Semgrep)

## 주요 특징

- **멀티 분석 엔진**: Semgrep(SAST), ITYfuzz(Dynamic Fuzzing) 통합 지원
- **Foundry 네이티브 지원**: 기존 Foundry 프로젝트를 그대로 사용하여 분석
- **실시간 블록체인 환경**: Anvil 로컬 체인에서 실제 컨트랙트 배포 및 퍼징
- **Docker 기반 실행**: 모든 분석기가 안전한 컨테이너 환경에서 실행
- **확장 가능한 구조**: 새로운 분석기를 쉽게 추가할 수 있는 어댑터 패턴
- **다양한 룰셋 지원**: 여러 개의 `.yaml` 룰셋을 한 번에 적용 (Semgrep)
- **한글 출력**: 분석 결과를 CLI에서 한글로 보기 쉽게 출력

## 필수 요구사항

- **Python 3.8+**
- **Docker**: 모든 분석 도구가 컨테이너에서 실행
- **Foundry**: ITYfuzz 분석 시 필요 (컨트랙트 컴파일 및 배포용)
  ```bash
  curl -L https://foundry.sh | bash
  foundryup
  ```

## 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. Docker 이미지 빌드
```bash
# Semgrep 이미지
docker build -f docker/semgrep.Dockerfile -t chainhawk-semgrep .

# ITYfuzz 이미지 (퍼징 분석용)
docker build -f docker/ityfuzz.Dockerfile -t chainhawk-ityfuzz .

# Anvil 이미지 (블록체인 환경)
docker pull ghcr.io/foundry-rs/foundry:latest
```

### 3. 환경 검증
```bash
# 모든 도구와 환경이 올바르게 설정되었는지 확인
python -m chainhawk.cli validate
```

## 사용 방법

### ITYfuzz 분석 (권장)
Foundry 프로젝트를 사용하여 실제 블록체인 환경에서 동적 퍼징 분석:

```bash
# 기본 분석 (컨트랙트 자동 감지)
python -m chainhawk.cli analyze --foundry-dir ./my_foundry_project --engine ityfuzz --debug

# 특정 컨트랙트 지정
python -m chainhawk.cli analyze --foundry-dir ./my_project --contract MyContract --engine ityfuzz

# 예시: 기존 프로젝트 분석
python -m chainhawk.cli analyze --foundry-dir ./DeFi-Project --contract Token --engine ityfuzz --debug
```

### Semgrep 분석
정적 코드 분석:

```bash
# Semgrep 룰셋으로 정적 분석
python -m chainhawk.cli analyze --foundry-dir ./my_project --engine semgrep --rules ./semgrep_rules/solidity/security
```

## Foundry 프로젝트 구조 예시

ITYfuzz 분석을 위한 표준 Foundry 프로젝트 구조:

```
my_project/
├── foundry.toml              # Foundry 설정 파일
├── src/
│   ├── MyContract.sol        # 분석할 메인 컨트랙트
│   ├── Token.sol            # 추가 컨트랙트들
│   └── interfaces/
├── test/
│   ├── MyContract.t.sol     # 테스트 파일들
│   └── Token.t.sol
├── script/
│   └── Deploy.s.sol         # 배포 스크립트
└── lib/                     # 의존성 라이브러리들
    └── forge-std/
```

## 분석 워크플로우

### ITYfuzz 전체 프로세스:
1. **Anvil 블록체인 시작** - 로컬 테스트 체인 구동
2. **컨트랙트 컴파일** - Foundry로 Solidity 컴파일
3. **스마트 컨트랙트 배포** - Anvil 체인에 실제 배포  
4. **ITYfuzz 퍼징 실행** - 배포된 컨트랙트 대상 동적 분석
5. **취약점 보고서 생성** - 발견된 이슈들을 한글로 출력
6. **환경 정리** - 임시 블록체인 및 컨테이너 정리

## 커스텀 룰셋 추가 (Semgrep)

1. `semgrep_rules/solidity/security/` 폴더에 새로운 `.yaml` 파일 추가
2. 예시 룰셋:
   ```yaml
   rules:
     - id: detect-reentrancy-pattern
       message: "재진입 공격 패턴 감지됨"
       pattern: |
         function $FUNC(...) {
           ...
           $ADDR.call{value: $VALUE}(...)
           ...
           $VAR = $VAR - $AMOUNT
           ...
         }
       languages: [solidity]
       severity: ERROR
   ```

3. 분석 실행 시 해당 폴더의 모든 룰이 자동 적용

## CLI 명령어

### 분석 실행
```bash
python -m chainhawk.cli analyze [OPTIONS]
```

**옵션:**
- `--foundry-dir, -f`: Foundry 프로젝트 디렉토리 경로 (필수)
- `--contract, -c`: 배포할 컨트랙트 이름 (선택사항, 자동 감지)
- `--engine, -e`: 분석 엔진 선택 (semgrep, ityfuzz)
- `--rules, -r`: Semgrep 룰셋 디렉터리 경로
- `--debug, -d`: 디버그 모드 활성화

### 유틸리티 명령어
```bash
# 환경 검증
python -m chainhawk.cli validate

# 도구 정보 확인
python -m chainhawk.cli info
```

## 실제 사용 예시

### DeFi 프로토콜 분석
```bash
# Uniswap V3 스타일 AMM 컨트랙트 퍼징
python -m chainhawk.cli analyze --foundry-dir ./UniswapV3-Fork --contract UniswapV3Pool --engine ityfuzz --debug

# 결과 예시:
# [ITYfuzz] 취약점이 발견되었습니다!
# 
# 분석 결과:
# - 산술 오버플로우 감지: line 127
# - 재진입 공격 벡터 발견: swapExactInputSingle 함수
# - 권한 우회 시나리오 탐지: onlyOwner 우회 가능
```

### NFT 컨트랙트 분석
```bash
# ERC-721 기반 NFT 컨트랙트 정적 분석
python -m chainhawk.cli analyze --foundry-dir ./NFT-Collection --engine semgrep --rules ./semgrep_rules/solidity/security

# ITYfuzz로 민팅 로직 동적 테스트
python -m chainhawk.cli analyze --foundry-dir ./NFT-Collection --contract MyNFT --engine ityfuzz
```

## 고급 설정

### ITYfuzz 설정 커스터마이징
`chainhawk/config.py`에서 퍼징 파라미터 조정:

```python
ITYFUZZ_CONFIG = {
    'chain_id': 31337,
    'iterations': 1000,  # 퍼징 반복 횟수 증가
    'timeout': 300,      # 타임아웃 연장
    'accounts': 20,      # 테스트 계정 수 증가
}
```

## 문제 해결

### 일반적인 오류들
- **"Foundry 프로젝트가 존재하지 않습니다"**: `foundry.toml` 파일이 있는 올바른 경로인지 확인
- **"컨트랙트 컴파일 실패"**: Foundry 프로젝트에서 `forge build` 명령으로 컴파일 가능한지 확인
- **"Docker 이미지를 찾을 수 없습니다"**: 위의 Docker 이미지 빌드 단계 재실행
- **"Anvil 시작 타임아웃"**: Docker Desktop이 실행 중인지, 충분한 시스템 리소스가 있는지 확인

### 로그 확인
```bash
# 상세한 디버그 로그와 함께 실행
python -m chainhawk.cli analyze --foundry-dir ./my_project --engine ityfuzz --debug
```


## 참고 자료

- **Foundry 문서**: https://book.getfoundry.sh/
- **Semgrep 문서**: https://semgrep.dev/docs/
- **ITYfuzz**: https://github.com/fuzzland/ityfuzz
- **Solidity 보안 가이드**: https://docs.soliditylang.org/en/latest/security-considerations.html
- **커뮤니티 룰셋**: https://github.com/Decurity/semgrep-smart-contracts
