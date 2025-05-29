FROM ubuntu:22.04

# 의존성 설치
RUN apt-get update && apt-get install -y \
    curl wget git build-essential pkg-config \
    libssl-dev libz3-dev clang ca-certificates cmake jq \
    && rm -rf /var/lib/apt/lists/*

# 환경 변수
ENV CC=clang CXX=clang++

# Rust 설치
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Foundry 설치 (forge, cast, anvil 등)
RUN curl -L https://foundry.paradigm.xyz | bash
ENV PATH="/root/.foundry/bin:${PATH}"
RUN bash -c 'source ~/.bashrc && foundryup' || echo "Foundry installation continuing..."


# ITYfuzz 설치
RUN curl -L https://ity.fuzz.land/ | bash

# PATH에 ITYfuzz 추가
ENV PATH="/root/.ityfuzz/bin:/root/.cargo/bin:${PATH}"

# bashrc에 PATH 설정 추가
RUN echo 'export PATH="/root/.ityfuzz/bin:/root/.cargo/bin:$PATH"' >> ~/.bashrc

# 설치 확인 (실패해도 빌드 계속)
RUN bash -c 'source ~/.bashrc && ityfuzzup && which ityfuzz && ityfuzz --help' || echo "ITYfuzz not found but continuing..."
RUN bash -c 'source ~/.bashrc && which forge && forge --version' || echo "Forge not found but continuing..."

# 작업 디렉토리
WORKDIR /workspace
RUN mkdir -p /workspace/results/corpus /workspace/results/output

# 시작할 때 bashrc 로드
CMD ["bash", "-c", "source ~/.bashrc && echo 'Available tools:' && which forge && which cast && which anvil && which ityfuzz && bash"]