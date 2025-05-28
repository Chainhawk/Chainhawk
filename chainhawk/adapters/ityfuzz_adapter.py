# ityfuzz_adapter.py
# ITYfuzz 도구 연동 어댑터 (블록체인 지원 추가)

import subprocess
import json
import os
import time
import tempfile
import shutil
from pathlib import Path
from ..config import DOCKER_CONFIG, ITYFUZZ_CONFIG, ANVIL_ACCOUNTS

def build_docker_image():
    """
    ITYfuzz 도커 이미지가 없으면 자동으로 빌드합니다.
    """
    tag = DOCKER_CONFIG['ityfuzz']['tag']
    dockerfile = DOCKER_CONFIG['ityfuzz']['dockerfile']
    check_cmd = ['docker', 'images', '-q', tag]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        print(f"[정보] 도커 이미지({tag})가 없어 자동 빌드합니다...")
        build_cmd = ['docker', 'build', '-f', dockerfile, '-t', tag, '.']
        build_result = subprocess.run(build_cmd, capture_output=True, text=True)
        if build_result.returncode != 0:
            raise RuntimeError(f"도커 이미지 빌드 실패: {build_result.stderr}")
        print(f"[성공] 도커 이미지({tag}) 빌드 완료.")

def start_anvil(debug=False):
    """
    Anvil 블록체인을 Docker 컨테이너로 시작합니다.
    """
    container_name = "chainhawk-anvil"
    
    # 기존 컨테이너 정리
    stop_cmd = ['docker', 'stop', container_name]
    subprocess.run(stop_cmd, capture_output=True)
    
    remove_cmd = ['docker', 'rm', container_name]
    subprocess.run(remove_cmd, capture_output=True)
    
    # Anvil 컨테이너 시작 (docker-compose 스타일 설정 적용)
    anvil_cmd = [
        'docker', 'run', '-d',
        '--name', container_name,
        '--network', 'host',  # host 네트워크 사용
        DOCKER_CONFIG['anvil']['image'],
        'anvil',
        '--host', '0.0.0.0',
        '--port', '8545',
        '--chain-id', str(ITYFUZZ_CONFIG['chain_id']),
        '--accounts', str(ITYFUZZ_CONFIG['accounts']),
        '--balance', str(ITYFUZZ_CONFIG['balance']),
        '--gas-limit', '30000000',
        '--gas-price', '1',
        '--mnemonic', ITYFUZZ_CONFIG['mnemonic']
    ]
    
    if debug:
        print(f"[디버그] Anvil 시작 명령어: {' '.join(anvil_cmd)}")
    
    result = subprocess.run(anvil_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if debug:
            print(f"[디버그] Anvil 시작 오류: {result.stderr}")
        raise RuntimeError(f"Anvil 시작 실패: {result.stderr}")
    
    # Anvil이 준비될 때까지 대기
    print("[정보] Anvil 블록체인 시작 중...")
    for i in range(30):  # 30초 대기
        try:
            # 컨테이너 상태 확인
            status_cmd = ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}']
            status_result = subprocess.run(status_cmd, capture_output=True, text=True)
            
            if debug and i % 5 == 0:  # 5번마다 디버그 출력
                print(f"[디버그] 컨테이너 상태 확인 ({i+1}/30): {status_result.stdout.strip()}")
            
            if "Up" not in status_result.stdout:
                if debug:
                    # 컨테이너 로그 확인
                    logs_cmd = ['docker', 'logs', container_name]
                    logs_result = subprocess.run(logs_cmd, capture_output=True, text=True)
                    print(f"[디버그] 컨테이너 로그: {logs_result.stdout}")
                    print(f"[디버그] 컨테이너 오류: {logs_result.stderr}")
                continue
            
            # RPC 연결 테스트
            test_cmd = [
                'curl', '-s', '-X', 'POST',
                '-H', 'Content-Type: application/json',
                '--data', '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}',
                f'http://localhost:{ITYFUZZ_CONFIG["port"]}'
            ]
            test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
            
            if debug and i % 5 == 0:
                print(f"[디버그] RPC 테스트 결과: {test_result.stdout}")
            
            if test_result.returncode == 0 and "result" in test_result.stdout:
                print(f"[성공] Anvil이 포트 {ITYFUZZ_CONFIG['port']}에서 실행 중입니다.")
                return True
                
        except subprocess.TimeoutExpired:
            if debug:
                print(f"[디버그] RPC 테스트 타임아웃 ({i+1}/30)")
        except Exception as e:
            if debug:
                print(f"[디버그] 연결 테스트 오류: {e}")
        
        time.sleep(2)
    
    # 타임아웃 시 로그 출력
    if debug:
        logs_cmd = ['docker', 'logs', container_name]
        logs_result = subprocess.run(logs_cmd, capture_output=True, text=True)
        print(f"[디버그] 최종 컨테이너 로그:")
        print(f"stdout: {logs_result.stdout}")
        print(f"stderr: {logs_result.stderr}")
    
    raise RuntimeError("Anvil 시작 타임아웃")

