pragma solidity 0.8.21;

//import { IPuzzle } from "curta/src/interfaces/IPuzzle.sol";
//import { LibClone } from "solady/src/utils/LibClone.sol";


/// @title The interface for a puzzle on Curta
/// @notice The goal of players is to view the source code of the puzzle (may
/// range from just the bytecode to Solidity—whatever the author wishes to
/// provide), interpret the code, solve it as if it was a regular puzzle, then
/// verify the solution on-chain.
/// @dev Since puzzles are on-chain, everyone can view everyone else's
/// submissions. The generative aspect prevents front-running and allows for
/// multiple winners: even if players view someone else's solution, they still
/// have to figure out what the rules/constraints of the puzzle are and apply
/// the solution to their respective starting position.


/// @notice Minimal proxy library.
/// @author Solady (https://github.com/vectorized/solady/blob/main/src/utils/LibClone.sol)
/// @author Minimal proxy by 0age (https://github.com/0age)
/// @author Clones with immutable args by wighawag, zefram.eth, Saw-mon & Natalie
/// (https://github.com/Saw-mon-and-Natalie/clones-with-immutable-args)
///
/// @dev Minimal proxy:
/// Although the sw0nt pattern saves 5 gas over the erc-1167 pattern during runtime,
/// it is not supported out-of-the-box on Etherscan. Hence, we choose to use the 0age pattern,
/// which saves 4 gas over the erc-1167 pattern during runtime, and has the smallest bytecode.
///
/// @dev Minimal proxy (PUSH0 variant):
/// This is a new minimal proxy that uses the PUSH0 opcode introduced during Shanghai.
/// It is optimized first for minimal runtime gas, then for minimal bytecode.
/// The PUSH0 clone functions are intentionally postfixed with a jarring "_PUSH0" as
/// many EVM chains may not support the PUSH0 opcode in the early months after Shanghai.
/// Please use with caution.
///
/// @dev Clones with immutable args (CWIA):
/// The implementation of CWIA here implements a `receive()` method that emits the
/// `ReceiveETH(uint256)` event. This skips the `DELEGATECALL` when there is no calldata,
/// enabling us to accept hard gas-capped `sends` & `transfers` for maximum backwards
/// composability. The minimal proxy implementation does not offer this feature.
library LibClone {
    /*´:°•.°+.*•´.*:˚.°*.˚•´.°:°•.°•.*•´.*:˚.°*.˚•´.°:°•.°+.*•´.*:*/
    /*                       CUSTOM ERRORS                        */
    /*.•°:°.´+˚.*°.˚:*.´•*.+°.•°:´*.´•*.•°.•°:°.´:•˚°.*°.˚:*.´+°.•*/

    /// @dev Unable to deploy the clone.
    error DeploymentFailed();

    /// @dev The salt must start with either the zero address or the caller.
    error SaltDoesNotStartWithCaller();

    /*´:°•.°+.*•´.*:˚.°*.˚•´.°:°•.°•.*•´.*:˚.°*.˚•´.°:°•.°+.*•´.*:*/
    /*                  MINIMAL PROXY OPERATIONS                  */
    /*.•°:°.´+˚.*°.˚:*.´•*.+°.•°:´*.´•*.•°.•°:°.´:•˚°.*°.˚:*.´+°.•*/

    /// @dev Deploys a clone of `implementation`.
    function clone(address implementation) internal returns (address instance) {
        /// @solidity memory-safe-assembly
        assembly {
        /**
         * --------------------------------------------------------------------------+
         * CREATION (9 bytes)                                                        |
         * --------------------------------------------------------------------------|
         * Opcode     | Mnemonic          | Stack     | Memory                       |
         * --------------------------------------------------------------------------|
         * 60 runSize | PUSH1 runSize     | r         |                              |
         * 3d         | RETURNDATASIZE    | 0 r       |                              |
         * 81         | DUP2              | r 0 r     |                              |
         * 60 offset  | PUSH1 offset      | o r 0 r   |                              |
         * 3d         | RETURNDATASIZE    | 0 o r 0 r |                              |
         * 39         | CODECOPY          | 0 r       | [0..runSize): runtime code   |
         * f3         | RETURN            |           | [0..runSize): runtime code   |
         * --------------------------------------------------------------------------|
         * RUNTIME (44 bytes)                                                        |
         * --------------------------------------------------------------------------|
         * Opcode  | Mnemonic       | Stack                  | Memory                |
         * --------------------------------------------------------------------------|
         *                                                                           |
         * ::: keep some values in stack ::::::::::::::::::::::::::::::::::::::::::: |
         * 3d      | RETURNDATASIZE | 0                      |                       |
         * 3d      | RETURNDATASIZE | 0 0                    |                       |
         * 3d      | RETURNDATASIZE | 0 0 0                  |                       |
         * 3d      | RETURNDATASIZE | 0 0 0 0                |                       |
         *                                                                           |
         * ::: copy calldata to memory ::::::::::::::::::::::::::::::::::::::::::::: |
         * 36      | CALLDATASIZE   | cds 0 0 0 0            |                       |
         * 3d      | RETURNDATASIZE | 0 cds 0 0 0 0          |                       |
         * 3d      | RETURNDATASIZE | 0 0 cds 0 0 0 0        |                       |
         * 37      | CALLDATACOPY   | 0 0 0 0                | [0..cds): calldata    |
         *                                                                           |
         * ::: delegate call to the implementation contract :::::::::::::::::::::::: |
         * 36      | CALLDATASIZE   | cds 0 0 0 0            | [0..cds): calldata    |
         * 3d      | RETURNDATASIZE | 0 cds 0 0 0 0          | [0..cds): calldata    |
         * 73 addr | PUSH20 addr    | addr 0 cds 0 0 0 0     | [0..cds): calldata    |
         * 5a      | GAS            | gas addr 0 cds 0 0 0 0 | [0..cds): calldata    |
         * f4      | DELEGATECALL   | success 0 0            | [0..cds): calldata    |
         *                                                                           |
         * ::: copy return data to memory :::::::::::::::::::::::::::::::::::::::::: |
         * 3d      | RETURNDATASIZE | rds success 0 0        | [0..cds): calldata    |
         * 3d      | RETURNDATASIZE | rds rds success 0 0    | [0..cds): calldata    |
         * 93      | SWAP4          | 0 rds success 0 rds    | [0..cds): calldata    |
         * 80      | DUP1           | 0 0 rds success 0 rds  | [0..cds): calldata    |
         * 3e      | RETURNDATACOPY | success 0 rds          | [0..rds): returndata  |
         *                                                                           |
         * 60 0x2a | PUSH1 0x2a     | 0x2a success 0 rds     | [0..rds): returndata  |
         * 57      | JUMPI          | 0 rds                  | [0..rds): returndata  |
         *                                                                           |
         * ::: revert :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * fd      | REVERT         |                        | [0..rds): returndata  |
         *                                                                           |
         * ::: return :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 5b      | JUMPDEST       | 0 rds                  | [0..rds): returndata  |
         * f3      | RETURN         |                        | [0..rds): returndata  |
         * --------------------------------------------------------------------------+
         */

            mstore(0x21, 0x5af43d3d93803e602a57fd5bf3)
            mstore(0x14, implementation)
            mstore(0x00, 0x602c3d8160093d39f33d3d3d3d363d3d37363d73)
            instance := create(0, 0x0c, 0x35)
        // If `instance` is zero, revert.
            if iszero(instance) {
            // Store the function selector of `DeploymentFailed()`.
                mstore(0x00, 0x30116425)
            // Revert with (offset, size).
                revert(0x1c, 0x04)
            }
        // Restore the part of the free memory pointer that has been overwritten.
            mstore(0x21, 0)
        }
    }

    /// @dev Deploys a deterministic clone of `implementation` with `salt`.
    function cloneDeterministic(address implementation, bytes32 salt)
    internal
    returns (address instance)
    {
        /// @solidity memory-safe-assembly
        assembly {
            mstore(0x21, 0x5af43d3d93803e602a57fd5bf3)
            mstore(0x14, implementation)
            mstore(0x00, 0x602c3d8160093d39f33d3d3d3d363d3d37363d73)
            instance := create2(0, 0x0c, 0x35, salt)
        // If `instance` is zero, revert.
            if iszero(instance) {
            // Store the function selector of `DeploymentFailed()`.
                mstore(0x00, 0x30116425)
            // Revert with (offset, size).
                revert(0x1c, 0x04)
            }
        // Restore the part of the free memory pointer that has been overwritten.
            mstore(0x21, 0)
        }
    }

    /// @dev Returns the initialization code hash of the clone of `implementation`.
    /// Used for mining vanity addresses with create2crunch.
    function initCodeHash(address implementation) internal pure returns (bytes32 hash) {
        /// @solidity memory-safe-assembly
        assembly {
            mstore(0x21, 0x5af43d3d93803e602a57fd5bf3)
            mstore(0x14, implementation)
            mstore(0x00, 0x602c3d8160093d39f33d3d3d3d363d3d37363d73)
            hash := keccak256(0x0c, 0x35)
        // Restore the part of the free memory pointer that has been overwritten.
            mstore(0x21, 0)
        }
    }

    /// @dev Returns the address of the deterministic clone of `implementation`,
    /// with `salt` by `deployer`.
    /// Note: The returned result has dirty upper 96 bits. Please clean if used in assembly.
    function predictDeterministicAddress(address implementation, bytes32 salt, address deployer)
    internal
    pure
    returns (address predicted)
    {
        bytes32 hash = initCodeHash(implementation);
        predicted = predictDeterministicAddress(hash, salt, deployer);
    }

    /*´:°•.°+.*•´.*:˚.°*.˚•´.°:°•.°•.*•´.*:˚.°*.˚•´.°:°•.°+.*•´.*:*/
    /*          MINIMAL PROXY OPERATIONS (PUSH0 VARIANT)          */
    /*.•°:°.´+˚.*°.˚:*.´•*.+°.•°:´*.´•*.•°.•°:°.´:•˚°.*°.˚:*.´+°.•*/

    /// @dev Deploys a PUSH0 clone of `implementation`.
    function clone_PUSH0(address implementation) internal returns (address instance) {
        /// @solidity memory-safe-assembly
        assembly {
        /**
         * --------------------------------------------------------------------------+
         * CREATION (9 bytes)                                                        |
         * --------------------------------------------------------------------------|
         * Opcode     | Mnemonic          | Stack     | Memory                       |
         * --------------------------------------------------------------------------|
         * 60 runSize | PUSH1 runSize     | r         |                              |
         * 5f         | PUSH0             | 0 r       |                              |
         * 81         | DUP2              | r 0 r     |                              |
         * 60 offset  | PUSH1 offset      | o r 0 r   |                              |
         * 5f         | PUSH0             | 0 o r 0 r |                              |
         * 39         | CODECOPY          | 0 r       | [0..runSize): runtime code   |
         * f3         | RETURN            |           | [0..runSize): runtime code   |
         * --------------------------------------------------------------------------|
         * RUNTIME (45 bytes)                                                        |
         * --------------------------------------------------------------------------|
         * Opcode  | Mnemonic       | Stack                  | Memory                |
         * --------------------------------------------------------------------------|
         *                                                                           |
         * ::: keep some values in stack ::::::::::::::::::::::::::::::::::::::::::: |
         * 5f      | PUSH0          | 0                      |                       |
         * 5f      | PUSH0          | 0 0                    |                       |
         *                                                                           |
         * ::: copy calldata to memory ::::::::::::::::::::::::::::::::::::::::::::: |
         * 36      | CALLDATASIZE   | cds 0 0                |                       |
         * 5f      | PUSH0          | 0 cds 0 0              |                       |
         * 5f      | PUSH0          | 0 0 cds 0 0            |                       |
         * 37      | CALLDATACOPY   | 0 0                    | [0..cds): calldata    |
         *                                                                           |
         * ::: delegate call to the implementation contract :::::::::::::::::::::::: |
         * 36      | CALLDATASIZE   | cds 0 0                | [0..cds): calldata    |
         * 5f      | PUSH0          | 0 cds 0 0              | [0..cds): calldata    |
         * 73 addr | PUSH20 addr    | addr 0 cds 0 0         | [0..cds): calldata    |
         * 5a      | GAS            | gas addr 0 cds 0 0     | [0..cds): calldata    |
         * f4      | DELEGATECALL   | success                | [0..cds): calldata    |
         *                                                                           |
         * ::: copy return data to memory :::::::::::::::::::::::::::::::::::::::::: |
         * 3d      | RETURNDATASIZE | rds success            | [0..cds): calldata    |
         * 5f      | PUSH0          | 0 rds success          | [0..cds): calldata    |
         * 5f      | PUSH0          | 0 0 rds success        | [0..cds): calldata    |
         * 3e      | RETURNDATACOPY | success                | [0..rds): returndata  |
         *                                                                           |
         * 60 0x29 | PUSH1 0x29     | 0x29 success           | [0..rds): returndata  |
         * 57      | JUMPI          |                        | [0..rds): returndata  |
         *                                                                           |
         * ::: revert :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 3d      | RETURNDATASIZE | rds                    | [0..rds): returndata  |
         * 5f      | PUSH0          | 0 rds                  | [0..rds): returndata  |
         * fd      | REVERT         |                        | [0..rds): returndata  |
         *                                                                           |
         * ::: return :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 5b      | JUMPDEST       |                        | [0..rds): returndata  |
         * 3d      | RETURNDATASIZE | rds                    | [0..rds): returndata  |
         * 5f      | PUSH0          | 0 rds                  | [0..rds): returndata  |
         * f3      | RETURN         |                        | [0..rds): returndata  |
         * --------------------------------------------------------------------------+
         */

            mstore(0x24, 0x5af43d5f5f3e6029573d5ffd5b3d5ff3) // 16
            mstore(0x14, implementation) // 20
            mstore(0x00, 0x602d5f8160095f39f35f5f365f5f37365f73) // 9 + 9
            instance := create(0, 0x0e, 0x36)
        // If `instance` is zero, revert.
            if iszero(instance) {
            // Store the function selector of `DeploymentFailed()`.
                mstore(0x00, 0x30116425)
            // Revert with (offset, size).
                revert(0x1c, 0x04)
            }
        // Restore the part of the free memory pointer that has been overwritten.
            mstore(0x24, 0)
        }
    }

    /// @dev Deploys a deterministic PUSH0 clone of `implementation` with `salt`.
    function cloneDeterministic_PUSH0(address implementation, bytes32 salt)
    internal
    returns (address instance)
    {
        /// @solidity memory-safe-assembly
        assembly {
            mstore(0x24, 0x5af43d5f5f3e6029573d5ffd5b3d5ff3) // 16
            mstore(0x14, implementation) // 20
            mstore(0x00, 0x602d5f8160095f39f35f5f365f5f37365f73) // 9 + 9
            instance := create2(0, 0x0e, 0x36, salt)
        // If `instance` is zero, revert.
            if iszero(instance) {
            // Store the function selector of `DeploymentFailed()`.
                mstore(0x00, 0x30116425)
            // Revert with (offset, size).
                revert(0x1c, 0x04)
            }
        // Restore the part of the free memory pointer that has been overwritten.
            mstore(0x24, 0)
        }
    }

    /// @dev Returns the initialization code hash of the PUSH0 clone of `implementation`.
    /// Used for mining vanity addresses with create2crunch.
    function initCodeHash_PUSH0(address implementation) internal pure returns (bytes32 hash) {
        /// @solidity memory-safe-assembly
        assembly {
            mstore(0x24, 0x5af43d5f5f3e6029573d5ffd5b3d5ff3) // 16
            mstore(0x14, implementation) // 20
            mstore(0x00, 0x602d5f8160095f39f35f5f365f5f37365f73) // 9 + 9
            hash := keccak256(0x0e, 0x36)
        // Restore the part of the free memory pointer that has been overwritten.
            mstore(0x24, 0)
        }
    }

    /// @dev Returns the address of the deterministic PUSH0 clone of `implementation`,
    /// with `salt` by `deployer`.
    /// Note: The returned result has dirty upper 96 bits. Please clean if used in assembly.
    function predictDeterministicAddress_PUSH0(
        address implementation,
        bytes32 salt,
        address deployer
    ) internal pure returns (address predicted) {
        bytes32 hash = initCodeHash_PUSH0(implementation);
        predicted = predictDeterministicAddress(hash, salt, deployer);
    }

    /*´:°•.°+.*•´.*:˚.°*.˚•´.°:°•.°•.*•´.*:˚.°*.˚•´.°:°•.°+.*•´.*:*/
    /*           CLONES WITH IMMUTABLE ARGS OPERATIONS            */
    /*.•°:°.´+˚.*°.˚:*.´•*.+°.•°:´*.´•*.•°.•°:°.´:•˚°.*°.˚:*.´+°.•*/

    /// @dev Deploys a minimal proxy with `implementation`,
    /// using immutable arguments encoded in `data`.
    ///
    /// Note: This implementation of CWIA differs from the original implementation.
    /// If the calldata is empty, it will emit a `ReceiveETH(uint256)` event and skip the `DELEGATECALL`.
    function clone(address implementation, bytes memory data) internal returns (address instance) {
        assembly {
        // Compute the boundaries of the data and cache the memory slots around it.
            let mBefore3 := mload(sub(data, 0x60))
            let mBefore2 := mload(sub(data, 0x40))
            let mBefore1 := mload(sub(data, 0x20))
            let dataLength := mload(data)
            let dataEnd := add(add(data, 0x20), dataLength)
            let mAfter1 := mload(dataEnd)

        // +2 bytes for telling how much data there is appended to the call.
            let extraLength := add(dataLength, 2)
        // The `creationSize` is `extraLength + 108`
        // The `runSize` is `creationSize - 10`.

        /**
         * ---------------------------------------------------------------------------------------------------+
         * CREATION (10 bytes)                                                                                |
         * ---------------------------------------------------------------------------------------------------|
         * Opcode     | Mnemonic          | Stack     | Memory                                                |
         * ---------------------------------------------------------------------------------------------------|
         * 61 runSize | PUSH2 runSize     | r         |                                                       |
         * 3d         | RETURNDATASIZE    | 0 r       |                                                       |
         * 81         | DUP2              | r 0 r     |                                                       |
         * 60 offset  | PUSH1 offset      | o r 0 r   |                                                       |
         * 3d         | RETURNDATASIZE    | 0 o r 0 r |                                                       |
         * 39         | CODECOPY          | 0 r       | [0..runSize): runtime code                            |
         * f3         | RETURN            |           | [0..runSize): runtime code                            |
         * ---------------------------------------------------------------------------------------------------|
         * RUNTIME (98 bytes + extraLength)                                                                   |
         * ---------------------------------------------------------------------------------------------------|
         * Opcode   | Mnemonic       | Stack                    | Memory                                      |
         * ---------------------------------------------------------------------------------------------------|
         *                                                                                                    |
         * ::: if no calldata, emit event & return w/o `DELEGATECALL` ::::::::::::::::::::::::::::::::::::::: |
         * 36       | CALLDATASIZE   | cds                      |                                             |
         * 60 0x2c  | PUSH1 0x2c     | 0x2c cds                 |                                             |
         * 57       | JUMPI          |                          |                                             |
         * 34       | CALLVALUE      | cv                       |                                             |
         * 3d       | RETURNDATASIZE | 0 cv                     |                                             |
         * 52       | MSTORE         |                          | [0..0x20): callvalue                        |
         * 7f sig   | PUSH32 0x9e..  | sig                      | [0..0x20): callvalue                        |
         * 59       | MSIZE          | 0x20 sig                 | [0..0x20): callvalue                        |
         * 3d       | RETURNDATASIZE | 0 0x20 sig               | [0..0x20): callvalue                        |
         * a1       | LOG1           |                          | [0..0x20): callvalue                        |
         * 00       | STOP           |                          | [0..0x20): callvalue                        |
         * 5b       | JUMPDEST       |                          |                                             |
         *                                                                                                    |
         * ::: copy calldata to memory :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 36       | CALLDATASIZE   | cds                      |                                             |
         * 3d       | RETURNDATASIZE | 0 cds                    |                                             |
         * 3d       | RETURNDATASIZE | 0 0 cds                  |                                             |
         * 37       | CALLDATACOPY   |                          | [0..cds): calldata                          |
         *                                                                                                    |
         * ::: keep some values in stack :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 3d       | RETURNDATASIZE | 0                        | [0..cds): calldata                          |
         * 3d       | RETURNDATASIZE | 0 0                      | [0..cds): calldata                          |
         * 3d       | RETURNDATASIZE | 0 0 0                    | [0..cds): calldata                          |
         * 3d       | RETURNDATASIZE | 0 0 0 0                  | [0..cds): calldata                          |
         * 61 extra | PUSH2 extra    | e 0 0 0 0                | [0..cds): calldata                          |
         *                                                                                                    |
         * ::: copy extra data to memory :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 80       | DUP1           | e e 0 0 0 0              | [0..cds): calldata                          |
         * 60 0x62  | PUSH1 0x62     | 0x62 e e 0 0 0 0         | [0..cds): calldata                          |
         * 36       | CALLDATASIZE   | cds 0x62 e e 0 0 0 0     | [0..cds): calldata                          |
         * 39       | CODECOPY       | e 0 0 0 0                | [0..cds): calldata, [cds..cds+e): extraData |
         *                                                                                                    |
         * ::: delegate call to the implementation contract ::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 36       | CALLDATASIZE   | cds e 0 0 0 0            | [0..cds): calldata, [cds..cds+e): extraData |
         * 01       | ADD            | cds+e 0 0 0 0            | [0..cds): calldata, [cds..cds+e): extraData |
         * 3d       | RETURNDATASIZE | 0 cds+e 0 0 0 0          | [0..cds): calldata, [cds..cds+e): extraData |
         * 73 addr  | PUSH20 addr    | addr 0 cds+e 0 0 0 0     | [0..cds): calldata, [cds..cds+e): extraData |
         * 5a       | GAS            | gas addr 0 cds+e 0 0 0 0 | [0..cds): calldata, [cds..cds+e): extraData |
         * f4       | DELEGATECALL   | success 0 0              | [0..cds): calldata, [cds..cds+e): extraData |
         *                                                                                                    |
         * ::: copy return data to memory ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 3d       | RETURNDATASIZE | rds success 0 0          | [0..cds): calldata, [cds..cds+e): extraData |
         * 3d       | RETURNDATASIZE | rds rds success 0 0      | [0..cds): calldata, [cds..cds+e): extraData |
         * 93       | SWAP4          | 0 rds success 0 rds      | [0..cds): calldata, [cds..cds+e): extraData |
         * 80       | DUP1           | 0 0 rds success 0 rds    | [0..cds): calldata, [cds..cds+e): extraData |
         * 3e       | RETURNDATACOPY | success 0 rds            | [0..rds): returndata                        |
         *                                                                                                    |
         * 60 0x60  | PUSH1 0x60     | 0x60 success 0 rds       | [0..rds): returndata                        |
         * 57       | JUMPI          | 0 rds                    | [0..rds): returndata                        |
         *                                                                                                    |
         * ::: revert ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * fd       | REVERT         |                          | [0..rds): returndata                        |
         *                                                                                                    |
         * ::: return ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::: |
         * 5b       | JUMPDEST       | 0 rds                    | [0..rds): returndata                        |
         * f3       | RETURN         |                          | [0..rds): returndata                        |
         * ---------------------------------------------------------------------------------------------------+
         */
        // Write the bytecode before the data.
            mstore(data, 0x5af43d3d93803e606057fd5bf3)
        // Write the address of the implementation.
            mstore(sub(data, 0x0d), implementation)
        // Write the rest of the bytecode.
            mstore(
                sub(data, 0x21),
                or(shl(0x48, extraLength), 0x593da1005b363d3d373d3d3d3d610000806062363936013d73)
            )
        // `keccak256("ReceiveETH(uint256)")`
            mstore(
                sub(data, 0x3a), 0x9e4ac34f21c619cefc926c8bd93b54bf5a39c7ab2127a895af1cc0691d7e3dff
            )
            mstore(
            // Do a out-of-gas revert if `extraLength` is too big. 0xffff - 0x62 + 0x01 = 0xff9e.
            // The actual EVM limit may be smaller and may change over time.
                sub(data, add(0x59, lt(extraLength, 0xff9e))),
                or(shl(0x78, add(extraLength, 0x62)), 0xfd6100003d81600a3d39f336602c57343d527f)
            )
            mstore(dataEnd, shl(0xf0, extraLength))

        // Create the instance.
            instance := create(0, sub(data, 0x4c), add(extraLength, 0x6c))

        // If `instance` is zero, revert.
            if iszero(instance) {
            // Store the function selector of `DeploymentFailed()`.
                mstore(0x00, 0x30116425)
            // Revert with (offset, size).
                revert(0x1c, 0x04)
            }

        // Restore the overwritten memory surrounding `data`.
            mstore(dataEnd, mAfter1)
            mstore(data, dataLength)
            mstore(sub(data, 0x20), mBefore1)
            mstore(sub(data, 0x40), mBefore2)
            mstore(sub(data, 0x60), mBefore3)
        }
    }

    /// @dev Deploys a deterministic clone of `implementation`,
    /// using immutable arguments encoded in `data`, with `salt`.
    ///
    /// Note: This implementation of CWIA differs from the original implementation.
    /// If the calldata is empty, it will emit a `ReceiveETH(uint256)` event and skip the `DELEGATECALL`.
    function cloneDeterministic(address implementation, bytes memory data, bytes32 salt)
    internal
    returns (address instance)
    {
        assembly {
        // Compute the boundaries of the data and cache the memory slots around it.
            let mBefore3 := mload(sub(data, 0x60))
            let mBefore2 := mload(sub(data, 0x40))
            let mBefore1 := mload(sub(data, 0x20))
            let dataLength := mload(data)
            let dataEnd := add(add(data, 0x20), dataLength)
            let mAfter1 := mload(dataEnd)

        // +2 bytes for telling how much data there is appended to the call.
            let extraLength := add(dataLength, 2)

        // Write the bytecode before the data.
            mstore(data, 0x5af43d3d93803e606057fd5bf3)
        // Write the address of the implementation.
            mstore(sub(data, 0x0d), implementation)
        // Write the rest of the bytecode.
            mstore(
                sub(data, 0x21),
                or(shl(0x48, extraLength), 0x593da1005b363d3d373d3d3d3d610000806062363936013d73)
            )
        // `keccak256("ReceiveETH(uint256)")`
            mstore(
                sub(data, 0x3a), 0x9e4ac34f21c619cefc926c8bd93b54bf5a39c7ab2127a895af1cc0691d7e3dff
            )
            mstore(
            // Do a out-of-gas revert if `extraLength` is too big. 0xffff - 0x62 + 0x01 = 0xff9e.
            // The actual EVM limit may be smaller and may change over time.
                sub(data, add(0x59, lt(extraLength, 0xff9e))),
                or(shl(0x78, add(extraLength, 0x62)), 0xfd6100003d81600a3d39f336602c57343d527f)
            )
            mstore(dataEnd, shl(0xf0, extraLength))

        // Create the instance.
            instance := create2(0, sub(data, 0x4c), add(extraLength, 0x6c), salt)

        // If `instance` is zero, revert.
            if iszero(instance) {
            // Store the function selector of `DeploymentFailed()`.
                mstore(0x00, 0x30116425)
            // Revert with (offset, size).
                revert(0x1c, 0x04)
            }

        // Restore the overwritten memory surrounding `data`.
            mstore(dataEnd, mAfter1)
            mstore(data, dataLength)
            mstore(sub(data, 0x20), mBefore1)
            mstore(sub(data, 0x40), mBefore2)
            mstore(sub(data, 0x60), mBefore3)
        }
    }

    /// @dev Returns the initialization code hash of the clone of `implementation`
    /// using immutable arguments encoded in `data`.
    /// Used for mining vanity addresses with create2crunch.
    function initCodeHash(address implementation, bytes memory data)
    internal
    pure
    returns (bytes32 hash)
    {
        assembly {
        // Compute the boundaries of the data and cache the memory slots around it.
            let mBefore3 := mload(sub(data, 0x60))
            let mBefore2 := mload(sub(data, 0x40))
            let mBefore1 := mload(sub(data, 0x20))
            let dataLength := mload(data)
            let dataEnd := add(add(data, 0x20), dataLength)
            let mAfter1 := mload(dataEnd)

        // Do a out-of-gas revert if `dataLength` is too big. 0xffff - 0x02 - 0x62 = 0xff9b.
        // The actual EVM limit may be smaller and may change over time.
            returndatacopy(returndatasize(), returndatasize(), gt(dataLength, 0xff9b))

        // +2 bytes for telling how much data there is appended to the call.
            let extraLength := add(dataLength, 2)

        // Write the bytecode before the data.
            mstore(data, 0x5af43d3d93803e606057fd5bf3)
        // Write the address of the implementation.
            mstore(sub(data, 0x0d), implementation)
        // Write the rest of the bytecode.
            mstore(
                sub(data, 0x21),
                or(shl(0x48, extraLength), 0x593da1005b363d3d373d3d3d3d610000806062363936013d73)
            )
        // `keccak256("ReceiveETH(uint256)")`
            mstore(
                sub(data, 0x3a), 0x9e4ac34f21c619cefc926c8bd93b54bf5a39c7ab2127a895af1cc0691d7e3dff
            )
            mstore(
                sub(data, 0x5a),
                or(shl(0x78, add(extraLength, 0x62)), 0x6100003d81600a3d39f336602c57343d527f)
            )
            mstore(dataEnd, shl(0xf0, extraLength))

        // Compute and store the bytecode hash.
            hash := keccak256(sub(data, 0x4c), add(extraLength, 0x6c))

        // Restore the overwritten memory surrounding `data`.
            mstore(dataEnd, mAfter1)
            mstore(data, dataLength)
            mstore(sub(data, 0x20), mBefore1)
            mstore(sub(data, 0x40), mBefore2)
            mstore(sub(data, 0x60), mBefore3)
        }
    }

    /// @dev Returns the address of the deterministic clone of
    /// `implementation` using immutable arguments encoded in `data`, with `salt`, by `deployer`.
    /// Note: The returned result has dirty upper 96 bits. Please clean if used in assembly.
    function predictDeterministicAddress(
        address implementation,
        bytes memory data,
        bytes32 salt,
        address deployer
    ) internal pure returns (address predicted) {
        bytes32 hash = initCodeHash(implementation, data);
        predicted = predictDeterministicAddress(hash, salt, deployer);
    }

    /*´:°•.°+.*•´.*:˚.°*.˚•´.°:°•.°•.*•´.*:˚.°*.˚•´.°:°•.°+.*•´.*:*/
    /*                      OTHER OPERATIONS                      */
    /*.•°:°.´+˚.*°.˚:*.´•*.+°.•°:´*.´•*.•°.•°:°.´:•˚°.*°.˚:*.´+°.•*/

    /// @dev Returns the address when a contract with initialization code hash,
    /// `hash`, is deployed with `salt`, by `deployer`.
    /// Note: The returned result has dirty upper 96 bits. Please clean if used in assembly.
    function predictDeterministicAddress(bytes32 hash, bytes32 salt, address deployer)
    internal
    pure
    returns (address predicted)
    {
        /// @solidity memory-safe-assembly
        assembly {
        // Compute and store the bytecode hash.
            mstore8(0x00, 0xff) // Write the prefix.
            mstore(0x35, hash)
            mstore(0x01, shl(96, deployer))
            mstore(0x15, salt)
            predicted := keccak256(0x00, 0x55)
        // Restore the part of the free memory pointer that has been overwritten.
            mstore(0x35, 0)
        }
    }

    /// @dev Reverts if `salt` does not start with either the zero address or the caller.
    function checkStartsWithCaller(bytes32 salt) internal view {
        /// @solidity memory-safe-assembly
        assembly {
        // If the salt does not start with the zero address or the caller.
            if iszero(or(iszero(shr(96, salt)), eq(caller(), shr(96, salt)))) {
            // Store the function selector of `SaltDoesNotStartWithCaller()`.
                mstore(0x00, 0x2f634836)
            // Revert with (offset, size).
                revert(0x1c, 0x04)
            }
        }
    }
}


