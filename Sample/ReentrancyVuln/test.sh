#!/bin/bash

echo "=== 리엔트런시 취약점 ITYfuzz 테스트 ==="

cd ~/Works/Project/Chainhawk/Sample/ReentrancyVuln


# 2. 컴파일 테스트
echo -e "\n=== 2. 컴파일 테스트 ==="
docker run --rm \
  -v $(pwd):/project \
  -w /project \
  chainhawk-ityfuzz forge build

if [ $? -eq 0 ]; then
    echo "✅ 컴파일 성공"
else
    echo "❌ 컴파일 실패"
    exit 1
fi

# 3. ITYfuzz 실행 (30초)
echo -e "\n=== 3. ITYfuzz 리엔트런시 취약점 탐지 (30초) ==="
timeout 30 docker run --rm \
  -v $(pwd):/project \
  -w /project \
  chainhawk-ityfuzz ityfuzz evm \
  --target script/Deploy.s.sol:DeployScript \
  --deployment-script script/Deploy.s.sol:DeployScript \
  --target-type setup \
  forge build

# echo -e "\n=== 4. 온체인 모드 테스트 (30초) ==="
# timeout 30 docker run --rm --network host \
#   -v $(pwd):/project \
#   -w /project \
#   chainhawk-ityfuzz ityfuzz evm \
#   --target script/Deploy.s.sol:DeployScript \
#   --deployment-script script/Deploy.s.sol:DeployScript \
#   --target-type setup \
#   --chain-type local \
#   --onchain-url http://localhost:8545 \
#   --onchain-chain-id 31337 \
#   forge build


echo -e "\n=== 🎯 테스트 완료! ==="
echo "ITYfuzz가 리엔트런시 취약점을 찾았는지 로그를 확인하세요:"
echo "- 'ReentrancyVuln' 컨트랙트가 커버리지에 나타나는지"
echo "- 'testReentrancyAttack' 또는 'receive' 함수에서 취약점 발견했는지"
echo "- 재귀 호출이나 무한 루프 관련 경고가 있는지"