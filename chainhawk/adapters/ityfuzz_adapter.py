# ityfuzz_adapter.py
# ITYfuzz 도구 연동 어댑터 (블록체인 지원 추가)

import subprocess
import json
import os
import time
import tempfile
import shutil
import re
import requests
from pathlib import Path
from eth_utils import keccak
import rlp
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
    
    # Anvil 컨테이너 시작
    anvil_cmd = [
        'docker', 'run', '-d',
        '--name', container_name,
        '--network', 'host',
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
    for i in range(30):
        try:
            test_cmd = [
                'curl', '-s', '-X', 'POST',
                '-H', 'Content-Type: application/json',
                '--data', '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}',
                f'http://localhost:{ITYFUZZ_CONFIG["port"]}'
            ]
            test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=5)
            
            if test_result.returncode == 0 and "result" in test_result.stdout:
                print(f"[성공] Anvil이 포트 {ITYFUZZ_CONFIG['port']}에서 실행 중입니다.")
                return True
                
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            if debug:
                print(f"[디버그] 연결 테스트 오류: {e}")
        
        time.sleep(2)
    
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

def calculate_contract_address(sender, nonce):
    """
    CREATE opcode 규칙을 사용하여 컨트랙트 주소를 계산합니다.
    """
    sender_bytes = bytes.fromhex(sender[2:])  # 0x 제거
    encoded = rlp.encode([sender_bytes, nonce])
    hash_result = keccak(encoded)
    return '0x' + hash_result[-20:].hex()

