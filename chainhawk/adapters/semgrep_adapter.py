import subprocess
import json
import os

def run_semgrep(target_path):
    """
    Semgrep을 도커 컨테이너에서 실행하고 결과(JSON)를 반환합니다.
    """
    abs_target = os.path.abspath(target_path)
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{abs_target}:/src',
        'chainhawk-semgrep',
        '--config', 'auto',
        '--json', '/src'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"[오류] Semgrep 실행 실패: {e.stderr}" 