// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.8.19;

import {Math} from "@openzeppelin/contracts@4.9.3/utils/math/Math.sol";
import "github.com/yearn/yearn-vaults/blob/v0.4.6/contracts/BaseStrategy.sol";
import "./interfaces/CurveInterfaces.sol";

contract StrategyCurveNoBoostClonable is BaseStrategy {
    using SafeERC20 for IERC20;

    /* ========== STATE VARIABLES ========== */

    /// @notice Curve gauge contract
    IGauge public gauge;

    // this means all of our fee values are in basis points
    uint256 internal constant FEE_DENOMINATOR = 10000;

    /// @notice The address of our base token (CRV for Curve, BAL for Balancer, etc.).
    IERC20 public constant crv =
        IERC20(0x712b3d230F3C1c19db860d80619288b1F0BDd0Bd);

    /// @notice The address of Gnosis' CRV minter. Gibs CRV!
    IMinter public constant mintr =
        IMinter(0xabC000d88f23Bb45525E447528DBF656A9D55bf5);

    // ySwaps stuff
    /// @notice The address of our ySwaps trade factory.
    address public tradeFactory;

    /// @notice Array of any extra rewards tokens this Convex pool may have.
    address[] public rewardsTokens;

    /// @notice Will only be true on the original deployed contract and not on clones; we dont want to clone a clone.
    bool public isOriginal = true;

    /// @notice Used to track the deployed version of this contract. Maps to releases in the CurveVaultFactory repo.
    /// @dev We append "d" here because this strategy directly deposits to the gauge instead of the normal proxy+voter method.
    string public constant strategyVersion = "3.0.2d";

    /* ========== CONSTRUCTOR ========== */

    constructor(
        address _vault,
        address _tradeFactory,
        address _gauge
    ) BaseStrategy(_vault) {
        _initializeStrat(_tradeFactory, _gauge);
    }

    /* ========== CLONING ========== */

    event Cloned(address indexed clone);

    /**
     * @notice Use this to clone an exact copy of this strategy on another vault.
     * @dev In practice, this will only be called by the factory on the template contract.
     * @param _vault Vault address we are targeting with this strategy.
     * @param _strategist Address to grant the strategist role.
     * @param _rewards If we have any strategist rewards, send them here.
     * @param _keeper Address to grant the keeper role.
     * @param _tradeFactory Our trade factory address.
     * @param _gauge Gauge address for this strategy.
     * @return newStrategy Address of our new cloned strategy.
     */
    function cloneStrategyCurveBoosted(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _tradeFactory,
        address _gauge
    ) external returns (address newStrategy) {
        // dont clone a clone
        if (!isOriginal) {
            revert("Cant clone a clone");
        }

        // Copied from https://github.com/optionality/clone-factory/blob/master/contracts/CloneFactory.sol
        bytes20 addressBytes = bytes20(address(this));
        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(
                clone_code,
                0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000
            )
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(
                add(clone_code, 0x28),
                0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000
            )
            newStrategy := create(0, clone_code, 0x37)
        }

        StrategyCurveNoBoostClonable(newStrategy).initialize(
            _vault,
            _strategist,
            _rewards,
            _keeper,
            _tradeFactory,
            _gauge
        );

        emit Cloned(newStrategy);
    }

    /**
     * @notice Initialize the strategy.
     * @dev This should only be called by the clone function above.
     * @param _vault Vault address we are targeting with this strategy.
     * @param _strategist Address to grant the strategist role.
     * @param _rewards If we have any strategist rewards, send them here.
     * @param _keeper Address to grant the keeper role.
     * @param _tradeFactory Our trade factory address.
     * @param _gauge Gauge address for this strategy.
     */
    function initialize(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _tradeFactory,
        address _gauge
    ) public {
        _initialize(_vault, _strategist, _rewards, _keeper);
        _initializeStrat(_tradeFactory, _gauge);
    }

    // this is called by our original strategy, as well as any clones
    function _initializeStrat(address _tradeFactory, address _gauge) internal {
        // make sure that we havent initialized this before
        if (address(gauge) != address(0)) {
            revert("Already initialized");
        }

        // 1:1 assignments
        tradeFactory = _tradeFactory;
        gauge = IGauge(_gauge);

        // want = Curve LP
        want.approve(_gauge, type(uint256).max);

        // set up our baseStrategy vars
        minReportDelay = 21 days;
        maxReportDelay = 365 days;
        creditThreshold = 50_000e18;

        // ySwaps setup
        _setUpTradeFactory();
    }

    /* ========== VIEWS ========== */

    /// @notice Strategy name.
    function name() external view override returns (string memory) {
        return
            string(
                abi.encodePacked(
                    "StrategyCurveBoostedFactory-",
                    IDetails(address(want)).symbol()
                )
            );
    }

    /// @notice Balance of want staked in Curves gauge.
    function stakedBalance() public view returns (uint256) {
        return gauge.balanceOf(address(this));
    }

    /// @notice Balance of want sitting in our strategy.
    function balanceOfWant() public view returns (uint256) {
        return want.balanceOf(address(this));
    }

    /// @notice Total assets the strategy holds, sum of loose and staked want.
    function estimatedTotalAssets() public view override returns (uint256) {
        return balanceOfWant() + stakedBalance();
    }

    /* ========== CORE STRATEGY FUNCTIONS ========== */

    function prepareReturn(
        uint256 _debtOutstanding
    )
        internal
        override
        returns (uint256 _profit, uint256 _loss, uint256 _debtPayment)
    {
        // rewards will be converted later with mev protection by yswaps (tradeFactory)

        // claim extra rewards if we have them
        if (rewardsTokens.length > 0) {
            gauge.claim_rewards();
        }

        // Mintr CRV emissions
        mintr.mint(address(gauge));

        // serious loss should never happen, but if it does (for instance, if Curve is hacked), lets record it accurately
        uint256 assets = estimatedTotalAssets();
        uint256 debt = vault.strategies(address(this)).totalDebt;

        // if assets are greater than debt, things are working great!
        if (assets >= debt) {
            unchecked {
                _profit = assets - debt;
            }
            _debtPayment = _debtOutstanding;

            uint256 toFree = _profit + _debtPayment;

            // freed is math.min(wantBalance, toFree)
            (uint256 freed, ) = liquidatePosition(toFree);

            if (toFree > freed) {
                if (_debtPayment > freed) {
                    _debtPayment = freed;
                    _profit = 0;
                } else {
                    unchecked {
                        _profit = freed - _debtPayment;
                    }
                }
            }
        }
        // if assets are less than debt, we are in trouble. dont worry about withdrawing here, just report losses
        else {
            unchecked {
                _loss = debt - assets;
            }
        }
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        // if in emergency exit, we dont want to deploy any more funds
        if (emergencyExit) {
            return;
        }

        // Send all of our LP tokens to the proxy and deposit to the gauge
        uint256 _toInvest = balanceOfWant();
        if (_toInvest > 0) {
            gauge.deposit(_toInvest);
        }
    }

    function liquidatePosition(
        uint256 _amountNeeded
    ) internal override returns (uint256 _liquidatedAmount, uint256 _loss) {
        // check our loose want
        uint256 _wantBal = balanceOfWant();
        if (_amountNeeded > _wantBal) {
            uint256 _stakedBal = stakedBalance();
            if (_stakedBal > 0) {
                uint256 _neededFromStaked;
                unchecked {
                    _neededFromStaked = _amountNeeded - _wantBal;
                }
                // withdraw whatever extra funds we need
                gauge.withdraw(Math.min(_stakedBal, _neededFromStaked));
            }
            uint256 _withdrawnBal = balanceOfWant();
            _liquidatedAmount = Math.min(_amountNeeded, _withdrawnBal);
            unchecked {
                _loss = _amountNeeded - _liquidatedAmount;
            }
        } else {
            // we have enough balance to cover the liquidation available
            return (_amountNeeded, 0);
        }
    }

    // fire sale, get rid of it all!
    function liquidateAllPositions() internal override returns (uint256) {
        uint256 _stakedBal = stakedBalance();
        if (_stakedBal > 0) {
            // dont bother withdrawing zero, save gas where we can
            gauge.withdraw(_stakedBal);
        }
        return balanceOfWant();
    }

    // migrate our want token to a new strategy if needed, as well as our CRV
    function prepareMigration(address _newStrategy) internal override {
        uint256 stakedBal = stakedBalance();
        if (stakedBal > 0) {
            gauge.withdraw(stakedBal);
        }
        uint256 crvBal = crv.balanceOf(address(this));

        if (crvBal > 0) {
            crv.safeTransfer(_newStrategy, crvBal);
        }
    }

    // want is blocked by default, add any other tokens to protect from gov here.
    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}

    /* ========== YSWAPS ========== */

    /**
     * @notice Use to add or update rewards, rebuilds tradefactory too
     * @dev Do this before updating trade factory if we have extra rewards. Can only be called by governance.
     * @param _rewards Rewards tokens to add to our trade factory.
     */
    function updateRewards(address[] memory _rewards) external onlyGovernance {
        address tf = tradeFactory;
        _removeTradeFactoryPermissions(true);
        rewardsTokens = _rewards;

        tradeFactory = tf;
        _setUpTradeFactory();
    }

    /**
     * @notice Use to update our trade factory.
     * @dev Can only be called by governance.
     * @param _newTradeFactory Address of new trade factory.
     */
    function updateTradeFactory(
        address _newTradeFactory
    ) external onlyGovernance {
        require(
            _newTradeFactory != address(0),
            "Cant remove with this function"
        );
        _removeTradeFactoryPermissions(true);
        tradeFactory = _newTradeFactory;
        _setUpTradeFactory();
    }

    function _setUpTradeFactory() internal {
        // approve and set up trade factory
        address _tradeFactory = tradeFactory;
        address _want = address(want);

        ITradeFactory tf = ITradeFactory(_tradeFactory);
        crv.approve(_tradeFactory, type(uint256).max);
        tf.enable(address(crv), _want);

        // enable for all rewards tokens too
        for (uint256 i; i < rewardsTokens.length; ++i) {
            address _rewardsToken = rewardsTokens[i];
            IERC20(_rewardsToken).approve(_tradeFactory, type(uint256).max);
            tf.enable(_rewardsToken, _want);
        }
    }

    /**
     * @notice Use this to remove permissions from our current trade factory.
     * @dev Once this is called, setUpTradeFactory must be called to get things working again.
     * @param _disableTf Specify whether to disable the tradefactory when removing. Option given in case we need to get
     *  around a reverting disable.
     */
    function removeTradeFactoryPermissions(
        bool _disableTf
    ) external onlyVaultManagers {
        _removeTradeFactoryPermissions(_disableTf);
    }

    function _removeTradeFactoryPermissions(bool _disableTf) internal {
        address _tradeFactory = tradeFactory;
        if (_tradeFactory == address(0)) {
            return;
        }
        ITradeFactory tf = ITradeFactory(_tradeFactory);

        address _want = address(want);
        crv.approve(_tradeFactory, 0);
        if (_disableTf) {
            tf.disable(address(crv), _want);
        }

        // disable for all rewards tokens too
        for (uint256 i; i < rewardsTokens.length; ++i) {
            address _rewardsToken = rewardsTokens[i];
            IERC20(_rewardsToken).approve(_tradeFactory, 0);
            if (_disableTf) {
                tf.disable(_rewardsToken, _want);
            }
        }

        tradeFactory = address(0);
    }

    /* ========== KEEP3RS ========== */

    /**
     * @notice
     *  Provide a signal to the keeper that harvest() should be called.
     *
     *  Dont harvest if a strategy is inactive.
     *  If we exceed our max delay, then harvest no matter what. For
     *  our min delay, credit threshold, and manual force trigger,
     *  only harvest if our gas price is acceptable.
     *
     * @param callCostinEth The keepers estimated gas cost to call harvest() (in wei).
     * @return True if harvest() should be called, false otherwise.
     */
    function harvestTrigger(
        uint256 callCostinEth
    ) public view override returns (bool) {
        // Should not trigger if strategy is not active (no assets and no debtRatio). This means we dont need to adjust keeper job.
        if (!isActive()) {
            return false;
        }

        StrategyParams memory params = vault.strategies(address(this));
        // harvest no matter what once we reach our maxDelay
        if (block.timestamp - params.lastReport > maxReportDelay) {
            return true;
        }

        // check if the base fee gas price is higher than we allow. if it is, block harvests.
        if (!isBaseFeeAcceptable()) {
            return false;
        }

        // trigger if we want to manually harvest, but only if our gas price is acceptable
        if (forceHarvestTriggerOnce) {
            return true;
        }

        // harvest if we hit our minDelay, but only if our gas price is acceptable
        if (block.timestamp - params.lastReport > minReportDelay) {
            return true;
        }

        // harvest our credit if its above our threshold
        if (vault.creditAvailable() > creditThreshold) {
            return true;
        }

        // otherwise, we dont harvest
        return false;
    }

    /**
     * @notice Convert our keepers eth cost into want
     * @dev We dont use this since we dont factor call cost into our harvestTrigger.
     * @param _ethAmount Amount of ether spent.
     * @return Value of ether in want.
     */
    function ethToWant(
        uint256 _ethAmount
    ) public view override returns (uint256) {}
}