def deploy_contract(foundry_project_dir, contract_name=None, debug=False):
    """
    기존 Foundry 프로젝트 디렉토리를 사용하여 컨트랙트를 배포합니다.
    
    Args:
        foundry_project_dir: Foundry 프로젝트 디렉토리 경로
        contract_name: 배포할 컨트랙트 이름 (없으면 자동 감지)
        debug: 디버그 모드
    """
    foundry_dir = Path(foundry_project_dir)
    
    if not foundry_dir.exists():
        raise RuntimeError(f"Foundry 프로젝트 디렉토리가 존재하지 않습니다: {foundry_project_dir}")
    
    if not (foundry_dir / "foundry.toml").exists():
        raise RuntimeError(f"유효한 Foundry 프로젝트가 아닙니다: {foundry_project_dir}")
    
    src_dir = foundry_dir / "src"
    if not src_dir.exists():
        raise RuntimeError(f"src 디렉토리가 없습니다: {src_dir}")
    
    try:
        # 컨트랙트 이름이 지정되지 않으면 자동 감지
        if not contract_name:
            # src 디렉토리에서 첫 번째 .sol 파일 찾기
            sol_files = list(src_dir.glob("*.sol"))
            if not sol_files:
                raise RuntimeError(f"src 디렉토리에 .sol 파일이 없습니다: {src_dir}")
            
            # 첫 번째 파일에서 컨트랙트 이름 추출
            first_contract_file = sol_files[0]
            with open(first_contract_file, 'r') as f:
                content = f.read()
                contract_matches = re.findall(r'contract\s+(\w+)', content)
                if contract_matches:
                    contract_name = contract_matches[0]
                    contract_file_name = first_contract_file.name
                else:
                    raise RuntimeError(f"컨트랙트를 찾을 수 없습니다: {first_contract_file}")
        else:
            # 지정된 컨트랙트 이름으로 파일 찾기
            contract_file_name = f"{contract_name}.sol"
            contract_file_path = src_dir / contract_file_name
            if not contract_file_path.exists():
                raise RuntimeError(f"컨트랙트 파일을 찾을 수 없습니다: {contract_file_path}")
        
        if debug:
            print(f"[디버그] 컨트랙트 이름: {contract_name}")
            print(f"[디버그] 컨트랙트 파일: {contract_file_name}")
            print(f"[디버그] Foundry 프로젝트: {foundry_dir}")
        
        # 컴파일
        compile_cmd = ['forge', 'build']
        
        if debug:
            print(f"[디버그] 컴파일 명령어: {' '.join(compile_cmd)}")
        
        compile_result = subprocess.run(
            compile_cmd, 
            cwd=foundry_dir,
            capture_output=True, 
            text=True
        )
        
        if compile_result.returncode != 0:
            if debug:
                print(f"[디버그] 컴파일 오류:")
                print(f"stdout: {compile_result.stdout}")
                print(f"stderr: {compile_result.stderr}")
            raise RuntimeError(f"컨트랙트 컴파일 실패: {compile_result.stderr}")
        
        if debug:
            print(f"[디버그] 컴파일 성공!")
        
        # 배포 전에 논스 확인 및 컨트랙트 주소 미리 계산
        deployer_address = ANVIL_ACCOUNTS[0]["address"]
        deployer_key = ANVIL_ACCOUNTS[0]["private_key"]
        
        # 현재 논스 가져오기
        nonce_payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionCount",
            "params": [deployer_address, "latest"],
            "id": 1
        }
        
        try:
            response = requests.post(
                f'http://localhost:{ITYFUZZ_CONFIG["port"]}',
                json=nonce_payload,
                timeout=10
            )
            current_nonce = int(response.json()["result"], 16)
            if debug:
                print(f"[디버그] 현재 논스: {current_nonce}")
        except Exception as e:
            if debug:
                print(f"[디버그] 논스 조회 실패: {e}")
            current_nonce = 0
        
        # 컨트랙트 주소 미리 계산
        expected_address = calculate_contract_address(deployer_address, current_nonce)
        if debug:
            print(f"[디버그] 예상 컨트랙트 주소: {expected_address}")
        
        # 배포
        deploy_cmd = [
            'forge', 'create',
            f'src/{contract_file_name}:{contract_name}',
            '--rpc-url', f'http://localhost:{ITYFUZZ_CONFIG["port"]}',
            '--private-key', deployer_key,
            '--json'
        ]
        
        if debug:
            print(f"[디버그] 배포 명령어: {' '.join(deploy_cmd)}")
        
        deploy_result = subprocess.run(
            deploy_cmd,
            cwd=foundry_dir,
            capture_output=True,
            text=True
        )
        
        if deploy_result.returncode != 0:
            if debug:
                print(f"[디버그] 배포 오류:")
                print(f"stdout: {deploy_result.stdout}")
                print(f"stderr: {deploy_result.stderr}")
            raise RuntimeError(f"컨트랙트 배포 실패: {deploy_result.stderr}")
        
        if debug:
            print(f"[디버그] 배포 출력:")
            print(deploy_result.stdout)
        
        # 배포 결과에서 컨트랙트 주소 추출
        contract_address = None
        
        try:
            deployment_info = json.loads(deploy_result.stdout)
            
            # 다양한 필드에서 컨트랙트 주소 찾기
            possible_fields = ["deployedTo", "contractAddress", "address"]
            for field in possible_fields:
                if field in deployment_info and deployment_info[field]:
                    contract_address = deployment_info[field]
                    break
            
            # 트랜잭션 해시가 있으면 receipt에서 확인
            tx_hash = None
            if "transactionHash" in deployment_info:
                tx_hash = deployment_info["transactionHash"]
            elif "transaction" in deployment_info:
                tx_info = deployment_info["transaction"]
                if "hash" in tx_info:
                    tx_hash = tx_info["hash"]
            
            if not contract_address and tx_hash:
                if debug:
                    print(f"[디버그] 트랜잭션 해시에서 주소 추출: {tx_hash}")
                
                # 잠시 대기 후 receipt 조회
                time.sleep(2)
                
                receipt_payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionReceipt",
                    "params": [tx_hash],
                    "id": 1
                }
                
                try:
                    response = requests.post(
                        f'http://localhost:{ITYFUZZ_CONFIG["port"]}',
                        json=receipt_payload,
                        timeout=10
                    )
                    receipt_data = response.json()
                    
                    if debug:
                        print(f"[디버그] Receipt 데이터: {receipt_data}")
                    
                    if "result" in receipt_data and receipt_data["result"]:
                        receipt = receipt_data["result"]
                        if "contractAddress" in receipt and receipt["contractAddress"]:
                            contract_address = receipt["contractAddress"]
                            
                except Exception as rpc_e:
                    if debug:
                        print(f"[디버그] Receipt RPC 오류: {rpc_e}")
                        
        except (json.JSONDecodeError, KeyError) as e:
            if debug:
                print(f"[디버그] JSON 파싱 오류: {e}")
        
        # 여전히 주소를 못 찾았으면 예상 주소 사용
        if not contract_address:
            contract_address = expected_address
            if debug:
                print(f"[디버그] 예상 주소 사용: {contract_address}")
        
        # 주소 유효성 검증
        if not re.match(r'^0x[a-fA-F0-9]{40}$', contract_address):
            raise RuntimeError(f"유효하지 않은 컨트랙트 주소: {contract_address}")
        
        print(f"[성공] {contract_name} 배포 완료: {contract_address}")
        return contract_address
        
    except Exception as e:
        raise e

