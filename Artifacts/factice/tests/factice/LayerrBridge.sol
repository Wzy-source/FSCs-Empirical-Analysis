// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.20;

import {IERC20} from "./interfaces/IERC20.sol";
import {IV3SwapRouter} from "./interfaces/IV3SwapRouter.sol";
import {IStargateRouter} from "./interfaces/IStargateRouter.sol";
import {ILayerrBridge} from "./interfaces/ILayerrBridge.sol";
import {IWETH} from "./interfaces/IWETH.sol";
import {MintOrder} from "./lib/MinterStructs.sol";
import {ILayerrMinter} from "./interfaces/ILayerrMinter.sol";

/**
 * @title LayerrBridge
 * @author 0xth0mas (Layerr)
 * @notice LayerrBridge is powered by Stargate Finance and LayerZero
 *         to allow crosschain minting of NFTs with the LayerrMinter
 *         contract and native-to-native bridging of tokens.
 */
contract LayerrBridge is ILayerrBridge {

    /// @dev Layerr-owned account
    address public owner = 0x0000000000799dfE79Ed462822EC68eF9a6199e6;
    /// @dev LayerrMinter interface
    ILayerrMinter public constant layerrMinter = ILayerrMinter(0x000000000000D58696577347F78259bD376F1BEC);
    /// @dev Stargate router contract interface for cross-chain bridging
    IStargateRouter public stargateRouter;
    /// @dev Automatic market maker router interface for local token swaps
    IV3SwapRouter public ammRouter;
    /// @dev WETH9 contract
    IWETH public weth;
    /// @dev Stargate native token contract
    IWETH public sgNative;

    /// @dev Layerr transaction fee in BPS
    uint256 private constant LAYERR_BPS = 25;
    /// @dev Denominator for BPS calculations
    uint256 private constant BPS_DENOMINATOR = 10_000;
    /// @dev Stargate transaction type for gas estimation
    uint8 private constant TYPE_SWAP_REMOTE = 1;

    modifier onlyOwner() {
        if (msg.sender != owner) {
            revert NotContractOwner();
        }
        _;
    }

    constructor() {
        _setInitialRouterAddresses();
    }

    /**
     * @inheritdoc ILayerrBridge
     */
    function remoteMintWithLocalNative(
        uint16 dstChainId,
        address bridgeToken,
        uint16 srcPoolId,
        uint16 dstPoolId,
        uint256 gasProvided,
        uint256 localSwapAmountOutMin,
        uint256 remoteSwapAmountOutMin,
        uint256 remoteGasUnits,
        MintOrder[] calldata mintOrders,
        bytes32 bridgeTrackingHash
    ) external payable {
        if(gasProvided == 0 || gasProvided > msg.value) revert InsufficientGas();

        uint256 nativeTokenToRouter = gasProvided;
        uint256 swapValueIn;
        uint256 layerrFee;
        unchecked {
            swapValueIn = msg.value - gasProvided;
            layerrFee = swapValueIn * LAYERR_BPS / BPS_DENOMINATOR;
            swapValueIn -= layerrFee;
        }

        _transferNative(owner, layerrFee);

        uint256 bridgeAmount;
        if(bridgeToken == address(sgNative)) {
            bridgeAmount = swapValueIn;
            nativeTokenToRouter += swapValueIn;
        } else {
            bridgeAmount = _swapNativeForTokens(bridgeToken, swapValueIn);
            IERC20(bridgeToken).approve(address(stargateRouter), bridgeAmount);
        }

        // encode payload data to send to destination contract, which it will handle with sgReceive()
        bytes memory data = abi.encode(remoteSwapAmountOutMin, mintOrders, msg.sender, bridgeTrackingHash);

        // Stargate's Router.swap() function sends the tokens to the destination chain.
        stargateRouter.swap{value:nativeTokenToRouter}(
            dstChainId,
            srcPoolId,
            dstPoolId,
            payable(msg.sender),
            bridgeAmount,
            localSwapAmountOutMin,
            IStargateRouter.lzTxObj(remoteGasUnits, 0, "0x"),
            abi.encodePacked(address(this)),
            data
        );
    }

    /**
     * @inheritdoc ILayerrBridge
     */
    function swapNativeForNative(
        uint16 dstChainId,
        address bridgeToken,
        uint16 srcPoolId,
        uint16 dstPoolId,
        uint256 gasProvided,
        uint256 localSwapAmountOutMin,
        uint256 remoteSwapAmountOutMin,
        uint256 remoteGasUnits,
        bytes32 bridgeTrackingHash
    ) external payable {
        if(gasProvided == 0 || gasProvided > msg.value) revert InsufficientGas();

        uint256 nativeTokenToRouter = gasProvided;
        uint256 swapValueIn;
        uint256 layerrFee;
        unchecked {
            swapValueIn = msg.value - gasProvided;
            layerrFee = swapValueIn * LAYERR_BPS / BPS_DENOMINATOR;
            swapValueIn -= layerrFee;
        }

        _transferNative(owner, layerrFee);

        uint256 bridgeAmount;
        if(bridgeToken == address(sgNative)) {
            bridgeAmount = swapValueIn;
            nativeTokenToRouter += swapValueIn;
        } else {
            bridgeAmount = _swapNativeForTokens(bridgeToken, swapValueIn);
            IERC20(bridgeToken).approve(address(stargateRouter), bridgeAmount);
        }

        // encode payload data to send to destination contract, which it will handle with sgReceive()
        bytes memory data = abi.encode(remoteSwapAmountOutMin, msg.sender, bridgeTrackingHash);

        // Stargate's Router.swap() function sends the tokens to the destination chain.
        stargateRouter.swap{value:nativeTokenToRouter}(
            dstChainId,
            srcPoolId,
            dstPoolId,
            payable(msg.sender),
            bridgeAmount,
            localSwapAmountOutMin,
            IStargateRouter.lzTxObj(remoteGasUnits, 0, "0x"),
            abi.encodePacked(address(this)),
            data
        );
    }

    /**
     * @inheritdoc ILayerrBridge
     */
    function estimateMintAndBridgeGas(
        uint16 dstChainId,
        uint256 remoteSwapAmountOutMin,
        uint256 remoteGasUnits,
        MintOrder[] calldata mintOrders
    ) external view returns(uint256) {
        bytes memory data = abi.encode(remoteSwapAmountOutMin, mintOrders, msg.sender, keccak256(""));

        (uint256 gasAmount, ) = stargateRouter.quoteLayerZeroFee(
            dstChainId,
            TYPE_SWAP_REMOTE,
            abi.encodePacked(address(this)),
            data,
            IStargateRouter.lzTxObj(remoteGasUnits, 0, "0x")
        );
        return gasAmount;
    }

    /**
     * @inheritdoc ILayerrBridge
     */
    function estimateBridgeOnlyGas(
        uint16 dstChainId,
        uint256 remoteSwapAmountOutMin,
        uint256 remoteGasUnits
    ) external view returns(uint256) {
        bytes memory data = abi.encode(remoteSwapAmountOutMin, msg.sender, keccak256(""));

        (uint256 gasAmount, ) = stargateRouter.quoteLayerZeroFee(
            dstChainId,
            TYPE_SWAP_REMOTE,
            abi.encodePacked(address(this)),
            data,
            IStargateRouter.lzTxObj(remoteGasUnits, 0, "0x")
        );
        return gasAmount;
    }

    /**
     * @notice Receive the tokens and payload from the Stargate Route
     * @dev Swap/bridge-only transactions will have a 64-byte payload
     *      Swap/bridge/mint transaction payloads will be greater than 64 bytes
     */
    function sgReceive(
        uint16,
        bytes memory,
        uint256,
        address tokenAddress,
        uint256 amountFromStargate,
        bytes memory payload
    ) override external {
        if(msg.sender != address(stargateRouter)) revert NotStargateRouter();

        uint256 nativeBalanceStart = address(this).balance;

        uint256 swapAmountOutMin;
        MintOrder[] memory mintOrders;
        address mintTo;
        bool swapAndMint;
        bytes32 bridgeTrackingHash;
        if(payload.length == 96) {
            (swapAmountOutMin, mintTo, bridgeTrackingHash) = abi.decode(payload, (uint256, address, bytes32));
        } else {
            (swapAmountOutMin, mintOrders, mintTo, bridgeTrackingHash) = abi.decode(payload, (uint256, MintOrder[], address, bytes32));
            swapAndMint = true;
        }

        uint256 amountOut;
        if(tokenAddress == address(sgNative)) {
            //withdraw native token if balance > 0, amountOut = amountFromStargate
            //future-proof if bridge is added to sgNative's noUnwrapTo
            uint256 sgNativeBalance = sgNative.balanceOf(address(this));
            if(sgNativeBalance > 0) {
                try sgNative.withdraw(sgNativeBalance) { } catch { }
            }
            amountOut = amountFromStargate;
            nativeBalanceStart = address(this).balance - amountFromStargate;
        } else {
            //non-native token swap through AMM
            amountOut = _swapTokensForNative(tokenAddress, amountFromStargate, swapAmountOutMin) - nativeBalanceStart;
        }
        if(amountOut == 0) {
            //swap failed, send tokens to minter, skip minting
            try IERC20(tokenAddress).transfer(mintTo, amountFromStargate) {
                emit RemoteSwapUnsuccessful(mintTo, tokenAddress, amountFromStargate, bridgeTrackingHash);
            } catch {
                emit RemoteSwapAndTransferUnsuccessful(mintTo, tokenAddress, amountFromStargate, bridgeTrackingHash);
            }
        } else {
            //swap successful, attempt to mint if mintOrder provided, only supply value from swap
            if(swapAndMint) {
                try layerrMinter.mintBatchTo{value: amountOut}(mintTo, mintOrders, 0) {
                    emit RemoteMintSuccessful(mintTo, bridgeTrackingHash);
                } catch {
                    emit RemoteMintUnsuccessful(mintTo, bridgeTrackingHash);
                }
            }
        }

        //transfer remaining native tokens to minter
        uint256 nativeBalanceRemaining = address(this).balance;
        if(nativeBalanceRemaining > nativeBalanceStart) {
            _transferNative(mintTo, (nativeBalanceRemaining - nativeBalanceStart));
        }
    }

    /**
     * @inheritdoc ILayerrBridge
     */
    function setRouterAddresses(
        address _stargateRouter,
        address _ammRouter,
        address _sgNative
    ) external onlyOwner {
        //only allow update if address was not previously set by
        //constructor or this function
        if(address(stargateRouter) == address(0)) {
            stargateRouter = IStargateRouter(_stargateRouter);
        }
        if(address(ammRouter) == address(0)) {
            ammRouter = IV3SwapRouter(_ammRouter);
        }
        if(address(sgNative) == address(0)) {
            sgNative = IWETH(_sgNative);
        }
        if(address(weth) == address(0)) {
            weth = IWETH(ammRouter.WETH9());
        }
    }

    /**
     * @dev Swaps `amountIn` of native token for `tokenAddress`
     *      We do not check for minimum output here. Minimum output
     *      is enforced through the Stargate swap.
     * @param tokenAddress the address of the token to swap for
     * @param amountIn the amount of native token to swap
     */
    function _swapNativeForTokens(
        address tokenAddress,
        uint256 amountIn
    ) internal returns (uint256 amountOut) {
        amountOut = ammRouter.exactInputSingle{value: amountIn}(
            IV3SwapRouter.ExactInputSingleParams({
                tokenIn: address(weth),
                tokenOut: tokenAddress,
                fee: 500,
                recipient: address(this),
                amountIn: amountIn,
                amountOutMinimum: 0,
                sqrtPriceLimitX96: 0
            })
        );
    }


    /**
     * @dev Swaps contract's balance of `tokenAddress` for chain native
     *      token. Enforces `amountOutMin` as minimum tokens to receive.
     *      Native token is received from AMM as WETH and unwrapped.
     * @param tokenAddress the address of the token to swap from
     * @param amountFromStargate the amount of tokens received from Stargate
     * @param amountOutMin the minimum amount of native tokens to receive
     * @return amountOut new native account balance
     */
    function _swapTokensForNative(
        address tokenAddress,
        uint256 amountFromStargate,
        uint256 amountOutMin
    ) internal returns (uint256 amountOut) {
        //prevent revert, contract will forward tokens if amountOut = 0
        try IERC20(tokenAddress).approve(address(ammRouter), amountFromStargate) { } catch { }

        try ammRouter.exactInputSingle(
            IV3SwapRouter.ExactInputSingleParams({
                tokenIn: tokenAddress,
                tokenOut: address(weth),
                fee: 500,
                recipient: address(this),
                amountIn: amountFromStargate,
                amountOutMinimum: amountOutMin,
                sqrtPriceLimitX96: 0
            })
        ) {
            try weth.withdraw(weth.balanceOf(address(this))) { } catch { }
        } catch { }
        amountOut = address(this).balance;
    }

    /**
     * @notice Transfers `amount` of native token to `to` address. Reverts if the transfer fails.
     * @param to address to send native token to
     * @param amount amount of native token to send
     */
    function _transferNative(address to, uint256 amount) internal {
        (bool sent, ) = payable(to).call{value: amount}("");
        if (!sent) {
            if(address(this).balance < amount) {
                revert InsufficientBalance();
            } else {
                revert PaymentFailed();
            }
        }
    }

    /**
     * @dev preset addresses for initial deployment of contracts via CREATE2
     */
    function _setInitialRouterAddresses() internal {
        if(block.chainid == 1) { //Ethereum mainnet
            stargateRouter = IStargateRouter(0xeCc19E177d24551aA7ed6Bc6FE566eCa726CC8a9);
            ammRouter = IV3SwapRouter(0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45);
            sgNative = IWETH(0x72E2F4830b9E45d52F80aC08CB2bEC0FeF72eD9c);
        } else if(block.chainid == 56) { //BSC
            stargateRouter = IStargateRouter(0xeCc19E177d24551aA7ed6Bc6FE566eCa726CC8a9);
            ammRouter = IV3SwapRouter(0xB971eF87ede563556b2ED4b1C0b0019111Dd85d2);
        } else if(block.chainid == 42161) { //Arbitrum
            stargateRouter = IStargateRouter(0xeCc19E177d24551aA7ed6Bc6FE566eCa726CC8a9);
            ammRouter = IV3SwapRouter(0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45);
            sgNative = IWETH(0x82CbeCF39bEe528B5476FE6d1550af59a9dB6Fc0);
        } else if(block.chainid == 10) { //Optimism
            stargateRouter = IStargateRouter(0xeCc19E177d24551aA7ed6Bc6FE566eCa726CC8a9);
            ammRouter = IV3SwapRouter(0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45);
            sgNative = IWETH(0xb69c8CBCD90A39D8D3d3ccf0a3E968511C3856A0);
        } else if(block.chainid == 43114) { //Avalanche
            stargateRouter = IStargateRouter(0xeCc19E177d24551aA7ed6Bc6FE566eCa726CC8a9);
            ammRouter = IV3SwapRouter(0xbb00FF08d01D300023C629E8fFfFcb65A5a578cE);
        } else if(block.chainid == 137) { //Polygon
            stargateRouter = IStargateRouter(0xeCc19E177d24551aA7ed6Bc6FE566eCa726CC8a9);
            ammRouter = IV3SwapRouter(0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45);
        } else if(block.chainid == 8453) { //Base
            stargateRouter = IStargateRouter(0xeCc19E177d24551aA7ed6Bc6FE566eCa726CC8a9);
            ammRouter = IV3SwapRouter(0x2626664c2603336E57B271c5C0b26F421741e481);
            sgNative = IWETH(0x224D8Fd7aB6AD4c6eb4611Ce56EF35Dec2277F03);
        }
        if(address(ammRouter) != address(0)) {
            weth = IWETH(ammRouter.WETH9());
        }
    }

    receive() external payable {}
    fallback() external payable {}
}
