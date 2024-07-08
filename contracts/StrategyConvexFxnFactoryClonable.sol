// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.8.19;

import {Math} from "@openzeppelin/contracts@4.9.3/utils/math/Math.sol";
import "github.com/yearn/yearn-vaults/blob/v0.4.6/contracts/BaseStrategy.sol";
import {IConvexFxn, ITradeFactory, IDetails} from "./interfaces/ConvexFxnInterfaces.sol";

contract StrategyConvexFxnFactoryClonable is BaseStrategy {
    using SafeERC20 for IERC20;

    /* ========== STATE VARIABLES ========== */

    /// @notice This is the f(x) Booster.
    IConvexFxn public constant fxnBooster =
        IConvexFxn(0xAffe966B27ba3E4Ebb8A0eC124C7b7019CC762f8);

    /// @notice This is the f(x) Pool Registry.
    IConvexFxn public constant fxnPoolRegistry =
        IConvexFxn(0xdB95d646012bB87aC2E6CD63eAb2C42323c1F5AF);

    /// @notice This is a unique numerical identifier for each Convex f(x) pool.
    uint256 public fxnPid;

    /// @notice This is the FXN gauge address for our LP token. Different from Curve gauge.
    address public fxnGauge;

    /// @notice This is the vault our strategy uses to stake on f(x) and use Convex boost.
    IConvexFxn public userVault;

    // this means all of our fee values are in basis points
    uint256 internal constant FEE_DENOMINATOR = 10000;

    /// @notice The address of our f(x) token (FXN).
    IERC20 public constant fxn =
        IERC20(0x365AccFCa291e7D3914637ABf1F7635dB165Bb09);

    // ySwaps stuff
    /// @notice The address of our ySwaps trade factory.
    address public tradeFactory;

    /// @notice Array of any extra rewards tokens this pool may have. Add CRV and CVX if those rewards start flowing.
    address[] public rewardsTokens;

    /// @notice Will only be true on the original deployed contract and not on clones; we do not want to clone a clone.
    bool public isOriginal = true;

    /// @notice Used to track the deployed version of this contract. Maps to releases in the CurveVaultFactory repo.
    string public constant strategyVersion = "4.0.2";

    /* ========== CONSTRUCTOR ========== */

    constructor(
        address _vault,
        address _tradeFactory,
        uint256 _fxnPid
    ) BaseStrategy(_vault) {
        _initializeStrat(_tradeFactory, _fxnPid);
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
     * @param _fxnPid Our fxn pool id (pid) for this strategy.
     */
    function cloneStrategyConvexFxn(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _tradeFactory,
        uint256 _fxnPid
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

        StrategyConvexFxnFactoryClonable(newStrategy).initialize(
            _vault,
            _strategist,
            _rewards,
            _keeper,
            _tradeFactory,
            _fxnPid
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
     * @param _fxnPid Our fxn pool id (pid) for this strategy.
     */
    function initialize(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _tradeFactory,
        uint256 _fxnPid
    ) public {
        _initialize(_vault, _strategist, _rewards, _keeper);
        _initializeStrat(_tradeFactory, _fxnPid);
    }

    // this is called by our original strategy, as well as any clones
    function _initializeStrat(address _tradeFactory, uint256 _fxnPid) internal {
        // make sure that we havent initialized this before
        if (fxnGauge != address(0)) {
            revert("Already initialized");
        }

        // use pid to get our staking and lp addresses, check against want
        (, address _gauge, address lptoken, , ) = fxnPoolRegistry.poolInfo(
            _fxnPid
        );
        if (address(lptoken) != address(want)) {
            revert("wrong pid");
        }

        // 1:1 assignments
        tradeFactory = _tradeFactory;
        fxnPid = _fxnPid;
        fxnGauge = _gauge;

        // have our strategy deploy our vault from the booster using the fxnPid
        userVault = IConvexFxn(fxnBooster.createVault(_fxnPid));

        // want = Curve LP
        want.approve(address(userVault), type(uint256).max);

        // set up our baseStrategy vars
        minReportDelay = 3650 days;
        creditThreshold = 50_000e18;

        // set up trade factory
        _setUpTradeFactory();
    }

    /* ========== VIEWS ========== */

    /**
     * @notice Strategy name.
     * @return strategyName Strategy name.
     */
    function name()
        external
        view
        override
        returns (string memory strategyName)
    {
        return
            string(
                abi.encodePacked(
                    "StrategyConvexFxnFactory-",
                    IDetails(address(want)).symbol()
                )
            );
    }

    /**
     * @notice Balance of want staked in Convex f(x).
     * @return balanceStaked Balance of want staked in Convex f(x).
     */
    function stakedBalance() public view returns (uint256 balanceStaked) {
        balanceStaked = IERC20(fxnGauge).balanceOf(address(userVault));
    }

    /**
     * @notice Balance of want sitting in our strategy.
     * @return wantBalance Balance of want sitting in our strategy.
     */
    function balanceOfWant() public view returns (uint256 wantBalance) {
        wantBalance = want.balanceOf(address(this));
    }

    /**
     * @notice Total assets the strategy holds, sum of loose and staked want.
     * @return totalAssets Total assets the strategy holds, sum of loose and staked want.
     */
    function estimatedTotalAssets()
        public
        view
        override
        returns (uint256 totalAssets)
    {
        totalAssets = balanceOfWant() + stakedBalance();
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
        userVault.getReward();

        // serious loss should never happen, but if it does (for instance, if Curve is hacked), lets record it
        uint256 assets = estimatedTotalAssets();
        uint256 debt = vault.strategies(address(this)).totalDebt;

        // if assets are greater than debt, things are working great!
        if (assets >= debt) {
            _profit = assets - debt;
            _debtPayment = _debtOutstanding;

            uint256 toFree = _profit + _debtPayment;

            // freed is math.min(wantBalance, toFree)
            (uint256 freed, ) = liquidatePosition(toFree);

            if (toFree > freed) {
                if (_debtPayment > freed) {
                    _debtPayment = freed;
                    _profit = 0;
                } else {
                    _profit = freed - _debtPayment;
                }
            }
        }
        // if assets are less than debt, we are in trouble. dont worry about withdrawing here, just report losses
        else {
            _loss = debt - assets;
        }
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        // if in emergency exit, we dont want to deploy any more funds
        if (emergencyExit) {
            return;
        }

        // Send all of our Curve pool tokens to be deposited
        uint256 _toInvest = balanceOfWant();

        if (_toInvest > 0) {
            userVault.deposit(_toInvest);
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
                userVault.withdraw(Math.min(_stakedBal, _neededFromStaked));
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
            userVault.withdraw(_stakedBal);
        }
        return balanceOfWant();
    }

    // migrate our want token to a new strategy if needed, claim rewards tokens as well unless its an emergency
    function prepareMigration(address _newStrategy) internal override {
        uint256 _stakedBal = stakedBalance();

        if (_stakedBal > 0) {
            userVault.withdraw(_stakedBal);
        }

        uint256 fxnBal = fxn.balanceOf(address(this));

        if (fxnBal > 0) {
            fxn.safeTransfer(_newStrategy, fxnBal);
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
     * @dev Do this before updating trade factory if we have extra rewards.
     * @param _rewards Rewards tokens to add to our trade factory.
     */
    function updateRewards(
        address[] memory _rewards
    ) external onlyVaultManagers {
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

        // enable if we have anything else
        for (uint256 i; i < rewardsTokens.length; ++i) {
            address _rewardsToken = rewardsTokens[i];
            require(_rewardsToken != address(want), "not rewards");
            IERC20(_rewardsToken).forceApprove(
                _tradeFactory,
                type(uint256).max
            );
            tf.enable(_rewardsToken, _want);
        }

        fxn.approve(_tradeFactory, type(uint256).max);
        tf.enable(address(fxn), _want);
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

        // disable for any other rewards tokens too
        for (uint256 i; i < rewardsTokens.length; ++i) {
            address _rewardsToken = rewardsTokens[i];
            IERC20(_rewardsToken).approve(_tradeFactory, 0);
            if (_disableTf) {
                tf.disable(_rewardsToken, _want);
            }
        }

        fxn.approve(_tradeFactory, 0);
        if (_disableTf) {
            tf.disable(address(fxn), _want);
        }

        tradeFactory = address(0);
    }

    /* ========== KEEP3RS ========== */

    /**
     * @notice
     *  Provide a signal to the keeper that harvest() should be called.
     *
     *  Dont harvest if a strategy is inactive.
     *  If our profit exceeds our upper limit, then harvest no matter what. For our lower profit limit, credit
     *  threshold, max delay, and manual force trigger, only harvest if our gas price is acceptable.
     *
     * @param _callCostinEth The keepers estimated gas cost to call harvest() (in wei).
     * @return True if harvest() should be called, false otherwise.
     */
    function harvestTrigger(
        uint256 _callCostinEth
    ) public view override returns (bool) {
        // Should not trigger if strategy is not active (no assets and no debtRatio). This means we dont need to adjust
        //  keeper job.
        if (!isActive()) {
            return false;
        }

        // check if the base fee gas price is higher than we allow. if it is, block harvests.
        if (!isBaseFeeAcceptable()) {
            return false;
        }

        // trigger if we want to manually harvest, but only if our gas price is acceptable
        if (forceHarvestTriggerOnce) {
            return true;
        }

        StrategyParams memory params = vault.strategies(address(this));
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