def create_ityfuzz_config(contract_address, foundry_dir, contract_name):
    """
    ITYfuzz를 위한 오프체인 설정 파일을 생성합니다. (ABI 포함 버전)
    """
    # ABI 파일에서 ABI 정보 읽기
    abi_file_path = Path(foundry_dir) / "out" / f"{contract_name}.sol" / f"{contract_name}.json"
    abi_data = []
    
    if abi_file_path.exists():
        try:
            with open(abi_file_path, 'r') as f:
                contract_json = json.load(f)
                abi_data = contract_json.get("abi", [])
        except Exception as e:
            print(f"[경고] ABI 파일 읽기 실패: {e}")
    
    config = {
        "target": {
            "type": "onchain",
            "address": contract_address,
            "abi": abi_data,  # ABI 직접 포함
            "abi_path": f"out/{contract_name}.sol/{contract_name}.json"
        },
        "rpc_url": f"http://localhost:{ITYFUZZ_CONFIG['port']}",
        "chain_id": ITYFUZZ_CONFIG['chain_id'],
        "deployer": ANVIL_ACCOUNTS[0]["address"],
        "deployer_private_key": ANVIL_ACCOUNTS[0]["private_key"],
        "contracts": {
            contract_address: {
                "abi": abi_data,
                "name": contract_name
            }
        }
    }
    
    config_path = Path(foundry_dir) / "ityfuzz_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def debug_ityfuzz_container(foundry_dir, debug=False):
    """
    ITYfuzz 컨테이너 내부 상태를 디버깅합니다.
    """
    tag = DOCKER_CONFIG['ityfuzz']['tag']
    foundry_abs_path = Path(foundry_dir).absolute()
    results_dir = Path("./ityfuzz_results")
    results_dir.mkdir(exist_ok=True)
    
    # 컨테이너 내부 파일 시스템 확인
    debug_cmd = [
        'docker', 'run', '--rm',
        '--network', 'host',
        '-v', f'{foundry_abs_path}:/project',
        '-v', f'{results_dir.absolute()}:/results',
        '-w', '/project',
        tag,
        'sh', '-c', 'ls -la /project && echo "=== Script directory ===" && ls -la /project/script/ && echo "=== Config file ===" && cat /project/ityfuzz_config.json && echo "=== Out directory ===" && ls -la /project/out/ReentrancyVuln.sol/'
    ]
    
    if debug:
        print(f"[디버그] 컨테이너 내부 확인 명령어: {' '.join(debug_cmd)}")
    
    result = subprocess.run(debug_cmd, capture_output=True, text=True)
    
    if debug:
        print(f"[디버그] 컨테이너 내부 상태:")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
    
    return result.stdout, result.stderr

