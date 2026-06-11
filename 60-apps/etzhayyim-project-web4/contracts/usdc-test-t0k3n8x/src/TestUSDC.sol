// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title TestUSDC
 * @notice Etzhayyim Computing Credits (GCC) — FiatTokenV2_2 ABI-compatible token.
 *
 * Implements every public function of Circle's FiatTokenV2_2 so that any
 * integration (UI, SDK, Safe module, …) that works against FiatTokenV2_2
 * will also work against this contract without ABI changes.
 *
 * Differences from production FiatTokenV2_2:
 *   - Single non-upgradeable deployment (no proxy)
 *   - `initialize` is called in the constructor
 *   - Balance/blacklist are NOT bit-packed (clarity > gas savings on testnet)
 */
contract TestUSDC {
    // ──────────────────────────────────────────────
    // ERC-20 storage
    // ──────────────────────────────────────────────
    string public name;
    string public symbol;
    uint8 public constant decimals = 6;
    string public currency;
    uint256 public totalSupply;

    mapping(address => uint256) internal _balances;
    mapping(address => mapping(address => uint256)) internal _allowances;

    // ──────────────────────────────────────────────
    // Roles
    // ──────────────────────────────────────────────
    address public owner;
    address public masterMinter;
    address public pauser;
    address public blacklister;
    address public rescuer;

    // ──────────────────────────────────────────────
    // Minter state
    // ──────────────────────────────────────────────
    mapping(address => bool) internal _minters;
    mapping(address => uint256) internal _minterAllowances;

    // ──────────────────────────────────────────────
    // Blacklist / Pause
    // ──────────────────────────────────────────────
    mapping(address => bool) internal _blacklisted;
    bool public paused;

    // ──────────────────────────────────────────────
    // EIP-712 / EIP-2612 / EIP-3009
    // ──────────────────────────────────────────────
    bytes32 public constant DOMAIN_TYPEHASH =
        keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)");

    bytes32 public constant PERMIT_TYPEHASH =
        keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");

    bytes32 public constant TRANSFER_WITH_AUTHORIZATION_TYPEHASH =
        keccak256(
            "TransferWithAuthorization(address from,address to,uint256 value,uint256 validAfter,uint256 validBefore,bytes32 nonce)"
        );

    bytes32 public constant RECEIVE_WITH_AUTHORIZATION_TYPEHASH =
        keccak256(
            "ReceiveWithAuthorization(address from,address to,uint256 value,uint256 validAfter,uint256 validBefore,bytes32 nonce)"
        );

    bytes32 public constant CANCEL_AUTHORIZATION_TYPEHASH =
        keccak256("CancelAuthorization(address authorizer,bytes32 nonce)");

    // Cached domain separator (rebuilt on first use per-chain)
    bytes32 private _cachedDomainSeparator;
    uint256 private _cachedChainId;

    mapping(address => uint256) public nonces; // EIP-2612 sequential nonces
    mapping(address => mapping(bytes32 => bool)) internal _authorizationStates; // EIP-3009

    // ──────────────────────────────────────────────
    // Version (matches USDC V2)
    // ──────────────────────────────────────────────
    string public constant version = "2";

    // ──────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Mint(address indexed minter, address indexed to, uint256 amount);
    event Burn(address indexed burner, uint256 amount);
    event MinterConfigured(address indexed minter, uint256 minterAllowedAmount);
    event MinterRemoved(address indexed oldMinter);
    event MasterMinterChanged(address indexed newMasterMinter);
    event Blacklisted(address indexed _account);
    event UnBlacklisted(address indexed _account);
    event BlacklisterChanged(address indexed newBlacklister);
    event Pause();
    event Unpause();
    event PauserChanged(address indexed newAddress);
    event OwnershipTransferred(address previousOwner, address newOwner);
    event RescuerChanged(address indexed newRescuer);
    event AuthorizationUsed(address indexed authorizer, bytes32 indexed nonce);
    event AuthorizationCanceled(address indexed authorizer, bytes32 indexed nonce);

    // ──────────────────────────────────────────────
    // Modifiers
    // ──────────────────────────────────────────────
    modifier onlyOwner() {
        require(msg.sender == owner, "Ownable: caller is not the owner");
        _;
    }

    modifier onlyMasterMinter() {
        require(msg.sender == masterMinter, "FiatToken: caller is not the masterMinter");
        _;
    }

    modifier onlyMinters() {
        require(_minters[msg.sender], "FiatToken: caller is not a minter");
        _;
    }

    modifier onlyPauser() {
        require(msg.sender == pauser, "FiatToken: caller is not the pauser");
        _;
    }

    modifier onlyBlacklister() {
        require(msg.sender == blacklister, "FiatToken: caller is not the blacklister");
        _;
    }

    modifier onlyRescuer() {
        require(msg.sender == rescuer, "FiatToken: caller is not the rescuer");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Pausable: paused");
        _;
    }

    modifier notBlacklisted(address account) {
        require(!_blacklisted[account], "Blacklistable: account is blacklisted");
        _;
    }

    // ──────────────────────────────────────────────
    // Constructor (replaces initialize chain)
    // ──────────────────────────────────────────────
    constructor(
        string memory _name,
        string memory _symbol,
        string memory _currency,
        address _masterMinter,
        address _pauser,
        address _blacklister,
        address _owner
    ) {
        require(_masterMinter != address(0), "zero masterMinter");
        require(_pauser != address(0), "zero pauser");
        require(_blacklister != address(0), "zero blacklister");
        require(_owner != address(0), "zero owner");

        name = _name;
        symbol = _symbol;
        currency = _currency;
        masterMinter = _masterMinter;
        pauser = _pauser;
        blacklister = _blacklister;
        owner = _owner;
        rescuer = _owner;

        _cachedChainId = block.chainid;
        _cachedDomainSeparator = _buildDomainSeparator();
    }

    // ══════════════════════════════════════════════
    // ERC-20
    // ══════════════════════════════════════════════

    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }

    function allowance(address _owner, address spender) external view returns (uint256) {
        return _allowances[_owner][spender];
    }

    function approve(address spender, uint256 value)
        external
        whenNotPaused
        notBlacklisted(msg.sender)
        notBlacklisted(spender)
        returns (bool)
    {
        _approve(msg.sender, spender, value);
        return true;
    }

    function transfer(address to, uint256 value)
        external
        whenNotPaused
        notBlacklisted(msg.sender)
        notBlacklisted(to)
        returns (bool)
    {
        _transfer(msg.sender, to, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value)
        external
        whenNotPaused
        notBlacklisted(msg.sender)
        notBlacklisted(from)
        notBlacklisted(to)
        returns (bool)
    {
        uint256 currentAllowance = _allowances[from][msg.sender];
        require(currentAllowance >= value, "ERC20: insufficient allowance");
        unchecked {
            _approve(from, msg.sender, currentAllowance - value);
        }
        _transfer(from, to, value);
        return true;
    }

    function increaseAllowance(address spender, uint256 increment)
        external
        whenNotPaused
        notBlacklisted(msg.sender)
        notBlacklisted(spender)
        returns (bool)
    {
        _approve(msg.sender, spender, _allowances[msg.sender][spender] + increment);
        return true;
    }

    function decreaseAllowance(address spender, uint256 decrement)
        external
        whenNotPaused
        notBlacklisted(msg.sender)
        notBlacklisted(spender)
        returns (bool)
    {
        uint256 currentAllowance = _allowances[msg.sender][spender];
        require(currentAllowance >= decrement, "ERC20: decreased allowance below zero");
        unchecked {
            _approve(msg.sender, spender, currentAllowance - decrement);
        }
        return true;
    }

    // ══════════════════════════════════════════════
    // Minting / Burning
    // ══════════════════════════════════════════════

    function mint(address to, uint256 amount)
        external
        whenNotPaused
        onlyMinters
        notBlacklisted(msg.sender)
        notBlacklisted(to)
        returns (bool)
    {
        require(to != address(0), "FiatToken: mint to the zero address");
        require(amount > 0, "FiatToken: mint amount not greater than 0");

        uint256 mintAllowance = _minterAllowances[msg.sender];
        require(amount <= mintAllowance, "FiatToken: mint amount exceeds minterAllowance");
        unchecked {
            _minterAllowances[msg.sender] = mintAllowance - amount;
        }

        totalSupply += amount;
        _balances[to] += amount;

        emit Mint(msg.sender, to, amount);
        emit Transfer(address(0), to, amount);
        return true;
    }

    function burn(uint256 amount) external whenNotPaused onlyMinters notBlacklisted(msg.sender) {
        require(amount > 0, "FiatToken: burn amount not greater than 0");
        uint256 balance = _balances[msg.sender];
        require(balance >= amount, "FiatToken: burn amount exceeds balance");
        unchecked {
            _balances[msg.sender] = balance - amount;
        }
        totalSupply -= amount;

        emit Burn(msg.sender, amount);
        emit Transfer(msg.sender, address(0), amount);
    }

    function configureMinter(address minter, uint256 minterAllowedAmount)
        external
        whenNotPaused
        onlyMasterMinter
        returns (bool)
    {
        _minters[minter] = true;
        _minterAllowances[minter] = minterAllowedAmount;
        emit MinterConfigured(minter, minterAllowedAmount);
        return true;
    }

    function removeMinter(address minter) external onlyMasterMinter returns (bool) {
        _minters[minter] = false;
        _minterAllowances[minter] = 0;
        emit MinterRemoved(minter);
        return true;
    }

    function isMinter(address account) external view returns (bool) {
        return _minters[account];
    }

    function minterAllowance(address minter) external view returns (uint256) {
        return _minterAllowances[minter];
    }

    function updateMasterMinter(address _newMasterMinter) external onlyOwner {
        require(_newMasterMinter != address(0), "FiatToken: new masterMinter is the zero address");
        masterMinter = _newMasterMinter;
        emit MasterMinterChanged(_newMasterMinter);
    }

    // ══════════════════════════════════════════════
    // Blacklisting
    // ══════════════════════════════════════════════

    function isBlacklisted(address account) external view returns (bool) {
        return _blacklisted[account];
    }

    function blacklist(address account) external onlyBlacklister {
        _blacklisted[account] = true;
        emit Blacklisted(account);
    }

    function unBlacklist(address account) external onlyBlacklister {
        _blacklisted[account] = false;
        emit UnBlacklisted(account);
    }

    function updateBlacklister(address _newBlacklister) external onlyOwner {
        require(_newBlacklister != address(0), "FiatToken: new blacklister is the zero address");
        blacklister = _newBlacklister;
        emit BlacklisterChanged(_newBlacklister);
    }

    // ══════════════════════════════════════════════
    // Pausing
    // ══════════════════════════════════════════════

    function pause() external onlyPauser {
        paused = true;
        emit Pause();
    }

    function unpause() external onlyPauser {
        paused = false;
        emit Unpause();
    }

    function updatePauser(address _newPauser) external onlyOwner {
        require(_newPauser != address(0), "FiatToken: new pauser is the zero address");
        pauser = _newPauser;
        emit PauserChanged(_newPauser);
    }

    // ══════════════════════════════════════════════
    // Ownership
    // ══════════════════════════════════════════════

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    // ══════════════════════════════════════════════
    // Rescuable (V1.1+)
    // ══════════════════════════════════════════════

    function rescueERC20(IERC20 tokenContract, address to, uint256 amount) external onlyRescuer {
        tokenContract.transfer(to, amount);
    }

    function updateRescuer(address newRescuer) external onlyOwner {
        require(newRescuer != address(0), "FiatToken: new rescuer is the zero address");
        rescuer = newRescuer;
        emit RescuerChanged(newRescuer);
    }

    // ══════════════════════════════════════════════
    // EIP-712 Domain Separator
    // ══════════════════════════════════════════════

    function DOMAIN_SEPARATOR() public view returns (bytes32) {
        if (block.chainid == _cachedChainId) {
            return _cachedDomainSeparator;
        }
        return _buildDomainSeparator();
    }

    function _buildDomainSeparator() private view returns (bytes32) {
        return keccak256(
            abi.encode(DOMAIN_TYPEHASH, keccak256(bytes(name)), keccak256(bytes(version)), block.chainid, address(this))
        );
    }

    // ══════════════════════════════════════════════
    // EIP-2612 Permit
    // ══════════════════════════════════════════════

    function permit(address _owner, address spender, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s)
        external
        whenNotPaused
        notBlacklisted(_owner)
        notBlacklisted(spender)
    {
        require(deadline >= block.timestamp, "FiatTokenV2: permit is expired");

        bytes32 structHash =
            keccak256(abi.encode(PERMIT_TYPEHASH, _owner, spender, value, nonces[_owner]++, deadline));
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR(), structHash));
        address recovered = ecrecover(digest, v, r, s);
        require(recovered != address(0) && recovered == _owner, "EIP2612: invalid signature");

        _approve(_owner, spender, value);
    }

    // ══════════════════════════════════════════════
    // EIP-3009 Transfer With Authorization
    // ══════════════════════════════════════════════

    function transferWithAuthorization(
        address from,
        address to,
        uint256 value,
        uint256 validAfter,
        uint256 validBefore,
        bytes32 _nonce,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external whenNotPaused notBlacklisted(from) notBlacklisted(to) {
        _requireValidAuthorization(from, _nonce, validAfter, validBefore);

        bytes32 digest = _hashTypedData(
            keccak256(
                abi.encode(TRANSFER_WITH_AUTHORIZATION_TYPEHASH, from, to, value, validAfter, validBefore, _nonce)
            )
        );
        _validateSignature(from, digest, v, r, s);

        _markAuthorizationUsed(from, _nonce);
        _transfer(from, to, value);
    }

    function receiveWithAuthorization(
        address from,
        address to,
        uint256 value,
        uint256 validAfter,
        uint256 validBefore,
        bytes32 _nonce,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external whenNotPaused notBlacklisted(from) notBlacklisted(to) {
        require(to == msg.sender, "FiatTokenV2: caller must be the payee");
        _requireValidAuthorization(from, _nonce, validAfter, validBefore);

        bytes32 digest = _hashTypedData(
            keccak256(
                abi.encode(RECEIVE_WITH_AUTHORIZATION_TYPEHASH, from, to, value, validAfter, validBefore, _nonce)
            )
        );
        _validateSignature(from, digest, v, r, s);

        _markAuthorizationUsed(from, _nonce);
        _transfer(from, to, value);
    }

    function cancelAuthorization(address authorizer, bytes32 _nonce, uint8 v, bytes32 r, bytes32 s)
        external
        whenNotPaused
    {
        require(!_authorizationStates[authorizer][_nonce], "FiatTokenV2: authorization is used or canceled");

        bytes32 digest =
            _hashTypedData(keccak256(abi.encode(CANCEL_AUTHORIZATION_TYPEHASH, authorizer, _nonce)));
        _validateSignature(authorizer, digest, v, r, s);

        _authorizationStates[authorizer][_nonce] = true;
        emit AuthorizationCanceled(authorizer, _nonce);
    }

    function authorizationState(address authorizer, bytes32 _nonce) external view returns (bool) {
        return _authorizationStates[authorizer][_nonce];
    }

    // ══════════════════════════════════════════════
    // Internal helpers
    // ══════════════════════════════════════════════

    function _transfer(address from, address to, uint256 amount) internal {
        require(from != address(0), "ERC20: transfer from the zero address");
        require(to != address(0), "ERC20: transfer to the zero address");

        uint256 fromBalance = _balances[from];
        require(fromBalance >= amount, "ERC20: transfer amount exceeds balance");
        unchecked {
            _balances[from] = fromBalance - amount;
            _balances[to] += amount;
        }
        emit Transfer(from, to, amount);
    }

    function _approve(address _owner, address spender, uint256 amount) internal {
        require(_owner != address(0), "ERC20: approve from the zero address");
        require(spender != address(0), "ERC20: approve to the zero address");
        _allowances[_owner][spender] = amount;
        emit Approval(_owner, spender, amount);
    }

    function _hashTypedData(bytes32 structHash) internal view returns (bytes32) {
        return keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR(), structHash));
    }

    function _validateSignature(address signer, bytes32 digest, uint8 v, bytes32 r, bytes32 s) internal pure {
        address recovered = ecrecover(digest, v, r, s);
        require(recovered != address(0) && recovered == signer, "EIP3009: invalid signature");
    }

    function _requireValidAuthorization(address authorizer, bytes32 _nonce, uint256 validAfter, uint256 validBefore)
        internal
        view
    {
        require(block.timestamp > validAfter, "FiatTokenV2: authorization is not yet valid");
        require(block.timestamp < validBefore, "FiatTokenV2: authorization is expired");
        require(!_authorizationStates[authorizer][_nonce], "FiatTokenV2: authorization is used or canceled");
    }

    function _markAuthorizationUsed(address authorizer, bytes32 _nonce) internal {
        _authorizationStates[authorizer][_nonce] = true;
        emit AuthorizationUsed(authorizer, _nonce);
    }
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
}
