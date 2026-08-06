// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {ECDSA} from "../src/utils/ECDSA.sol";
import {
    TitheRouter,
    IERC20 as ITitheRouterUsdc,
    IConstitution as ITitheRouterConstitution,
    IChartersComplianceRegistry as ITitheRouterCharters
} from "../src/TitheRouter.sol";
import {Constitution} from "../src/Constitution.sol";
import {AdherentRegistry} from "../src/AdherentRegistry.sol";
import {ChartersComplianceRegistry, IAdherentRegistry as ICharterAdherentRegistry} from "../src/ChartersComplianceRegistry.sol";
import {MockUsdc} from "../script/MockUsdc.sol";

/// @dev First test coverage for TitheRouter.route() — the 10%/90% atomic-split logic
///      itself (ADR-2605192130). Every other contract this actor depends on already had
///      its own test file; the split arithmetic + purpose gating + charter gating on
///      route() did not, despite being the mechanism every single donation to etzhayyim
///      passes through.
contract TitheRouterTest is Test {
    using ECDSA for bytes32;

    TitheRouter router;
    Constitution constitution;
    ChartersComplianceRegistry charters;
    AdherentRegistry adherents;
    MockUsdc usdc;

    address constant PAYER = address(0x9A7E4);
    address constant RECIPIENT = address(0x4EC17);
    address constant PUBLIC_FUND = address(0xF00D);

    bytes32 constant K_TITHE_BPS = keccak256("tithe_bps");
    bytes32 constant PURPOSE_DONATION = keccak256("donation");

    uint256[5] councilKeys = [uint256(11), uint256(12), uint256(13), uint256(14), uint256(15)];
    address[5] council;

    function setUp() public {
        for (uint256 i = 0; i < 5; i++) council[i] = vm.addr(councilKeys[i]);

        usdc = new MockUsdc();

        bytes32[] memory noConstants = new bytes32[](0);
        bytes32[] memory mutKeys = new bytes32[](1);
        bytes32[] memory mutVals = new bytes32[](1);
        mutKeys[0] = K_TITHE_BPS;
        mutVals[0] = bytes32(uint256(1000)); // 10%
        constitution = new Constitution(noConstants, noConstants, mutKeys, mutVals);

        address[] memory officers = new address[](1);
        officers[0] = address(this);
        adherents = new AdherentRegistry(officers);

        address[] memory bootstrap = new address[](5);
        for (uint256 i = 0; i < 5; i++) bootstrap[i] = council[i];
        charters = new ChartersComplianceRegistry(ICharterAdherentRegistry(address(adherents)), bootstrap);

        router = new TitheRouter(
            ITitheRouterUsdc(address(usdc)),
            ITitheRouterConstitution(address(constitution)),
            ITitheRouterCharters(address(charters)),
            PUBLIC_FUND
        );

        usdc.mint(PAYER, 1_000_000e6);
        vm.prank(PAYER);
        usdc.approve(address(router), type(uint256).max);
    }

    function _signAttestNonAlignedAddress(
        address subject,
        bytes32 reasonHash,
        bytes32 evidenceCid,
        uint256 pk
    ) internal view returns (bytes memory) {
        bytes32 digest = charters.computeAttestNonAlignedAddressDigest(subject, reasonHash, evidenceCid);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, digest);
        return abi.encodePacked(r, s, v);
    }

    function _makeNonAligned(address subject) internal {
        bytes[] memory sigs = new bytes[](3);
        address[] memory signers = new address[](3);
        bytes32 reasonHash = keccak256("reason");
        bytes32 evidenceCid = keccak256("evidence");
        for (uint256 i = 0; i < 3; i++) {
            signers[i] = council[i];
            sigs[i] = _signAttestNonAlignedAddress(subject, reasonHash, evidenceCid, councilKeys[i]);
        }
        charters.attestNonAlignedAddress(subject, reasonHash, evidenceCid, sigs, signers);
        vm.warp(block.timestamp + charters.APPEAL_WINDOW() + 1);
        charters.finalize(true, subject, 0);
        assertTrue(charters.isNonAlignedAddress(subject));
    }

    // ── the 10%/90% split itself ─────────────────────────────────────────

    function test_route_splitsExactly10PercentAt1000Bps() public {
        vm.prank(PAYER);
        (uint256 titheAmount, uint256 netAmount) = router.route(RECIPIENT, 1_000e6, PURPOSE_DONATION);

        assertEq(titheAmount, 100e6);
        assertEq(netAmount, 900e6);
        assertEq(usdc.balanceOf(PUBLIC_FUND), 100e6);
        assertEq(usdc.balanceOf(RECIPIENT), 900e6);
        assertEq(usdc.balanceOf(PAYER), 1_000_000e6 - 1_000e6);
    }

    function test_route_floorsIntegerDivisionRatherThanRounding() public {
        // 999 * 1000 / 10000 = 99.9 -> floors to 99, net = 900 (999 - 99).
        vm.prank(PAYER);
        (uint256 titheAmount, uint256 netAmount) = router.route(RECIPIENT, 999, PURPOSE_DONATION);
        assertEq(titheAmount, 99);
        assertEq(netAmount, 900);
        assertEq(titheAmount + netAmount, 999); // no dust lost or created
    }

    function test_route_emitsRoutedWithAllFields() public {
        vm.expectEmit(true, true, true, true);
        emit TitheRouter.Routed(PAYER, RECIPIENT, 1_000e6, 100e6, 900e6, PURPOSE_DONATION);
        vm.prank(PAYER);
        router.route(RECIPIENT, 1_000e6, PURPOSE_DONATION);
    }

    function test_route_respectsUpdatedTitheBpsFromConstitution() public {
        // A second router pointed at a Constitution with a different tithe_bps proves
        // the split is read live from Constitution, not hardcoded in TitheRouter.
        bytes32[] memory noConstants = new bytes32[](0);
        bytes32[] memory mutKeys = new bytes32[](1);
        bytes32[] memory mutVals = new bytes32[](1);
        mutKeys[0] = K_TITHE_BPS;
        mutVals[0] = bytes32(uint256(500)); // 5%
        Constitution c5 = new Constitution(noConstants, noConstants, mutKeys, mutVals);
        TitheRouter router5 = new TitheRouter(
            ITitheRouterUsdc(address(usdc)),
            ITitheRouterConstitution(address(c5)),
            ITitheRouterCharters(address(charters)),
            PUBLIC_FUND
        );
        vm.prank(PAYER);
        usdc.approve(address(router5), type(uint256).max);

        vm.prank(PAYER);
        (uint256 titheAmount, uint256 netAmount) = router5.route(RECIPIENT, 1_000e6, PURPOSE_DONATION);
        assertEq(titheAmount, 50e6);
        assertEq(netAmount, 950e6);
    }

    // ── purpose gating (G-invariant: only "donation" is titheable here) ────

    function test_route_revertsOnZeroAmount() public {
        vm.prank(PAYER);
        vm.expectRevert(TitheRouter.ZeroAmount.selector);
        router.route(RECIPIENT, 0, PURPOSE_DONATION);
    }

    function test_route_revertsForNonTitheablePurposes() public {
        bytes32[4] memory rejected = [
            keccak256("kisha"),
            keccak256("grant"),
            keccak256("tithe"),
            keccak256("escrow-refund")
        ];
        for (uint256 i = 0; i < rejected.length; i++) {
            vm.prank(PAYER);
            vm.expectRevert(abi.encodeWithSelector(TitheRouter.PurposeNotTitheable.selector, rejected[i]));
            router.route(RECIPIENT, 1_000e6, rejected[i]);
        }
    }

    // ── Charter Compliance gating ────────────────────────────────────────

    function test_route_revertsForNonAlignedPayer() public {
        _makeNonAligned(PAYER);
        vm.prank(PAYER);
        vm.expectRevert(abi.encodeWithSelector(TitheRouter.PayerCharterNonCompliant.selector, PAYER));
        router.route(RECIPIENT, 1_000e6, PURPOSE_DONATION);
    }

    function test_route_revertsForNonAlignedRecipient() public {
        _makeNonAligned(RECIPIENT);
        vm.prank(PAYER);
        vm.expectRevert(abi.encodeWithSelector(TitheRouter.RecipientCharterNonCompliant.selector, RECIPIENT));
        router.route(RECIPIENT, 1_000e6, PURPOSE_DONATION);
    }

    // ── atomicity: insufficient allowance must revert the WHOLE call, no dust left ──

    function test_route_revertsAtomicallyOnInsufficientAllowance() public {
        vm.prank(PAYER);
        usdc.approve(address(router), 500e6); // less than the 1,000 USDC about to be routed

        uint256 publicFundBefore = usdc.balanceOf(PUBLIC_FUND);
        uint256 recipientBefore = usdc.balanceOf(RECIPIENT);

        vm.prank(PAYER);
        vm.expectRevert(bytes("MockUsdc: allow"));
        router.route(RECIPIENT, 1_000e6, PURPOSE_DONATION);

        // Neither leg of the split landed -- no partial state.
        assertEq(usdc.balanceOf(PUBLIC_FUND), publicFundBefore);
        assertEq(usdc.balanceOf(RECIPIENT), recipientBefore);
    }
}