def run_ityfuzz_fuzzing(contract_address, foundry_dir, contract_name, debug=False):
    """
    배포된 컨트랙트에 대해 ITYfuzz 퍼징을 실행합니다.
    """
    tag = DOCKER_CONFIG['ityfuzz']['tag']
    
    # 결과 디렉토리 생성
    results_dir = Path("./ityfuzz_results")
    results_dir.mkdir(exist_ok=True)
    
    if debug:
        print(f"[디버그] 컨트랙트 이름: {contract_name}")
    
    # 배포 스크립트 생성
    config_path = create_ityfuzz_config(contract_address, foundry_dir, contract_name)
    
    foundry_abs_path = Path(foundry_dir).absolute()
    
    # ITYfuzz 실행 명령어
    ityfuzz_cmd = [
        'docker', 'run', '--rm',
        '-v', f'{foundry_abs_path}:/project',
        '-v', f'{results_dir.absolute()}:/results',
        '-w', '/project',
        tag, 'ityfuzz', 'evm',
        '--target', f'script/Deploy.s.sol:DeployScript',
        '--deployment-script', f'script/Deploy.s.sol:DeployScript',
        '--target-type', 'setup',
        'forge', 'build'
    ]
    
    if debug:
        print(f"[디버그] ITYfuzz 실행 명령어: {' '.join(ityfuzz_cmd)}")
    
    try:
        # 실시간 출력을 위해 capture_output=False로 설정
        result = subprocess.run(
            ityfuzz_cmd,
            capture_output=False,  # 실시간 출력을 위해 False로 설정
            text=True,
            timeout=300
        )
        stdout = ""
        stderr = ""
    except subprocess.TimeoutExpired:
        if debug:
            print("[디버그] ITYfuzz 실행 타임아웃 (300초)")
        stdout = "ITYfuzz가 300초간 실행되었습니다 (타임아웃)"
        stderr = ""
    
    # 임시 파일 정리
    try:
        if config_path.exists():
            config_path.unlink()
    except Exception as e:
        if debug:
            print(f"[디버그] 파일 정리 중 오류: {e}")
    
    return stdout, stderr

def run_ityfuzz(foundry_project_dir, contract_name=None, debug=False):
    """
    ITYfuzz를 사용한 전체 분석 워크플로우
    """
    try:
        # 1. Docker 이미지 준비
        build_docker_image()
        
        # 2. Anvil 블록체인 시작
        start_anvil(debug)
        
        # 3. 컨트랙트 배포
        contract_address = deploy_contract(foundry_project_dir, contract_name, debug)
        
        # 4. 실제 컨트랙트 이름 확인 (None이면 자동 감지된 이름 찾기)
        if not contract_name:
            foundry_dir = Path(foundry_project_dir)
            src_dir = foundry_dir / "src"
            sol_files = list(src_dir.glob("*.sol"))
            if sol_files:
                with open(sol_files[0], 'r') as f:
                    content = f.read()
                    contract_matches = re.findall(r'contract\s+(\w+)', content)
                    if contract_matches:
                        contract_name = contract_matches[0]
        
        if debug:
            print(f"[디버그] 사용할 컨트랙트 이름: {contract_name}")
        
        # 5. ITYfuzz 퍼징 실행
        stdout, stderr = run_ityfuzz_fuzzing(contract_address, foundry_project_dir, contract_name or "Contract", debug)
        
        # 6. 결과 파싱 및 반환
        if stdout and ("vulnerability" in stdout.lower() or "bug" in stdout.lower() or "violation" in stdout.lower() or "exploit" in stdout.lower()):
            return {
                "status": "vulnerability_found",
                "message": "취약점이 발견되었습니다!",
                "details": stdout,
                "contract_address": contract_address
            }
        elif stdout:
            return {
                "status": "completed",
                "message": "분석이 완료되었습니다.",
                "details": stdout,
                "contract_address": contract_address
            }
        elif stderr and "panicked" not in stderr and stderr.strip():
            return {
                "status": "completed",
                "message": "분석이 완료되었습니다.",
                "details": stderr,
                "contract_address": contract_address
            }
        else:
            return {
                "status": "completed",
                "message": "분석이 완료되었습니다. 특별한 이슈가 발견되지 않았습니다.",
                "details": "",
                "contract_address": contract_address
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"ITYfuzz 실행 중 오류 발생: {str(e)}",
            "details": str(e),
            "contract_address": None
        }
    
    finally:
        # 7. 인프라 정리
        stop_anvil()