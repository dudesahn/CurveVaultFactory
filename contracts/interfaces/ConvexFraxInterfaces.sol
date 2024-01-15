// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;

interface ITradeFactory {
    function enable(address, address) external;

    function disable(address, address) external;
}

interface IOracle {
    function latestRoundData(
        address,
        address
    )
        external
        view
        returns (
            uint80 roundId,
            uint256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

interface IDetails {
    // get details from curve
    function name() external view returns (string memory);

    function symbol() external view returns (string memory);
}

interface IConvexWrapper {
    function deposit(uint256 _amount, address _to) external;

    function withdrawAndUnwrap(uint256 _amount) external;

    function balanceOf(address _user) external returns (uint256);
}

interface IConvexFrax {
    // use this to create our personal convex frax vault for this strategy to get convex's FXS boost
    function createVault(uint256 pid) external returns (address);

    function stakingToken() external returns (address);

    function getReward() external; // claim our rewards from the staking contract via our user vault

    function stakeLocked(
        uint256 _liquidity,
        uint256 _secs
    ) external returns (bytes32 kek_id);

    function stakeLockedCurveLp(
        uint256 _liquidity,
        uint256 _secs
    ) external returns (bytes32 kek_id); // stake our frax convex LP as a new kek

    function lockAdditional(bytes32 _kek_id, uint256 _addl_liq) external;

    function lockAdditionalCurveLp(bytes32 _kek_id, uint256 _addl_liq) external; // add want to an existing lock/kek

    // returns FXS first, then any other reward token, then CRV and CVX
    // this is used on newer pools
    function earned(
        address
    ) external view returns (uint256[] memory total_earned);

    // this is used for our userVault on older pools
    function earned()
        external
        view
        returns (
            address[] memory token_addresses,
            uint256[] memory total_earned
        );

    function getAllRewardTokens()
        external
        view
        returns (address[] memory token_addresses);

    function fxs() external view returns (address);

    function crv() external view returns (address);

    function cvx() external view returns (address);

    function lock_time_for_max_multiplier() external view returns (uint256);

    function lock_time_min() external view returns (uint256);

    struct LockedStake {
        bytes32 kek_id;
        uint256 start_timestamp;
        uint256 amount;
        uint256 ending_timestamp;
        uint256 multiplier; // 6 decimals of precision. 1x = 1000000
    }

    function lockedLiquidityOf(address user) external view returns (uint256);

    function lockedStakesOf(
        address _address
    ) external view returns (LockedStake[] memory);

    function withdrawLocked(bytes32 _kek_id) external;

    function withdrawLockedAndUnwrap(bytes32 _kek_id) external;
}
