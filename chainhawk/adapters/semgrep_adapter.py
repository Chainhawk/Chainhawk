import subprocess
import json
import os
import glob
from ..config import DOCKER_CONFIG

def build_docker_image():
    """
    Semgrep 도커 이미지가 없으면 자동으로 빌드합니다.
    """
    tag = DOCKER_CONFIG['semgrep']['tag']
    dockerfile = DOCKER_CONFIG['semgrep']['dockerfile']
    # 이미지 존재 여부 확인
    check_cmd = ['docker', 'images', '-q', tag]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        print(f"[정보] 도커 이미지({tag})가 없어 자동 빌드합니다...")
        build_cmd = ['docker', 'build', '-f', dockerfile, '-t', tag, '.']
        build_result = subprocess.run(build_cmd, capture_output=True, text=True)
        if build_result.returncode != 0:
            raise RuntimeError(f"도커 이미지 빌드 실패: {build_result.stderr}")
        print(f"[성공] 도커 이미지({tag}) 빌드 완료.")

def extract_json(text):
    """
    텍스트에서 JSON 부분을 추출합니다.
    """
    try:
        # 첫 번째 '{' 부터 마지막 '}' 까지의 텍스트를 추출
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            json_text = text[start:end]
            print(f"[디버그] 추출된 JSON 시작: {json_text[:100]}...")
            return json_text
    except Exception as e:
        print(f"[디버그] JSON 추출 오류: {e}")
    return text

def run_semgrep(target_path, rules_path='semgrep_rules'):
    """
    Semgrep을 도커 컨테이너에서 실행하고 결과를 반환합니다.
    """
    build_docker_image()
    abs_target = os.path.abspath(target_path)
    print(f"[디버그] 절대 경로: {abs_target}")
    
    # rules_path가 절대경로가 아니면, 현재 작업 디렉터리 기준으로 변환
    if not os.path.isabs(rules_path):
        rules = os.path.abspath(rules_path)
    else:
        rules = rules_path
    print(f"[디버그] 룰셋 절대 경로: {rules}")

    # 룰셋 파일 목록 수집
    rule_files = []
    for root, _, files in os.walk(rules):
        for file in files:
            if file.endswith('.yaml'):
                rule_files.append(os.path.join(root, file))
    
    if not rule_files:
        return "[오류] 룰셋 파일을 찾을 수 없습니다."

    print(f"[디버그] 발견된 룰셋 파일들: {rule_files}")
    
    tag = DOCKER_CONFIG['semgrep']['tag']

    # 먼저 rules 디렉터리 확인
    check_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{rules}:/rules',
        tag,
        'ls', '-la', '/rules'
    ]
    check_result = subprocess.run(check_cmd, capture_output=True, text=True)
    print("[정보] 룰셋 디렉터리 내용:")
    print(check_result.stdout)

    # 각 룰셋 파일에 대해 개별적으로 Semgrep 실행
    all_findings = []
    for rule_file in rule_files:
        rule_name = os.path.basename(rule_file)
        print(f"[디버그] {rule_name} 룰셋으로 검사 중...")
        
        # Semgrep 실행
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{abs_target}:/src/{os.path.basename(abs_target)}',
            '-v', f'{rule_file}:/rules/{rule_name}',
            tag,
            '--config', f'/rules/{rule_name}',
            '--metrics', 'off',
            '--json',
            f'/src/{os.path.basename(abs_target)}'
        ]
        print(f"[디버그] 실행할 명령어: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        print(f"[디버그] 반환 코드: {result.returncode}")
        
        if result.returncode != 0 and "METRICS:" not in result.stderr:
            print(f"[경고] {rule_name} 룰셋 실행 실패: {result.stderr}")
            continue
        
        try:
            json_text = extract_json(result.stdout)
            findings = json.loads(json_text)
            if findings.get('results'):
                all_findings.extend(findings['results'])
        except json.JSONDecodeError as e:
            print(f"[경고] {rule_name} 결과 파싱 실패: {e}")
    
    if all_findings:
        output = "다음과 같은 취약점이 발견되었습니다:\n\n"
        for finding in all_findings:
            output += f"[취약점] {finding.get('check_id', 'Unknown')}\n"
            output += f"위치: {os.path.basename(finding.get('path', ''))}:{finding.get('start', {}).get('line', '?')}\n"
            output += f"설명: {finding.get('extra', {}).get('message', '설명 없음')}\n"
            output += "-" * 80 + "\n"
        return output
    
    return "분석 완료: 취약점이 발견되지 않았습니다." 