interface IPuzzle {
    /// @notice Returns the puzzle's name.
    /// @return The puzzle's name.
    function name() external pure returns (string memory);

    /// @notice Generates the puzzle's starting position based on a seed.
    /// @dev The seed is intended to be `msg.sender` of some wrapper function or
    /// call.
    /// @param _seed The seed to use to generate the puzzle.
    /// @return The puzzle's starting position.
    function generate(address _seed) external returns (uint256);

    /// @notice Verifies that a solution is valid for the puzzle.
    /// @dev `_start` is intended to be an output from {IPuzzle-generate}.
    /// @param _start The puzzle's starting position.
    /// @param _solution The solution to the puzzle.
    /// @return Whether the solution is valid.
    function verify(uint256 _start, uint256 _solution) external returns (bool);
}



contract PhilosophersStone is IPuzzle {
    using LibClone for address;

    struct Trial {
        uint32 aeon;
        address arcanum;
        uint8 phase;
    }

    address codex;
    mapping(uint256 => Trial) trials;
    mapping(address => bool) elixirs;

    constructor() {
        codex = address(new Codex());
        codex.call(
            abi.encodeWithSignature(
                "prepare(address,address,bytes4)", address(0), address(0), bytes4(0)
            )
        );
    }

    function name() external pure returns (string memory) {
        return unicode"♄ 🝡🝟 ☉";
    }

    function generate(address _seed) public pure returns (uint256) {
        return uint256(keccak256(abi.encode(_seed)));
    }

    function verify(uint256 _start, uint256 _solution) external view returns (bool) {
        Trial memory trial = trials[_start];
        require(trial.arcanum == address(uint160(_solution)));
        return trial.phase == 2;
    }

    function alter(address adept) public {
        require(elixirs[msg.sender]);
        elixirs[msg.sender] = false;
        uint256 sigil = generate(adept);
        trials[sigil].phase += 1;
    }

    function transmute(uint256 materia) external {
        uint256 sigil = generate(msg.sender);
        trials[sigil] = Trial({
            aeon: uint32(block.number),
            arcanum: address(uint160(materia)),
            phase: 0
        });
    }

    function solve() external {
        uint256 sigil = generate(msg.sender);
        Trial memory trial = trials[sigil];

        require(trial.aeon == uint32(block.number));
        require(trial.phase == 0);

        address materia = trial.arcanum;
        require(bytes3(materia.codehash) == 0x001ead);

        bytes32 salt = bytes32(abi.encodePacked(uint128(trial.aeon), uint128(sigil)));
        bytes4 essence = bytes4(bytes32(sigil));

        address elixir = codex.cloneDeterministic(salt);
        elixir.call(
            abi.encodeWithSignature(
                "prepare(address,address,bytes4)", msg.sender, materia, essence
            )
        );
        elixirs[elixir] = true;
    }

    function coagula() external {
        uint256 sigil = generate(msg.sender);
        Trial memory trial = trials[sigil];

        require(trial.aeon == uint32(block.number));
        require(trial.phase == 1);

        address materia = trial.arcanum;
        require(bytes3(materia.codehash) == 0x00901d);

        bytes32 salt = bytes32(abi.encodePacked(uint128(trial.aeon), uint128(sigil >> 128)));
        bytes4 essence = bytes4(bytes32(sigil) << 32);

        address elixir = codex.cloneDeterministic(salt);
        elixir.call(
            abi.encodeWithSignature(
                "prepare(address,address,bytes4)", msg.sender, materia, essence
            )
        );
        elixirs[elixir] = true;
    }
}

