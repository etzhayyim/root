// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

import "forge-std/Test.sol";
import {EtzhayyimAnchor} from "../src/EtzhayyimAnchor.sol";

contract EtzhayyimAnchorTest is Test {
    EtzhayyimAnchor anchorC;

    address constant ANCHORER_A = address(0xA);
    address constant ANCHORER_B = address(0xB);

    function setUp() public {
        anchorC = new EtzhayyimAnchor();
    }

    // ─── Happy path ─────────────────────────────────────────────────────

    function test_anchor_emits_event_and_stores_entry() public {
        bytes32 root = keccak256(abi.encodePacked("root-1"));
        bytes memory cid = bytes("bafyreidemo...");
        vm.expectEmit(true, true, false, true);
        emit EtzhayyimAnchor.Anchored(root, address(this), cid, block.number, 100);
        anchorC.anchor(root, cid, 100);
        assertEq(anchorC.rootCount(), 1);
    }

    function test_anchor_indexes_anchorer_address() public {
        bytes32 root = keccak256(abi.encodePacked("root-indexed"));
        bytes memory cid = bytes("bafy-indexed");

        // The second indexed topic is `anchorer`. We assert it carries
        // the caller address — important for off-chain indexers that
        // filter by who anchored.
        vm.prank(ANCHORER_A);
        vm.expectEmit(true, true, false, true);
        emit EtzhayyimAnchor.Anchored(root, ANCHORER_A, cid, block.number, 7);
        anchorC.anchor(root, cid, 7);
    }

    function test_anchor_stores_full_entry_shape() public {
        bytes32 root = keccak256(abi.encodePacked("root-shape"));
        bytes memory cid = bytes("bafy-shape");

        vm.roll(12345);
        vm.warp(1_700_000_000);
        vm.prank(ANCHORER_A);
        anchorC.anchor(root, cid, 42);

        (
            bytes32 storedRoot,
            bytes memory storedCid,
            uint256 storedBlock,
            address storedAnchorer,
            uint64 storedBatchSize,
            uint64 storedAnchoredAt
        ) = anchorC.anchors(root);

        assertEq(storedRoot, root);
        assertEq(storedCid, cid);
        assertEq(storedBlock, 12345);
        assertEq(storedAnchorer, ANCHORER_A);
        assertEq(storedBatchSize, 42);
        assertEq(storedAnchoredAt, 1_700_000_000);
    }

    function test_anchors_unanchored_returns_zero_entry() public view {
        bytes32 root = keccak256(abi.encodePacked("nope"));
        (, , uint256 storedBlock, , , ) = anchorC.anchors(root);
        // anchor() uses blockNumber != 0 as the "already anchored"
        // probe; the zero-block-number guarantee is what makes
        // anchor-cron's idempotency check correct.
        assertEq(storedBlock, 0);
    }

    // ─── Reverts ─────────────────────────────────────────────────────────

    function test_anchor_reverts_on_duplicate() public {
        bytes32 root = keccak256(abi.encodePacked("root-1"));
        bytes memory cid = bytes("bafyreidemo...");
        anchorC.anchor(root, cid, 100);
        vm.expectRevert(
            abi.encodeWithSelector(EtzhayyimAnchor.AlreadyAnchored.selector, root)
        );
        anchorC.anchor(root, cid, 100);
    }

    function test_anchor_reverts_on_empty_cid() public {
        bytes32 root = keccak256(abi.encodePacked("root-1"));
        vm.expectRevert(EtzhayyimAnchor.EmptyIpfsCid.selector);
        anchorC.anchor(root, bytes(""), 100);
    }

    function test_anchor_duplicate_revert_does_not_change_state() public {
        bytes32 root = keccak256(abi.encodePacked("root-once"));
        anchorC.anchor(root, bytes("first-cid"), 1);
        uint256 countBefore = anchorC.rootCount();

        vm.expectRevert();
        anchorC.anchor(root, bytes("second-cid"), 99);

        // The original entry must remain — anchoring twice MUST NOT
        // overwrite.
        (
            bytes32 storedRoot,
            bytes memory storedCid,
            ,
            ,
            uint64 storedBatchSize,

        ) = anchorC.anchors(root);
        assertEq(storedRoot, root);
        assertEq(storedCid, bytes("first-cid"));
        assertEq(storedBatchSize, 1);
        assertEq(anchorC.rootCount(), countBefore);
    }

    // ─── listRoots ───────────────────────────────────────────────────────

    function test_listRoots_paginates() public {
        for (uint256 i = 0; i < 5; i++) {
            anchorC.anchor(keccak256(abi.encode(i)), bytes("bafy..."), 1);
        }
        bytes32[] memory page = anchorC.listRoots(1, 2);
        assertEq(page.length, 2);
    }

    function test_listRoots_offset_at_or_past_total_returns_empty() public {
        for (uint256 i = 0; i < 3; i++) {
            anchorC.anchor(keccak256(abi.encode(i)), bytes("bafy..."), 1);
        }
        bytes32[] memory pageAt = anchorC.listRoots(3, 5);
        assertEq(pageAt.length, 0);
        bytes32[] memory pagePast = anchorC.listRoots(99, 5);
        assertEq(pagePast.length, 0);
    }

    function test_listRoots_partial_last_page() public {
        bytes32[] memory anchored = new bytes32[](3);
        for (uint256 i = 0; i < 3; i++) {
            anchored[i] = keccak256(abi.encode("partial", i));
            anchorC.anchor(anchored[i], bytes("bafy..."), 1);
        }
        // offset=2 limit=5 → end clamps to total=3 → length 1 returned.
        bytes32[] memory page = anchorC.listRoots(2, 5);
        assertEq(page.length, 1);
        assertEq(page[0], anchored[2]);
    }

    function test_listRoots_preserves_insertion_order() public {
        bytes32[] memory expected = new bytes32[](4);
        for (uint256 i = 0; i < 4; i++) {
            expected[i] = keccak256(abi.encode("order", i));
            anchorC.anchor(expected[i], bytes("bafy..."), 1);
        }
        bytes32[] memory page = anchorC.listRoots(0, 4);
        assertEq(page.length, 4);
        for (uint256 i = 0; i < 4; i++) {
            assertEq(page[i], expected[i]);
        }
    }

    function test_listRoots_limit_zero_returns_empty() public {
        anchorC.anchor(keccak256(abi.encode("zero")), bytes("bafy"), 1);
        bytes32[] memory page = anchorC.listRoots(0, 0);
        assertEq(page.length, 0);
    }

    // ─── rootCount ──────────────────────────────────────────────────────

    function test_rootCount_grows_monotonically_across_anchorers() public {
        assertEq(anchorC.rootCount(), 0);

        vm.prank(ANCHORER_A);
        anchorC.anchor(keccak256(abi.encode("a-1")), bytes("bafy"), 1);
        assertEq(anchorC.rootCount(), 1);

        vm.prank(ANCHORER_B);
        anchorC.anchor(keccak256(abi.encode("b-1")), bytes("bafy"), 1);
        assertEq(anchorC.rootCount(), 2);

        vm.prank(ANCHORER_A);
        anchorC.anchor(keccak256(abi.encode("a-2")), bytes("bafy"), 1);
        assertEq(anchorC.rootCount(), 3);
    }

    // ─── Fuzz ───────────────────────────────────────────────────────────

    /// @notice Fuzz the rootHash + cid + batchSize tuple. anchor() must
    ///         succeed for any non-empty cid and any new rootHash, no
    ///         matter the bit pattern. Bounds are wide; foundry's default
    ///         runs (256) give us good coverage.
    function testFuzz_anchor_accepts_any_nonempty_cid(
        bytes32 root,
        bytes memory cid,
        uint64 batchSize
    ) public {
        vm.assume(cid.length > 0);
        // Foundry sometimes generates a root that we'd hit twice if we
        // didn't dedupe; the assume + the no-prior-entry probe keeps
        // each fuzz run sane.
        vm.assume(_unanchored(root));
        anchorC.anchor(root, cid, batchSize);
        (, , uint256 storedBlock, , uint64 storedBatchSize, ) = anchorC.anchors(root);
        assertEq(storedBlock, block.number);
        assertEq(storedBatchSize, batchSize);
    }

    function _unanchored(bytes32 root) internal view returns (bool) {
        (, , uint256 storedBlock, , , ) = anchorC.anchors(root);
        return storedBlock == 0;
    }
}
