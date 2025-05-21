# config.py
# 통합 설정 파일 파싱 및 관리 

DOCKER_CONFIG = {
    'semgrep': {
        'dockerfile': 'docker/semgrep.Dockerfile',
        'tag': 'chainhawk-semgrep',
    },
    # 추후 ityfuzz, halmos도 추가 가능
} 