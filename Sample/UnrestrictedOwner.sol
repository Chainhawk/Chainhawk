// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UnrestrictedOwner {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function changeOwner(address _newOwner) public {
        owner = _newOwner; // 접근제어 없음: 누구나 오너 변경 가능
    }
} 