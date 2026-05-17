// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {Constitution} from "../../src/Constitution.sol";
import {AdherentRegistry} from "../../src/AdherentRegistry.sol";
import {KishaStream} from "../../src/KishaStream.sol";
import {Phenotype} from "../../src/Phenotype.sol";
import {AnchorBridge} from "../../src/AnchorBridge.sol";
import {Governance} from "../../src/Governance.sol";
import {TreasuryMirror} from "../../src/TreasuryMirror.sol";

/// @dev Shared deployment fixture used across the test suite. Wires up
///      Constitution → AdherentRegistry → KishaStream → Phenotype →
///      Governance → TreasuryMirror with sensible S0/S1/S2 defaults so
///      individual tests can focus on behavior rather than setup.
abstract contract Fixture is Test {
    // --- Constitutional keys --------------------------------------------
    bytes32 internal constant K_ONE_SBT_ONE_VOTE     = keccak256("one_sbt_one_vote");
    bytes32 internal constant K_PHENOTYPE_MIN        = keccak256("phenotype_min_bps");
    bytes32 internal constant K_PHENOTYPE_MAX        = keccak256("phenotype_max_bps");
    bytes32 internal constant K_KAPPA_FLOOR          = keccak256("kappa_floor_bps");
    bytes32 internal constant K_KAPPA_CEILING        = keccak256("kappa_ceiling_bps");
    bytes32 internal constant K_QUORUM_FLOOR         = keccak256("quorum_floor_bps");
    bytes32 internal constant K_KISHA_BASE           = keccak256("kisha_base_rate");
    bytes32 internal constant K_KAPPA                = keccak256("kappa_bps");
    bytes32 internal constant K_QUORUM               = keccak256("quorum_bps");
    bytes32 internal constant K_ACTIVE_WINDOW        = keccak256("active_window_secs");
    bytes32 internal constant K_TIMELOCK             = keccak256("timelock_secs");

    bytes32 internal constant EVT_PRAYER = keccak256("prayer");

    // --- Actors ---------------------------------------------------------
    address internal officer = address(0xA11CE);
    address internal alice   = address(0xBEEF);
    address internal bob     = address(0xC0DE);

    // Cell EOA used to sign Phenotype updates.
    uint256 internal cellKey = uint256(keccak256("cell-key"));
    address internal cellAddr;

    // Oracle EOA used to sign TreasuryMirror NAV updates.
    uint256 internal oracleKey = uint256(keccak256("oracle-key"));
    address internal oracleAddr;

    // --- Deployed contracts ---------------------------------------------
    Constitution     internal c;
    AdherentRegistry internal r;
    KishaStream      internal ks;
    Phenotype        internal pn;
    AnchorBridge     internal ab;
    Governance       internal gov;
    TreasuryMirror   internal tm;

    function _deployStack() internal {
        cellAddr = vm.addr(cellKey);
        oracleAddr = vm.addr(oracleKey);

        // Constitution
        bytes32[] memory cK = new bytes32[](6);
        bytes32[] memory cV = new bytes32[](6);
        cK[0] = K_ONE_SBT_ONE_VOTE; cV[0] = bytes32(uint256(1));
        cK[1] = K_PHENOTYPE_MIN;     cV[1] = bytes32(uint256(5_000));
        cK[2] = K_PHENOTYPE_MAX;     cV[2] = bytes32(uint256(20_000));
        cK[3] = K_KAPPA_FLOOR;       cV[3] = bytes32(uint256(100));
        cK[4] = K_KAPPA_CEILING;     cV[4] = bytes32(uint256(500));
        cK[5] = K_QUORUM_FLOOR;      cV[5] = bytes32(uint256(2_000));

        bytes32[] memory mK = new bytes32[](5);
        bytes32[] memory mV = new bytes32[](5);
        mK[0] = K_KISHA_BASE;     mV[0] = bytes32(uint256(1_000_000));
        mK[1] = K_KAPPA;           mV[1] = bytes32(uint256(300));
        mK[2] = K_QUORUM;          mV[2] = bytes32(uint256(3_300));
        mK[3] = K_ACTIVE_WINDOW;   mV[3] = bytes32(uint256(30 days));
        mK[4] = K_TIMELOCK;        mV[4] = bytes32(uint256(72 hours));

        c = new Constitution(cK, cV, mK, mV);

        // AdherentRegistry
        address[] memory officers = new address[](1);
        officers[0] = officer;
        r = new AdherentRegistry(officers);

        // KishaStream + Phenotype
        ks = new KishaStream(r, c, 1_000_000, 30 days);
        pn = new Phenotype(c);

        // AnchorBridge
        ab = new AnchorBridge();

        // Governance + TreasuryMirror
        gov = new Governance(r, c);
        tm  = new TreasuryMirror(c);

        // Bind: Constitution.governance = Governance contract
        c.bindGovernance(address(gov));
    }

    /// Join + first attestation so the adherent immediately counts as active.
    function _joinAndAttest(address holder, string memory did) internal returns (uint256 tokenId) {
        vm.startPrank(officer);
        tokenId = r.join(holder, did, bytes32(0));
        r.attest(tokenId, EVT_PRAYER, bytes32(0));
        vm.stopPrank();
    }

    /// Build an EIP-191-style signature using a Foundry signer key.
    function _signEip191(uint256 pk, bytes32 innerHash) internal pure returns (bytes memory) {
        bytes32 envelope = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", innerHash));
        (uint8 v, bytes32 rSig, bytes32 sSig) = vm.sign(pk, envelope);
        return abi.encodePacked(rSig, sSig, v);
    }
}
