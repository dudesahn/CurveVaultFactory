// SPDX-License-Identifier: MIT
pragma solidity 0.6.12;

interface ITradeFactoryPositionsHandler {
    struct Trade {
        uint256 _id;
        address _strategy;
        address _swapper;
        address _tokenIn;
        address _tokenOut;
        uint256 _amountIn;
        uint256 _maxSlippage;
        uint256 _deadline;
    }

    event TradeCreated(
        uint256 indexed _id,
        address _strategy,
        address _swapper,
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn,
        uint256 _maxSlippage,
        uint256 _deadline
    );

    event TradeCanceled(address indexed _strategy, uint256 indexed _id);

    event TradesCanceled(address indexed _strategy, uint256[] _ids);

    event TradesSwapperChanged(
        address indexed _strategy,
        uint256[] _ids,
        address _newSwapper
    );

    function pendingTradesById(uint256)
        external
        view
        returns (
            uint256 _id,
            address _strategy,
            address _swapper,
            address _tokenIn,
            address _tokenOut,
            uint256 _amountIn,
            uint256 _maxSlippage,
            uint256 _deadline
        );

    function pendingTradesIds()
        external
        view
        returns (uint256[] memory _pendingIds);

    function pendingTradesIds(address _strategy)
        external
        view
        returns (uint256[] memory _pendingIds);

    function create(
        address _tokenIn,
        address _tokenOut,
        uint256 _amountIn,
        uint256 _deadline
    ) external returns (uint256 _id);

    function cancelPending(uint256 _id) external;

    function cancelAllPending()
        external
        returns (uint256[] memory _canceledTradesIds);

    function setStrategyAsyncSwapperAsAndChangePending(
        address _strategy,
        address _swapper,
        bool _migrateSwaps
    ) external returns (uint256[] memory _changedSwapperIds);

    function changeStrategyPendingTradesSwapper(
        address _strategy,
        address _swapper
    ) external returns (uint256[] memory _changedSwapperIds);
}
