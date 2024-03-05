// SPDX-License-Identifier: MIT
pragma solidity ^0.6.1;
contract Greeter2 {
    string private greeting;
    constructor(string memory gre) public {
        greeting = gre;
    }
}