def stop_anvil():
    """
    Anvil 컨테이너를 중지합니다.
    """
    container_name = "chainhawk-anvil"
    stop_cmd = ['docker', 'stop', container_name]
    subprocess.run(stop_cmd, capture_output=True)
    remove_cmd = ['docker', 'rm', container_name]
    subprocess.run(remove_cmd, capture_output=True)
    print("[정보] Anvil 블록체인이 중지되었습니다.")

def deploy_contract(contract_file, debug=False):
    """
    Foundry를 사용하여 컨트랙트를 Anvil에 배포합니다.
    """
    work_dir = Path(tempfile.mkdtemp(prefix="chainhawk-deploy-"))
    
    try:
        # Foundry 프로젝트 초기화
        init_cmd = ['forge', 'init', '--no-git', str(work_dir), '--force']
        init_result = subprocess.run(init_cmd, capture_output=True, text=True)
        if init_result.returncode != 0:
            raise RuntimeError(f"Foundry 초기화 실패: {init_result.stderr}")
        
        # 컨트랙트 파일 복사
        contract_path = Path(contract_file)
        target_path = work_dir / "src" / contract_path.name
        shutil.copy2(contract_path, target_path)
        
        # 컨트랙트 배포
        contract_name = contract_path.stem
        deployer_key = ANVIL_ACCOUNTS[0]["private_key"]
        
        deploy_cmd = [
            'forge', 'create',
            f'src/{contract_path.name}:{contract_name}',
            '--rpc-url', f'http://localhost:{ITYFUZZ_CONFIG["port"]}',
            '--private-key', deployer_key,
            '--json'
        ]
        
        if debug:
            print(f"[디버그] 배포 명령어: {' '.join(deploy_cmd)}")
        
        deploy_result = subprocess.run(deploy_cmd, cwd=work_dir, capture_output=True, text=True)
        if deploy_result.returncode != 0:
            raise RuntimeError(f"컨트랙트 배포 실패: {deploy_result.stderr}")
        
        # 배포 결과 파싱
        deployment_info = json.loads(deploy_result.stdout)
        contract_address = deployment_info["deployedTo"]
        
        print(f"[성공] {contract_name} 배포 완료: {contract_address}")
        return contract_address
        
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

def run_ityfuzz_fuzzing(contract_address, debug=False):
    """
    배포된 컨트랙트에 대해 ITYfuzz 퍼징을 실행합니다.
    """
    tag = DOCKER_CONFIG['ityfuzz']['tag']
    
    # 결과 디렉토리 생성
    results_dir = Path("./ityfuzz_results")
    results_dir.mkdir(exist_ok=True)
    
    # ITYfuzz 명령어 구성
    fuzz_cmd = [
        'docker', 'run', '--rm',
        '--network', 'host',  # host 네트워크로 Anvil 접근
        '-v', f'{results_dir.absolute()}:/results',
        tag,
        'ityfuzz', 'evm',
        '--target', contract_address,
        '--rpc-url', f'http://localhost:{ITYFUZZ_CONFIG["port"]}',
        '--chain-id', str(ITYFUZZ_CONFIG['chain_id']),
        '--iterations', str(ITYFUZZ_CONFIG['iterations']),
        '--timeout', str(ITYFUZZ_CONFIG['timeout']),
        '--work-dir', '/results',
        '--verbose'
    ]
    
    if debug:
        print(f"[디버그] ITYfuzz 명령어: {' '.join(fuzz_cmd)}")
    
    print(f"[정보] ITYfuzz 퍼징 시작 (대상: {contract_address})...")
    fuzz_result = subprocess.run(fuzz_cmd, capture_output=True, text=True)
    
    if debug:
        print(f"[디버그] ITYfuzz 반환 코드: {fuzz_result.returncode}")
        print(f"[디버그] ITYfuzz 출력: {fuzz_result.stdout}")
        if fuzz_result.stderr:
            print(f"[디버그] ITYfuzz 오류: {fuzz_result.stderr}")
    
    return fuzz_result.stdout, fuzz_result.stderr

def run_ityfuzz(target_path, debug=False):
    """
    ITYfuzz를 사용한 전체 분석 워크플로우:
    1. Anvil 블록체인 시작
    2. 컨트랙트 배포
    3. ITYfuzz 퍼징 실행
    4. 결과 반환
    5. 인프라 정리
    """
    try:
        # 1. Docker 이미지 준비
        build_docker_image()
        
        # 2. Anvil 블록체인 시작
        start_anvil(debug)
        
        # 3. 컨트랙트 배포
        contract_address = deploy_contract(target_path, debug)
        
        # 4. ITYfuzz 퍼징 실행
        stdout, stderr = run_ityfuzz_fuzzing(contract_address, debug)
        
        # 5. 결과 파싱
        if "vulnerability" in stdout.lower() or "bug" in stdout.lower():
            return f"[ITYfuzz] 취약점이 발견되었습니다!\n\n분석 결과:\n{stdout}"
        elif stdout:
            return f"[ITYfuzz] 분석 완료\n\n{stdout}"
        else:
            return "[ITYfuzz] 분석 완료: 특별한 이슈가 발견되지 않았습니다."
    
    except Exception as e:
        return f"[ITYfuzz 오류] {str(e)}"
    
    finally:
        # 6. 인프라 정리
        stop_anvil()