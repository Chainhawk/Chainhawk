// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReentrancyVuln {
    mapping(address => uint) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint _amount) public {
        require(balances[msg.sender] >= _amount, "balances lack");
        (bool sent, ) = msg.sender.call{value: _amount}("");
        require(sent, "transfer fail");
        balances[msg.sender] -= _amount;
    }
} 