contract Codex {
    address stone;
    uint256 aeon;
    address adept;
    address materia;
    bytes4 essence;

    constructor() {
        bytes memory elixir = (
            hex"608060405234801561001057600080fd5b50600436106100575760003560e01c806383"
            hex"197ef01461005c578063841271ed146100665780638bbbb2e21461006e578063a69dc2"
            hex"7414610081578063cd57c8ea14610089575b600080fd5b610064610091565b005b6100"
            hex"64610128565b61006461007c36600461046f565b610264565b6100646102d3565b6100"
            hex"6461035c565b6002546001600160a01b031633146100a857600080fd5b436001541461"
            hex"00b657600080fd5b6003546040516655895656d5895560c91b81526000918291600160"
            hex"0160a01b03909116906007016000604051808303816000865af19150503d8060008114"
            hex"61011a576040519150601f19603f3d011682016040523d82523d6000602084013e6101"
            hex"1f565b606091505b50909250905033ff5b6002546001600160a01b0316331461013f57"
            hex"600080fd5b436001541461014d57600080fd5b6003546040516655895656d5895560c9"
            hex"1b815260009182916001600160a01b0390911690600701600060405180830381600086"
            hex"5af19150503d80600081146101b1576040519150601f19603f3d011682016040523d82"
            hex"523d6000602084013e6101b6565b606091505b5091509150816101c557600080fd5b60"
            hex"00818060200190518101906101db91906104b6565b6003549091506001600160e01b03"
            hex"19808316600160a01b90920460e01b161461020357600080fd5b60005460405163b10a"
            hex"582160e01b81523360048201526001600160a01b039091169063b10a58219060240160"
            hex"0060405180830381600087803b15801561024857600080fd5b505af115801561025c57"
            hex"3d6000803e3d6000fd5b503392505050ff5b6000546001600160a01b03161561027a57"
            hex"600080fd5b600080546001600160a01b03199081163317909155436001556002805460"
            hex"01600160a01b0395861692169190911790556003805460e09290921c600160a01b0260"
            hex"01600160c01b03199092169290931691909117179055565b6002546001600160a01b03"
            hex"1633146102ea57600080fd5b43600154146102f857600080fd5b600354604051665589"
            hex"5656d5895560c91b815260009182916001600160a01b03909116906007016000604051"
            hex"808303816000865af19150503d8060008114610057576040519150601f19603f3d0116"
            hex"82016040523d82523d6000602084013e600080fd5b6002546001600160a01b03163314"
            hex"61037357600080fd5b436001541461038157600080fd5b6003546040516655895656d5"
            hex"895560c91b815260009182916001600160a01b03909116906007016000604051808303"
            hex"816000865af19150503d80600081146103e5576040519150601f19603f3d0116820160"
            hex"40523d82523d6000602084013e6103ea565b606091505b5091509150816103f9576000"
            hex"80fd5b60008180602001905181019061040f91906104b6565b60035490915060016001"
            hex"60e01b0319808316600160a01b90920460e01b161461043757600080fd5b33ff5b8035"
            hex"6001600160a01b038116811461045157600080fd5b919050565b6001600160e01b0319"
            hex"8116811461046c57600080fd5b50565b60008060006060848603121561048457600080"
            hex"fd5b61048d8461043a565b925061049b6020850161043a565b915060408401356104ab"
            hex"81610456565b809150509250925092565b6000602082840312156104c857600080fd5b"
            hex"81516104d381610456565b939250505056fea164736f6c6343000815000a"
        );
        assembly {
            return(add(elixir, 0x20), mload(elixir))
        }
    }
}
