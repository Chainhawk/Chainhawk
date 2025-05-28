# Anvil (Foundry) 블록체인 컨테이너
FROM ghcr.io/foundry-rs/foundry:latest

# 기본 도구 설치
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 헬스체크 스크립트 추가
RUN echo '#!/bin/bash\ncurl -sf -X POST -H "Content-Type: application/json" --data '"'"'{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'"'"' http://localhost:8545 > /dev/null' > /usr/local/bin/healthcheck.sh \
    && chmod +x /usr/local/bin/healthcheck.sh

# 고정된 니모닉 사용하여 예측 가능한 계정 생성
ENV ANVIL_MNEMONIC="test test test test test test test test test test test junk"

# 헬스체크 설정
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD /usr/local/bin/healthcheck.sh

# 포트 노출
EXPOSE 8545

# Anvil 실행
CMD ["anvil", "--host", "0.0.0.0", "--port", "8545", "--chain-id", "31337", "--accounts", "10", "--balance", "10000", "--mnemonic", "test test test test test test test test test test test junk"]