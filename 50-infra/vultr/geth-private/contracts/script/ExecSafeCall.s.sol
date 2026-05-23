// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {Script, console2} from "forge-std/Script.sol";

interface ISafe {
    function getTransactionHash(
        address to, uint256 value, bytes memory data, uint8 operation,
        uint256 safeTxGas, uint256 baseGas, uint256 gasPrice,
        address gasToken, address refundReceiver, uint256 _nonce
    ) external view returns (bytes32);
    function nonce() external view returns (uint256);
    function execTransaction(
        address to, uint256 value, bytes memory data, uint8 operation,
        uint256 safeTxGas, uint256 baseGas, uint256 gasPrice,
        address gasToken, address payable refundReceiver, bytes memory signatures
    ) external payable returns (bool success);
}

/// @notice Execute an arbitrary call via the 2-of-3 Safe.
///
/// Required env vars:
///   K1_PRIV      — hex private key for Safe owner 1 (signer, no ETH needed)
///   K2_PRIV      — hex private key for Safe owner 2 (signer, no ETH needed)
///   SENDER_PRIV  — hex private key for gas payer / broadcaster (e.g. sealer)
///   TARGET       — contract address to call
///   CALLDATA     — ABI-encoded calldata (output of `cast calldata ...`)
///
/// Usage:
///   forge script script/ExecSafeCall.s.sol \
///     --rpc-url https://geth.etzhayyim.com --broadcast --legacy
contract ExecSafeCall is Script {
    ISafe constant SAFE = ISafe(0xc0C20918372bf200faf3587eB0C6685a830daFc1);

    function run() external {
        uint256 k1Priv     = vm.envUint("K1_PRIV");
        uint256 k2Priv     = vm.envUint("K2_PRIV");
        uint256 senderPriv = vm.envUint("SENDER_PRIV");
        address target     = vm.envAddress("TARGET");
        bytes memory data  = vm.envBytes("CALLDATA");

        uint256 nonce = SAFE.nonce();
        bytes32 txHash = SAFE.getTransactionHash(
            target, 0, data,
            0,          // CALL
            0, 0, 0,    // safeTxGas, baseGas, gasPrice
            address(0), address(0),
            nonce
        );

        (uint8 v1, bytes32 r1, bytes32 s1) = vm.sign(k1Priv, txHash);
        (uint8 v2, bytes32 r2, bytes32 s2) = vm.sign(k2Priv, txHash);

        address addr1 = vm.addr(k1Priv);
        address addr2 = vm.addr(k2Priv);

        bytes memory sigs;
        if (addr1 < addr2) {
            sigs = abi.encodePacked(r1, s1, v1, r2, s2, v2);
        } else {
            sigs = abi.encodePacked(r2, s2, v2, r1, s1, v1);
        }

        console2.log("Safe nonce:", nonce);
        console2.log("txHash:"); console2.logBytes32(txHash);
        console2.log("Signer1:", addr1);
        console2.log("Signer2:", addr2);

        vm.startBroadcast(senderPriv);
        bool ok = SAFE.execTransaction(
            target, 0, data,
            0, 0, 0, 0,
            address(0), payable(address(0)),
            sigs
        );
        vm.stopBroadcast();

        require(ok, "Safe: execTransaction failed");
        console2.log("Safe execTransaction succeeded");
    }
}
