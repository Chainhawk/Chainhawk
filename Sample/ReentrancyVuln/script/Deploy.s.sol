// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Script.sol";
import "../src/ReentrancyVuln.sol";

contract DeployScript is Script {
    ReentrancyVuln public target;
    
    function setUp() public {
        // 순수하게 취약한 컨트랙트만 배포
        target = new ReentrancyVuln();
        
        // 초기 자금 제공 (테스트를 위해)
        target.deposit{value: 1 ether}();
    }
    
    function run() external {
        // broadcast 없이 단순 배포
        if (address(target) == address(0)) {
            target = new ReentrancyVuln();
            target.deposit{value: 1 ether}();
        }
    }
    
    // ITYfuzz가 이 함수들을 호출하면서 자동으로 취약점 발견해야 함
    function testDeposit() public payable {
        // 단순히 deposit만 호출 - 공격 코드 없음
        if (msg.value > 0) {
            target.deposit{value: msg.value}();
        }
    }
    
    function testWithdraw(uint256 amount) public {
        // 단순히 withdraw만 호출 - 공격 코드 없음
        if (amount > 0) {
            target.withdraw(amount);
        }
    }
    
    function testBalance() public view returns (uint256) {
        return target.balances(address(this));
    }
    
    function testContractBalance() public view returns (uint256) {
        return address(target).balance;
    }
    
    // 이 함수에는 공격 코드가 없음 - ITYfuzz가 알아서 발견해야 함
    function testMultipleWithdraws() public {
        uint256 balance = target.balances(address(this));
        if (balance > 0) {
            target.withdraw(balance);
        }
    }
}