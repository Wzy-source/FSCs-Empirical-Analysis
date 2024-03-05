// SPDX-License-Identifier: MIT
pragma solidity 0.6.8;


contract Greeter {
    string private greeting;
    constructor(string memory gre) public {
        greeting = gre;
    }
}

contract Bank {
    //地址=>余额
    mapping(address => uint) balance;
    address public  owner;
    Greeter[] public greeterArray;

    constructor() public {
        owner = msg.sender;
    }
    //充值
    function deposit() public payable {
        balance[msg.sender] += msg.value;
    }
    //提款msg.sender的全部ether
    function withdraw() public {
        require(balance[msg.sender] > 0);
        //这里具有重入攻击的风险
//        (bool success,) = msg.sender.call{value: balance[msg.sender]}("");
//        require(success);
        balance[msg.sender] = 0;
    }
    //获取本合约的余额
    function getBalance() public view returns (uint){
        return address(this).balance;
    }

    function createGreeterByNew(string memory _greeting) public {
        Greeter greet = new Greeter(_greeting);
        greeterArray.push(greet);
    }

    function createGreeterByEVMCreate(bytes memory bytecode) public {
        address addr;
        bytes32 loadedcode;
        assembly {
            loadedcode := mload(bytecode)
            addr := create(0, add(bytecode, 0x20), loadedcode)
        }
    }

    function createGreeterByEVMCreate2(bytes32 salt, bytes memory bytecode) public {
        address addr;
        bytes32 loadedcode;
        assembly {
            loadedcode := mload(bytecode)
            addr := create2(0, add(bytecode, 0x20), loadedcode, salt)
        }
    }
}

