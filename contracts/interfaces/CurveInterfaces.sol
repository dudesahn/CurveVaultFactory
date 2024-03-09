// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;

interface ICurveStrategyProxy {
    function balanceOf(address _gauge) external view returns (uint256);

    function harvest(address _gauge) external;

    function claimManyRewards(address _gauge, address[] memory _token) external;

    function deposit(address _gauge, address _token) external;

    function withdraw(
        address _gauge,
        address _token,
        uint256 _amount
    ) external returns (uint256);
}

interface ITradeFactory {
    function enable(address, address) external;

    function disable(address, address) external;
}

interface IDetails {
    // get details from curve
    function name() external view returns (string memory);

    function symbol() external view returns (string memory);
}

interface IGauge {
    function deposit(uint256) external;

    function balanceOf(address) external view returns (uint256);

    function claim_rewards() external;

    function withdraw(uint256) external;
}

interface IMinter {
    function mint(address) external;
}
