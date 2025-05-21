// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UncheckedCall {
    function sendEther(address payable _to) public payable {
        // call의 반환값을 체크하지 않음 (취약)
        _to.call{value: msg.value}("");
    }
} 