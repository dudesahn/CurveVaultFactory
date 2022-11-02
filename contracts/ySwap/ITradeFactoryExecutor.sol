// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

interface ITradeFactoryExecutor {
    event SyncTradeExecuted(
        address indexed _strategy,
        address indexed _swapper,
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn,
        uint256 _maxSlippage,
        bytes _data,
        uint256 _receivedAmount
    );

    event AsyncTradeExecuted(uint256 indexed _id, uint256 _receivedAmount);

    event AsyncTradeExpired(uint256 indexed _id);

    event SwapperAndTokenEnabled(address indexed _swapper, address _token);

    function approvedTokensBySwappers(address _swapper)
        external
        view
        returns (address[] memory _tokens);

    function execute(
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn,
        uint256 _maxSlippage,
        bytes calldata _data
    ) external returns (uint256 _receivedAmount);

    function execute(uint256 _id, bytes calldata _data)
        external
        returns (uint256 _receivedAmount);

    function expire(uint256 _id) external returns (uint256 _freedAmount);
}
