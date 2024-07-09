// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IConvexFxn {
    function poolInfo(
        uint pid
    )
        external
        view
        returns (
            address impl,
            address gauge,
            address token,
            address rewards,
            uint8 active
        );

    function createVault(uint256 pid) external returns (address);

    function getReward() external;

    function balanceOf(address account) external view returns (uint256);

    function deposit(uint256 _value) external;

    function withdraw(uint256 _value) external;

    function rewards() external view returns (address);

    function rewardTokens(uint256 _rid) external view returns (address);

    function rewardTokenLength() external view returns (uint256);
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
