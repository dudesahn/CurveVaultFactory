// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;

interface IStrategy {
    function harvest() external;
}

contract KeeperWrapper {
    /// @notice This allows anyone to call harvest() on vaults created by the factory.
    function harvestStrategy(address _strategy) external {
        IStrategy(_strategy).harvest();
    }
}
