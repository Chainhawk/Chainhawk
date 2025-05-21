// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReentrancyVuln {
    mapping(address => uint) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint _amount) public {
        require(balances[msg.sender] >= _amount, "잔액 부족");
        (bool sent, ) = msg.sender.call{value: _amount}("");
        require(sent, "전송 실패");
        balances[msg.sender] -= _amount;
    }
} 