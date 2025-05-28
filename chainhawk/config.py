# config.py
# 통합 설정 파일 파싱 및 관리 

DOCKER_CONFIG = {
    'semgrep': {
        'dockerfile': 'docker/semgrep.Dockerfile',
        'tag': 'chainhawk-semgrep',
    },
    'ityfuzz': {
        'dockerfile': 'docker/ityfuzz.Dockerfile',
        'tag': 'chainhawk-ityfuzz',
    },
    'anvil': {
        'image': 'ghcr.io/foundry-rs/foundry:latest',
        'tag': 'chainhawk-anvil',
    }
}

# ITYfuzz 설정
ITYFUZZ_CONFIG = {
    'chain_id': 31337,
    'port': 8545,
    'iterations': 500,
    'timeout': 120,
    'accounts': 10,
    'balance': 10000,
    'mnemonic': 'test test test test test test test test test test test junk'
}

# Anvil 기본 계정들 (고정된 니모닉에서 생성)
ANVIL_ACCOUNTS = [
    {
        "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "private_key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    },
    {
        "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", 
        "private_key": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
    },
    {
        "address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        "private_key": "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"
    }
]