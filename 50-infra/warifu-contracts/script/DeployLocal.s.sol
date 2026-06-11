// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
pragma solidity ^0.8.26;

import {WarifuCard} from "../src/WarifuCard.sol";
import {CreditLine} from "../src/CreditLine.sol";
import {SettlementRouter} from "../src/SettlementRouter.sol";

// Minimal HEVM broadcast surface (no forge-std dependency).
interface Vm {
    function startBroadcast() external;
    function stopBroadcast() external;
}

// LOCAL-ONLY mock USDC. On real networks the canonical USDC address is passed instead
// (Base mainnet 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913) — this is NEVER deployed to prod.
contract MockUSDC {
    string public constant symbol = "USDC";
    uint8 public constant decimals = 6;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    function mint(address to, uint256 a) external { balanceOf[to] += a; }
    function approve(address s, uint256 a) external returns (bool) { allowance[msg.sender][s] = a; return true; }
    function transfer(address to, uint256 a) external returns (bool) { balanceOf[msg.sender] -= a; balanceOf[to] += a; return true; }
    function transferFrom(address f, address t, uint256 a) external returns (bool) {
        allowance[f][msg.sender] -= a; balanceOf[f] -= a; balanceOf[t] += a; return true;
    }
}

/// @title DeployLocal — wire warifu contracts on a local Anvil node (ADR-2605302000).
/// @dev Run: forge script script/DeployLocal.s.sol:DeployLocal --rpc-url http://127.0.0.1:8545
///          --broadcast --private-key <anvil acct0 key>
///      The broadcaster (anvil account 0) is used as Council/wakai-float for the LOCAL deploy
///      only; on real networks Council = the Lv6+/Lv7+ Safe and wakai-float = the wakai pool.
contract DeployLocal {
    Vm constant vm = Vm(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    // Anvil default account 0 — a PUBLIC dev address, never a religious-corp key (no-platform-key,
    // ADR-2605231525). Real deploys pass the Council Safe address via env, not this constant.
    address constant COUNCIL = 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266;

    function run()
        external
        returns (address usdc, address card, address credit, address router)
    {
        vm.startBroadcast();

        MockUSDC _usdc = new MockUSDC();
        WarifuCard _card = new WarifuCard(COUNCIL);
        CreditLine _credit = new CreditLine(COUNCIL, COUNCIL); // wakaiFloat = COUNCIL (local)
        SettlementRouter _router =
            new SettlementRouter(address(_usdc), address(_credit), COUNCIL, COUNCIL);

        // Wire (broadcaster == COUNCIL, so onlyCouncil calls pass).
        _credit.setRouter(address(_router));
        _card.setIssuer(COUNCIL, true);

        vm.stopBroadcast();

        // Fail the deploy if any constitutional invariant is violated.
        require(_router.MERCHANT_FEE_BPS() == 0, "INVARIANT: merchant fee must be 0");
        require(_credit.INTEREST_BPS() == 0, "INVARIANT: credit interest must be 0");
        require(_credit.LATE_FEE_BPS() == 0, "INVARIANT: late fee must be 0");
        require(_card.locked(1) && _card.locked(999), "INVARIANT: cards must be soulbound");
        require(!_router.phase2Enabled(), "INVARIANT: phase2 must default closed");

        return (address(_usdc), address(_card), address(_credit), address(_router));
    }
}
