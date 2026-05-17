// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.27;

/**
 * @title MockUsdc
 * @notice Minimal USDC-compatible ERC20 surface for integration tests
 *         against a local Anvil. Six decimals, no supply cap, anyone
 *         may mint. NOT for production — never deploy this to a real
 *         network.
 *
 * @dev Surface chosen to match the {IERC20} subset that
 *      `KishaPayout` actually calls: `balanceOf`, `allowance`,
 *      `approve`, `transferFrom`. The full ERC20 set is not
 *      implemented (no `transfer`, no events) — paymaster integration
 *      tests don't require them.
 */
contract MockUsdc {
    string public constant name = "Mock USDC";
    string public constant symbol = "USDC";
    uint8  public constant decimals = 6;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(allowance[from][msg.sender] >= amount, "MockUsdc: allow");
        require(balanceOf[from] >= amount,             "MockUsdc: bal");
        unchecked {
            allowance[from][msg.sender] -= amount;
            balanceOf[from] -= amount;
            balanceOf[to]   += amount;
        }
        return true;
    }
}
