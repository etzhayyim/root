// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

// ERC-1271: allows contract signers (Gnosis Safe witness cells) as quorum members.
interface IERC1271 {
    function isValidSignature(bytes32 hash, bytes memory signature) external view returns (bytes4);
}
bytes4 constant ERC1271_MAGIC_VALUE = 0x1626ba7e;

/// @notice TitheRouter (50-infra/etzhayyim-chain-contracts/src/TitheRouter.sol).
///         route() pulls `gross` from msg.sender (this escrow) and splits
///         90% recipient + 10% Public Fund Safe, atomic. purpose must be titheable.
interface ITitheRouter {
    function route(address recipient, uint256 grossAmount, bytes32 purpose)
        external
        returns (uint256 titheAmount, uint256 netAmount);
}

/// @notice Adherent SBT (50-infra/etzhayyim-membership-contract). Non-transferable
///         membership. balanceOf > 0 == covenant member.
interface IAdherentSBT {
    function balanceOf(address owner) external view returns (uint256);
}

/// @notice Charter compliance registry (same gate TitheRouter uses).
interface ICharterComplianceRegistry {
    function isNonAlignedAddress(address subject) external view returns (bool);
}

/// @title MishmarBondEscrow — data-availability "守れば信、失えば損" primitive.
///
/// @notice ADR-2606082100 (Mishmar Storage Covenant). A type-faithful remap of
///         ClaimStakeEscrow (ADR-2604261717) from "claim truth" to "data
///         availability". A pinner posts a REFUNDABLE, NON-YIELDING bond to keep
///         `rootCid` available for `durationEpochs`. The kotoba-datomic witness
///         quorum (>=K-of-N, ADR-2605231400) attests availability on challenge.
///
///         Lifecycle:
///           1. postPin   — pinner deposits `bond`; enters Pinned; expiry set.
///                          gated: Adherent SBT held + Charter-compliant.
///                          `rootCid` MUST already be committed via
///                          AnchorBridge.commitRoot (cross-checked off-chain by
///                          the relayer/kotoba per AnchorBridge's policy-layer model).
///           2. challenge — a registered witness issues a random-block availability
///                          challenge (nonce); enters Challenged; proof window opens.
///           3a. proveAvailability — pinner submits >=quorumThreshold DISTINCT
///                          registered-witness signatures over
///                          keccak256(pinId, nonce, address(this), chainid).
///                          → back to Pinned; emits RetainerEarned (reward is
///                          OFF-CHAIN social-capital + mKOTO, never paid here).
///           3b. slash    — proof window elapsed with no valid proof. bond is
///                          routed to the COMMONS via TitheRouter (90% retainer
///                          pool that funds honest pinners + 10% Public Fund).
///                          NOTHING goes to a competing staker — no extraction game.
///           4. release   — after expiry, no open challenge → bond returned IN
///                          FULL. Never more than principal (anti-usury / Yobel).
///           5. yobelRelease — Shmita/Yobel cycle: owner/Yobel-registry force-
///                          releases the bond and FORGIVES the obligation.
///
/// @dev    Differences vs ClaimStakeEscrow, all enforcing Charter §2(b) + Yobel:
///           - NO challenger counter-bond and NO challenger payout (no bounty /
///             no extraction). Challenges come from the trusted witness set.
///           - NO winner/reward split to individuals. Slashed value → commons only.
///           - Honest release returns EXACTLY the principal (no yield / interest).
///           - Single arbiter → >=K-of-N witness quorum (EOA via ECDSA, contract
///             cells via ERC-1271).
///
/// @dev    CEI strict; single-token; failed transfers revert. No ReentrancyGuard
///         needed (no external callback on the success path).
contract MishmarBondEscrow {
    // ── Immutable wiring ─────────────────────────────────────────────────────
    IERC20  public immutable bondToken;     // GCC (same as ClaimStakeEscrow)
    ITitheRouter public immutable tithe;    // commons router (slash destination)
    IAdherentSBT public immutable sbt;      // membership gate
    ICharterComplianceRegistry public immutable charters;
    address public immutable retainerPool;  // commons pool funding honest pinners
                                            // (slash recipient; 90/10 via TitheRouter)

    /// keccak256("storage-slash") — must be titheable in TitheRouter policy.
    bytes32 public constant PURPOSE_STORAGE_SLASH = keccak256("storage-slash");

    // ── Admin / policy ───────────────────────────────────────────────────────
    address public owner;
    address public yobelRegistry;           // may force jubilee release

    uint64 public constant EPOCH = 1 days;  // 1 durationEpoch == 1 day
    uint64 public constant MIN_DURATION_EPOCHS = 1;
    uint64 public constant MAX_DURATION_EPOCHS = 365 * 7; // 7yr (Shmita horizon)
    uint64 public constant DEFAULT_PROOF_WINDOW = 1 days; // time to answer a challenge
    uint64 public proofWindow = DEFAULT_PROOF_WINDOW;

    uint256 public minBond;                 // anti-spam floor
    uint16  public quorumThreshold;         // K in K-of-N (default 3)

    /// Active witness set (the Murakumo fleet cell signer keys / Safes).
    /// hash(rootCid) % N subset-selection is an OFF-CHAIN relayer policy
    /// (AnchorBridge model); on-chain we only require K distinct ACTIVE witnesses.
    mapping(address => bool) public isWitness;
    uint16 public witnessCount;

    enum State { None, Pinned, Challenged, Slashed, Released, Forgiven }

    struct Pin {
        bytes32 pinId;
        bytes32 rootCid;        // == AnchorBridge committed root
        bytes32 didHash;        // pinner DID hash (observability)
        uint256 bond;
        uint64  postedAt;
        uint64  expiresAt;      // postedAt + durationEpochs*EPOCH
        address pinner;
        State   state;
    }
    struct Chal {
        bytes32 nonce;
        uint64  postedAt;       // proof due by postedAt + proofWindow
        address challenger;     // a registered witness
    }

    mapping(bytes32 => Pin)  internal _pins;
    mapping(bytes32 => Chal) internal _chals;

    // ── Events ───────────────────────────────────────────────────────────────
    event Pinned(bytes32 indexed pinId, bytes32 indexed rootCid, address indexed pinner, bytes32 didHash, uint256 bond, uint64 expiresAt);
    event Challenged(bytes32 indexed pinId, bytes32 nonce, address indexed challenger, uint64 proofDueAt);
    event Proven(bytes32 indexed pinId, uint64 epoch, uint16 attestations);
    event RetainerEarned(bytes32 indexed pinId, address indexed pinner, bytes32 indexed rootCid, uint64 epoch); // consumed off-chain by mKOTO L6 (social-capital-denominated)
    event Slashed(bytes32 indexed pinId, uint256 bond, uint256 toRetainer, uint256 toPublicFund);
    event Released(bytes32 indexed pinId, uint256 bond);
    event Forgiven(bytes32 indexed pinId, uint256 bond); // Yobel
    event WitnessUpdated(address indexed witness, bool active);
    event PolicyUpdated(uint16 quorumThreshold, uint256 minBond, uint64 proofWindow);
    event YobelRegistryUpdated(address indexed oldReg, address indexed newReg);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // ── Errors ───────────────────────────────────────────────────────────────
    error NotOwner();
    error NotWitness();
    error NotYobel();
    error ZeroAddress();
    error ZeroId();
    error PinAlreadyExists();
    error PinNotFound();
    error InvalidState();
    error BondTooSmall();
    error InvalidDuration();
    error NotMember();
    error CharterNonCompliant();
    error NotExpired();
    error ChallengeOpen();
    error ProofWindowOpen();
    error ProofWindowClosed();
    error QuorumNotMet();
    error DuplicateSigner();
    error SignerNotWitness();
    error InvalidQuorumPolicy();
    error TransferFailed();
    error ApproveFailed();

    modifier onlyOwner() { if (msg.sender != owner) revert NotOwner(); _; }
    modifier onlyWitness() { if (!isWitness[msg.sender]) revert NotWitness(); _; }

    constructor(
        IERC20 bondToken_,
        ITitheRouter tithe_,
        IAdherentSBT sbt_,
        ICharterComplianceRegistry charters_,
        address retainerPool_,
        address owner_
    ) {
        if (address(bondToken_) == address(0) || address(tithe_) == address(0)
            || address(sbt_) == address(0) || address(charters_) == address(0)
            || retainerPool_ == address(0)) revert ZeroAddress();
        bondToken = bondToken_;
        tithe = tithe_;
        sbt = sbt_;
        charters = charters_;
        retainerPool = retainerPool_;
        owner = owner_ == address(0) ? msg.sender : owner_;

        quorumThreshold = 3;       // >=3-of-5 (ADR-2605231400)
        minBond = 1 ether;         // 1 GCC
        proofWindow = DEFAULT_PROOF_WINDOW;

        emit OwnershipTransferred(address(0), owner);
        emit PolicyUpdated(quorumThreshold, minBond, proofWindow);
    }

    // ── Pinner path ────────────────────────────────────────────────────────
    /// @notice Lock `bond`. Caller must `bondToken.approve(escrow, bond)` first.
    ///         `rootCid` MUST equal a root committed via AnchorBridge.commitRoot
    ///         (enforced off-chain by the relayer/kotoba — AnchorBridge policy model).
    function postPin(
        bytes32 pinId,
        bytes32 rootCid,
        bytes32 didHash,
        uint256 bond,
        uint64 durationEpochs
    ) external {
        if (pinId == bytes32(0) || rootCid == bytes32(0)) revert ZeroId();
        if (_pins[pinId].state != State.None) revert PinAlreadyExists();
        if (bond < minBond) revert BondTooSmall();
        if (durationEpochs < MIN_DURATION_EPOCHS || durationEpochs > MAX_DURATION_EPOCHS) revert InvalidDuration();
        // covenant gate (mirrors TitheRouter's compliance gate)
        if (sbt.balanceOf(msg.sender) == 0) revert NotMember();
        if (charters.isNonAlignedAddress(msg.sender)) revert CharterNonCompliant();

        if (!bondToken.transferFrom(msg.sender, address(this), bond)) revert TransferFailed();

        uint64 nowTs = uint64(block.timestamp);
        uint64 expiresAt = nowTs + durationEpochs * EPOCH;
        _pins[pinId] = Pin({
            pinId: pinId,
            rootCid: rootCid,
            didHash: didHash,
            bond: bond,
            postedAt: nowTs,
            expiresAt: expiresAt,
            pinner: msg.sender,
            state: State.Pinned
        });

        emit Pinned(pinId, rootCid, msg.sender, didHash, bond, expiresAt);
    }

    // ── Witness challenge path ───────────────────────────────────────────────
    /// @notice A registered witness issues an availability challenge. No
    ///         counter-bond, no bounty (anti-extraction). Re-challengeable after
    ///         a successful proof.
    function challenge(bytes32 pinId, bytes32 nonce) external onlyWitness {
        Pin storage p = _pins[pinId];
        if (p.state == State.None) revert PinNotFound();
        if (p.state != State.Pinned) revert InvalidState();

        p.state = State.Challenged;
        _chals[pinId] = Chal({ nonce: nonce, postedAt: uint64(block.timestamp), challenger: msg.sender });

        emit Challenged(pinId, nonce, msg.sender, uint64(block.timestamp) + proofWindow);
    }

    /// @notice Pinner answers a challenge with >=quorumThreshold DISTINCT
    ///         active-witness signatures over
    ///         keccak256(pinId, nonce, address(this), chainid).
    ///         `signers[i]` is the claimed witness for `sigs[i]`; each verified
    ///         as EOA (ECDSA) or contract cell (ERC-1271).
    function proveAvailability(
        bytes32 pinId,
        address[] calldata signers,
        bytes[] calldata sigs
    ) external {
        Pin storage p = _pins[pinId];
        if (p.state == State.None) revert PinNotFound();
        if (p.state != State.Challenged) revert InvalidState();

        Chal storage ch = _chals[pinId];
        if (block.timestamp > uint256(ch.postedAt) + uint256(proofWindow)) revert ProofWindowClosed();
        if (signers.length != sigs.length || signers.length < quorumThreshold) revert QuorumNotMet();

        bytes32 payloadHash = keccak256(abi.encode(pinId, ch.nonce, address(this), block.chainid));
        bytes32 ethSignedHash = ECDSA.toEthSignedMessageHash(payloadHash);

        uint16 valid;
        for (uint256 i = 0; i < signers.length; i++) {
            address s = signers[i];
            if (!isWitness[s]) revert SignerNotWitness();
            // distinctness (N is small; O(n^2) acceptable)
            for (uint256 j = 0; j < i; j++) {
                if (signers[j] == s) revert DuplicateSigner();
            }
            if (_isValidWitnessSig(s, payloadHash, ethSignedHash, sigs[i])) {
                valid++;
            }
        }
        if (valid < quorumThreshold) revert QuorumNotMet();

        // proof good → back to Pinned; reward is emitted, never transferred here.
        p.state = State.Pinned;
        uint64 epoch = uint64(block.timestamp) / EPOCH;
        emit Proven(pinId, epoch, valid);
        emit RetainerEarned(pinId, p.pinner, p.rootCid, epoch);
    }

    /// @notice Slash a pin whose proof window elapsed with no valid proof.
    ///         Permissionless. Bond → commons via TitheRouter (90% retainer
    ///         pool + 10% Public Fund). No payout to any individual.
    function slash(bytes32 pinId) external {
        Pin storage p = _pins[pinId];
        if (p.state == State.None) revert PinNotFound();
        if (p.state != State.Challenged) revert InvalidState();

        Chal storage ch = _chals[pinId];
        if (block.timestamp <= uint256(ch.postedAt) + uint256(proofWindow)) revert ProofWindowOpen();

        p.state = State.Slashed;
        uint256 bond = p.bond;

        // approve + route (TitheRouter.route pulls from this escrow).
        if (!bondToken.approve(address(tithe), bond)) revert ApproveFailed();
        (uint256 toPublicFund, uint256 toRetainer) = tithe.route(retainerPool, bond, PURPOSE_STORAGE_SLASH);

        emit Slashed(pinId, bond, toRetainer, toPublicFund);
    }

    /// @notice After expiry with no open challenge → return bond IN FULL.
    ///         No interest (Yobel/anti-usury). Permissionless (anyone may poke).
    function release(bytes32 pinId) external {
        Pin storage p = _pins[pinId];
        if (p.state == State.None) revert PinNotFound();
        if (p.state != State.Pinned) revert InvalidState();
        if (block.timestamp < uint256(p.expiresAt)) revert NotExpired();

        p.state = State.Released;
        uint256 bond = p.bond;
        if (!bondToken.transfer(p.pinner, bond)) revert TransferFailed();

        emit Released(pinId, bond);
    }

    /// @notice Yobel/Shmita jubilee: force-release the bond and forgive the
    ///         remaining availability obligation. Owner or bound Yobel registry only.
    ///         Works from Pinned OR Challenged (a pending challenge is forgiven too).
    function yobelRelease(bytes32 pinId) external {
        if (msg.sender != owner && msg.sender != yobelRegistry) revert NotYobel();
        Pin storage p = _pins[pinId];
        if (p.state == State.None) revert PinNotFound();
        if (p.state != State.Pinned && p.state != State.Challenged) revert InvalidState();

        p.state = State.Forgiven;
        uint256 bond = p.bond;
        if (!bondToken.transfer(p.pinner, bond)) revert TransferFailed();

        emit Forgiven(pinId, bond);
    }

    // ── Signature verification (mirrors ClaimStakeEscrow._isValidArbiterSig) ──
    function _isValidWitnessSig(
        address expected,
        bytes32 payloadHash,
        bytes32 ethSignedHash,
        bytes calldata sig
    ) internal view returns (bool) {
        bytes memory sigMem = sig;
        (address recovered, ECDSA.RecoverError err) = ECDSA.tryRecover(ethSignedHash, sigMem);
        if (err == ECDSA.RecoverError.NoError && recovered == expected) return true;
        if (expected.code.length == 0) return false; // EOA mismatch, no contract path
        (bool ok, bytes memory ret) = expected.staticcall(
            abi.encodeWithSelector(IERC1271.isValidSignature.selector, payloadHash, sig)
        );
        return ok && ret.length >= 32 && abi.decode(ret, (bytes4)) == ERC1271_MAGIC_VALUE;
    }

    // ── Admin ────────────────────────────────────────────────────────────────
    function setWitness(address witness, bool active) external onlyOwner {
        if (witness == address(0)) revert ZeroAddress();
        bool cur = isWitness[witness];
        if (cur == active) return;
        isWitness[witness] = active;
        if (active) witnessCount++; else witnessCount--;
        emit WitnessUpdated(witness, active);
    }

    function setPolicy(uint16 newQuorumThreshold, uint256 newMinBond, uint64 newProofWindow) external onlyOwner {
        if (newQuorumThreshold == 0 || newProofWindow == 0) revert InvalidQuorumPolicy();
        quorumThreshold = newQuorumThreshold;
        minBond = newMinBond;
        proofWindow = newProofWindow;
        emit PolicyUpdated(newQuorumThreshold, newMinBond, newProofWindow);
    }

    function setYobelRegistry(address newReg) external onlyOwner {
        emit YobelRegistryUpdated(yobelRegistry, newReg);
        yobelRegistry = newReg;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert NotOwner();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    // ── Views ────────────────────────────────────────────────────────────────
    function pins(bytes32 pinId) external view returns (Pin memory) { return _pins[pinId]; }
    function challenges(bytes32 pinId) external view returns (Chal memory) { return _chals[pinId]; }
}
