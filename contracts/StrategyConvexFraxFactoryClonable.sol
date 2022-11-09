// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;
pragma experimental ABIEncoderV2;

// These are the core Yearn libraries
import "@openzeppelin/contracts/utils/math/Math.sol";
import "./interfaces/curve.sol";
import "@yearnvaults/contracts/BaseStrategy.sol";

interface ITradeFactory {
    function enable(address, address) external;

    function disable(address, address) external;
}

interface IOracle {
    function getPriceUsdcRecommended(
        address tokenAddress
    ) external view returns (uint256);
}

interface IConvexRewards {
    // strategy's staked balance in the synthetix staking contract
    function balanceOf(address account) external view returns (uint256);

    // read how much claimable CRV a strategy has
    function earned(address account) external view returns (uint256);

    // stake a convex tokenized deposit
    function stake(uint256 _amount) external returns (bool);

    // withdraw to a convex tokenized deposit, probably never need to use this
    function withdraw(uint256 _amount, bool _claim) external returns (bool);

    // withdraw directly to curve LP token, this is what we primarily use
    function withdrawAndUnwrap(
        uint256 _amount,
        bool _claim
    ) external returns (bool);

    // claim rewards, with an option to claim extra rewards or not
    function getReward(
        address _account,
        bool _claimExtras
    ) external returns (bool);

    // check if we have rewards on a pool
    function extraRewardsLength() external view returns (uint256);

    // if we have rewards, see what the address is
    function extraRewards(uint256 _reward) external view returns (address);

    // read our rewards token
    function rewardToken() external view returns (address);

    // check our reward period finish
    function periodFinish() external view returns (uint256);
}

interface IDetails {
    // get details from curve
    function name() external view returns (string memory);

    function symbol() external view returns (string memory);
}

interface IConvexDeposit {
    // deposit into convex, receive a tokenized deposit.  parameter to stake immediately (we always do this).
    function deposit(
        uint256 _pid,
        uint256 _amount,
        bool _stake
    ) external returns (bool);

    // burn a tokenized deposit (Convex deposit tokens) to receive curve lp tokens back
    function withdraw(uint256 _pid, uint256 _amount) external returns (bool);

    function poolLength() external view returns (uint256);

    function crv() external view returns (address);

    // give us info about a pool based on its pid
    function poolInfo(
        uint256
    ) external view returns (address, address, address, address, address, bool);

    // use this to create our personal convex frax vault for this strategy to get convex's FXS boost
    function createVault(uint256 pid) external returns (address);
}

interface IConvexFrax {
    // use this to create our personal convex frax vault for this strategy to get convex's FXS boost
    function createVault(uint256 pid) external returns (address);

    function getReward() external; // claim our rewards from the staking contract via our user vault

    function stakeLockedCurveLp(
        uint256 _liquidity,
        uint256 _secs
    ) external returns (bytes32 kek_id); // stake our frax convex LP as a new kek

    function lockAdditionalCurveLp(bytes32 _kek_id, uint256 _addl_liq) external; // add want to an existing lock/kek

    // returns FXS first, then any other reward token, then CRV and CVX
    function earned()
        external
        view
        returns (
            address[] memory token_addresses,
            uint256[] memory total_earned
        );

    function fxs() external view returns (address);

    function crv() external view returns (address);

    function cvx() external view returns (address);

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

    function withdrawLockedAndUnwrap(bytes32 _kek_id) external;
}

contract StrategyConvexFraxFactoryClonable is BaseStrategy {
    using SafeERC20 for IERC20;
    /* ========== STATE VARIABLES ========== */
    // these should stay the same across different wants.

    uint256 public localKeepCRV;
    uint256 public localKeepCVX;
    uint256 public localKeepFXS;

    address public curveVoter; // Yearn's veCRV voter, we send some extra CRV here
    address public convexVoter; // Yearn's veCVX voter, we send some extra CVX here
    address public fraxVoter; // Yearn's veCVX voter, we send some extra CVX here
    uint256 internal constant FEE_DENOMINATOR = 10000; // this means all of our fee values are in basis points

    IERC20 public crv;
    IERC20 public convexToken;
    IERC20 public fxs;

    string internal stratName; // we use this to be able to adjust our strategy's name

    // convex-specific variables
    uint256 public harvestProfitMin; // minimum size in USDC that we want to harvest
    uint256 public harvestProfitMax; // maximum size in USDC that we want to harvest

    // ySwaps stuff
    address public tradeFactory;
    address[] public rewardsTokens;

    // check for cloning. Will only be true on the original deployed contract and not on the clones
    bool public isOriginal = true;

    // frax-specific stuff
    address public fraxBooster;
    IConvexFrax public userVault; // This is the vault our strategy uses to stake with frax
    IConvexFrax public stakingAddress;

    uint256 public fraxPid; // this is unique to each pool

    //Timestamp of the most recent deposit to track liquid funds
    uint256 public lastDeposit;
    //Most recent amount deposited
    uint256 public lastDepositAmount;
    uint256 public minDeposit;

    //This is the time the tokens are locked for when staked
    //Inititally set to the min time, 24hours, can be updated later if desired
    uint256 public lockTime;
    //A new "kek" is created each time we stake the LP token and a whole kek must be withdrawn during any withdraws
    //This is the max amount of Keks, we will allow the strat to have open at one time to limit withdraw loops
    uint256 public maxKeks = 5;
    //The index of the next kek to be deposited for deposit/withdraw tracking
    uint256 public nextKek;

    /* ========== CONSTRUCTOR ========== */

    constructor(
        address _vault,
        address _tradeFactory,
        uint256 _fraxPid,
        address _stakingAddress,
        uint256 _harvestProfitMin,
        uint256 _harvestProfitMax,
        address _booster
    ) BaseStrategy(_vault) {
        _initializeStrat(
            _fraxPid,
            _stakingAddress,
            _tradeFactory,
            _harvestProfitMin,
            _harvestProfitMax,
            _booster
        );
    }

    /* ========== CLONING ========== */

    event Cloned(address indexed clone);

    // we use this to clone our original strategy to other vaults
    function cloneStrategyConvexFrax(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        uint256 _fraxPid,
        address _stakingAddress,
        address _tradeFactory,
        uint256 _harvestProfitMin,
        uint256 _harvestProfitMax,
        address _booster
    ) external returns (address newStrategy) {
        if (!isOriginal) {
            revert();
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

        StrategyConvexFraxFactoryClonable(newStrategy).initialize(
            _vault,
            _strategist,
            _rewards,
            _keeper,
            _fraxPid,
            _stakingAddress,
            _tradeFactory,
            _harvestProfitMin,
            _harvestProfitMax,
            _booster
        );

        emit Cloned(newStrategy);
    }

    // this will only be called by the clone function above
    function initialize(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        uint256 _fraxPid,
        address _stakingAddress,
        address _tradeFactory,
        uint256 _harvestProfitMin,
        uint256 _harvestProfitMax,
        address _booster
    ) public {
        _initialize(_vault, _strategist, _rewards, _keeper);
        _initializeStrat(
            _fraxPid,
            _stakingAddress,
            _tradeFactory,
            _harvestProfitMin,
            _harvestProfitMax,
            _booster
        );
    }

    // this is called by our original strategy, as well as any clones
    function _initializeStrat(
        uint256 _fraxPid,
        address _stakingAddress,
        address _tradeFactory,
        uint256 _harvestProfitMin,
        uint256 _harvestProfitMax,
        address _booster
    ) internal {
        // make sure that we haven't initialized this before
        if (address(tradeFactory) != address(0)) {
            revert(); // already initialized.
        }

        // have our strategy deploy our vault from the booster using the fraxPid
        userVault = IConvexFrax(IConvexFrax(fraxBooster).createVault(_fraxPid));
        convexToken = IERC20(userVault.cvx());
        crv = IERC20(userVault.crv());
        fxs = IERC20(userVault.fxs());

        // want = Curve LP
        want.approve(address(userVault), type(uint256).max);

        harvestProfitMin = _harvestProfitMin;
        harvestProfitMax = _harvestProfitMax;

        stakingAddress = IConvexFrax(_stakingAddress);

        fraxPid = _fraxPid;

        lockTime = 604800; // default to minimum of 1 week

        //         if (address(lptoken) != address(want)) {
        //             revert();
        //         }

        tradeFactory = _tradeFactory;

        _updateRewards();
        _setUpTradeFactory();

        // set our strategy's name
        stratName = string(
            abi.encodePacked(
                IDetails(address(want)).name(),
                " Auto-Compounding ",
                IDetails(address(convexToken)).symbol(),
                " Strategy"
            )
        );
    }

    function _setUpTradeFactory() internal {
        //approve and set up trade factory
        address _tradeFactory = tradeFactory;
        address _want = address(want);

        ITradeFactory tf = ITradeFactory(_tradeFactory);
        crv.approve(_tradeFactory, type(uint256).max);
        tf.enable(address(crv), _want);

        convexToken.approve(_tradeFactory, type(uint256).max);
        tf.enable(address(convexToken), _want);

        fxs.approve(_tradeFactory, type(uint256).max);
        tf.enable(address(fxs), _want);

        // check if we have anything other than CRV, CVX, and FXS
        (address[] memory tokenAddresses, ) = userVault.earned();
        uint256 rewardsLength = tokenAddresses.length;

        // enable if we have anything else
        if (rewardsLength > 3) {
            for (uint256 i = 1; i < rewardsLength - 2; ++i) {
                address _rewardsToken = tokenAddresses[i];
                IERC20(_rewardsToken).approve(_tradeFactory, type(uint256).max);
                tf.enable(_rewardsToken, _want);
            }
        }
    }

    /* ========== FUNCTIONS ========== */

    function prepareReturn(
        uint256 _debtOutstanding
    )
        internal
        override
        returns (uint256 _profit, uint256 _loss, uint256 _debtPayment)
    {
        // rewards will be converted later with mev protection by yswaps (tradeFactory)
        userVault.getReward();

        uint256 _localKeepCRV = localKeepCRV;
        address _curveVoter = curveVoter;
        if (_localKeepCRV > 0) {
            uint256 crvBalance = crv.balanceOf(address(this));
            uint256 _sendToVoter = (crvBalance * _localKeepCRV) /
                FEE_DENOMINATOR;
            if (_sendToVoter > 0) {
                crv.safeTransfer(_curveVoter, _sendToVoter);
            }
        }

        uint256 _localKeepCVX = localKeepCVX;
        address _convexVoter = convexVoter;
        if (_localKeepCVX > 0 && _convexVoter != address(0)) {
            uint256 cvxBalance = convexToken.balanceOf(address(this));
            uint256 _sendToVoter = (cvxBalance * _localKeepCVX) /
                FEE_DENOMINATOR;
            if (_sendToVoter > 0) {
                convexToken.safeTransfer(_convexVoter, _sendToVoter);
            }
        }

        uint256 _localKeepFXS = localKeepFXS;
        address _fraxVoter = fraxVoter;
        if (_localKeepFXS > 0 && _fraxVoter != address(0)) {
            uint256 fxsBalance = fxs.balanceOf(address(this));
            uint256 _sendToVoter = (fxsBalance * _localKeepFXS) /
                FEE_DENOMINATOR;
            if (_sendToVoter > 0) {
                fxs.safeTransfer(_fraxVoter, _sendToVoter);
            }
        }

        // serious loss should never happen, but if it does (for instance, if Curve is hacked), let's record it accurately
        uint256 assets = estimatedTotalAssets();
        uint256 debt = vault.strategies(address(this)).totalDebt;

        // if assets are greater than debt, things are working great!
        if (assets >= debt) {
            _profit = assets - debt;
            _debtPayment = _debtOutstanding;

            uint256 toFree = _profit + _debtPayment;

            //freed is math.min(wantBalance, toFree)
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
        // if assets are less than debt, we are in trouble. should never happen. dont worry about withdrawing here just report profit
        else {
            _loss = debt - assets;
        }
    }

    //Migration should only be called if all funds are completely liquid
    //In case of problems, emergencyExit can be set to true and then harvest the strategy.
    //Or manually withdraw all liquid keks and wait until the remainder becomes liquid
    //This will allow as much of the liquid position to be withdrawn while allowing future withdraws for still locked tokens
    function prepareMigration(address _newStrategy) internal override {
        require(
            lastDeposit + lockTime < block.timestamp,
            "Latest deposit is not avialable yet for withdraw"
        );
        withdrawSome(type(uint256).max);

        uint256 crvBal = crv.balanceOf(address(this));
        uint256 cvxBal = convexToken.balanceOf(address(this));
        uint256 fxsBal = fxs.balanceOf(address(this));

        if (crvBal > 0) {
            crv.safeTransfer(_newStrategy, crvBal);
        }
        if (cvxBal > 0) {
            convexToken.safeTransfer(_newStrategy, cvxBal);
        }
        if (fxsBal > 0) {
            fxs.safeTransfer(_newStrategy, fxsBal);
        }
    }

    /* ========== KEEP3RS ========== */
    // use this to determine when to harvest automagically
    function harvestTrigger(
        uint256 callCostinEth
    ) public view override returns (bool) {
        // Should not trigger if strategy is not active (no assets and no debtRatio). This means we don't need to adjust keeper job.
        if (!isActive()) {
            return false;
        }

        // harvest if we have a profit to claim at our upper limit without considering gas price
        uint256 claimableProfit = claimableProfitInUsdc();
        if (claimableProfit > harvestProfitMax) {
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

        // harvest if we have a sufficient profit to claim, but only if our gas price is acceptable
        if (claimableProfit > harvestProfitMin) {
            return true;
        }

        StrategyParams memory params = vault.strategies(address(this));
        // harvest regardless of profit once we reach our maxDelay
        if (block.timestamp - params.lastReport > maxReportDelay) {
            return true;
        }

        // harvest our credit if it's above our threshold
        if (vault.creditAvailable() > creditThreshold) {
            return true;
        }

        // otherwise, we don't harvest
        return false;
    }

    /// @notice Calculates the profit if all claimable assets were sold for USDC (6 decimals).
    /// @return Total return in USDC from selling claimable CRV, CVX, and FXS.
    function claimableProfitInUsdc() public view returns (uint256) {
        (, uint256[] memory tokenAmounts) = userVault.earned();
        // get our balances of fxs, crv, cvx. fxs always first, crv + cvx always last two
        uint256 claimableFxs = tokenAmounts[0];
        uint256 rewardLength = tokenAmounts.length;
        uint256 claimableCvx = tokenAmounts[rewardLength - 1];
        uint256 claimableCrv = tokenAmounts[rewardLength - 2];

        IOracle yearnOracle = IOracle(
            0x83d95e0D5f402511dB06817Aff3f9eA88224B030
        ); // yearn lens oracle
        uint256 crvPrice = yearnOracle.getPriceUsdcRecommended(address(crv));
        uint256 cvxPrice = yearnOracle.getPriceUsdcRecommended(
            address(convexToken)
        );
        uint256 fxsPrice = yearnOracle.getPriceUsdcRecommended(address(fxs));

        return
            (crvPrice *
                claimableCrv +
                cvxPrice *
                claimableCvx +
                fxsPrice *
                claimableFxs) / 1e18;
    }

    // convert our keeper's eth cost into want, we don't need this anymore since we don't use baseStrategy harvestTrigger
    function ethToWant(
        uint256 _ethAmount
    ) public view override returns (uint256) {}

    /* ========== SETTERS ========== */

    // These functions are useful for setting parameters of the strategy that may need to be adjusted.

    // Use to add or update rewards
    // Rebuilds tradefactory too
    function updateRewards() external onlyGovernance {
        address tf = tradeFactory;
        _removeTradeFactoryPermissions();
        _updateRewards();

        tradeFactory = tf;
        _setUpTradeFactory();
    }

    function _updateRewards() internal {
        delete rewardsTokens; // empty the rewardsTokens and rebuild

        // check our user vault to see what rewards we have
        (address[] memory tokenAddresses, ) = userVault.earned();
        uint256 rewardsLength = tokenAddresses.length;

        // if we have rewards other than CRV, CVX, and FXS then add them too
        if (rewardsLength > 3) {
            for (uint256 i = 1; i < rewardsLength - 2; ++i) {
                address _rewardsToken = tokenAddresses[i];
                rewardsTokens.push(_rewardsToken);
            }
        }
    }

    function updateLocalKeepCrvs(
        uint256 _keepCrv,
        uint256 _keepCvx,
        uint256 _keepFxs
    ) external onlyGovernance {
        if (_keepCrv > 10_000 || _keepCvx > 10_000 || _keepFxs > 10_000) {
            revert();
        }

        localKeepCRV = _keepCrv;
        localKeepCVX = _keepCvx;
        localKeepFXS = _keepFxs;
    }

    // Use to turn off extra rewards claiming and selling.
    function turnOffRewards() external onlyGovernance {
        delete rewardsTokens;
    }

    /* ========== VIEWS ========== */

    function name() external view override returns (string memory) {
        return stratName;
    }

    function stakedBalance() public view returns (uint256) {
        // how much want we have staked in Convex-Frax
        return stakingAddress.lockedLiquidityOf(address(userVault));
    }

    function balanceOfWant() public view returns (uint256) {
        // balance of want sitting in our strategy
        return want.balanceOf(address(this));
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return balanceOfWant() + stakedBalance();
    }

    /* ========== CONSTANT FUNCTIONS ========== */
    // these should stay the same across different wants.

    function adjustPosition(uint256 _debtOutstanding) internal override {
        if (emergencyExit) {
            return;
        }

        // Send all of our Curve pool tokens to be deposited
        uint256 _toInvest = balanceOfWant();

        // If we have already locked the max amount of keks, we need to withdraw the oldest one
        // and reinvest that alongside the new funds
        if (nextKek >= maxKeks && _toInvest > minDeposit) {
            //Get the oldest kek that could have funds in it
            IConvexFrax.LockedStake memory stake = stakingAddress
                .lockedStakesOf(address(this))[nextKek - maxKeks];
            //Make sure it hasnt already been withdrawn
            if (stake.amount > 0) {
                //Withdraw funds and add them to the amount to deposit
                userVault.withdrawLockedAndUnwrap(stake.kek_id);
                unchecked {
                    _toInvest += stake.amount;
                }
            }
        }

        userVault.stakeLockedCurveLp(_toInvest, lockTime);

        lastDeposit = block.timestamp;
        lastDepositAmount = _toInvest;
        nextKek++;
    }

    function liquidatePosition(
        uint256 _amountNeeded
    ) internal override returns (uint256 _liquidatedAmount, uint256 _loss) {
        uint256 _liquidWant = balanceOfWant();

        if (_liquidWant < _amountNeeded) {
            uint256 needed;
            unchecked {
                needed = _amountNeeded - _liquidWant;
            }

            //Need to check that there is enough liquidity to withdraw so we dont report loss thats not true
            if (lastDeposit + lockTime > block.timestamp) {
                require(
                    stakedBalance() - stillLockedStake() >= needed,
                    "Need to wait till most recent deposit unlocks"
                );
            }

            withdrawSome(needed);

            _liquidWant = balanceOfWant();
        }

        unchecked {
            if (_liquidWant >= _amountNeeded) {
                _liquidatedAmount = _amountNeeded;
            } else {
                _liquidatedAmount = _liquidWant;
                _loss = _amountNeeded - _liquidWant;
            }
        }
    }

    function withdrawSome(uint256 _amount) internal {
        if (_amount == 0) return;

        IConvexFrax.LockedStake[] memory stakes = stakingAddress.lockedStakesOf(
            address(this)
        );

        uint256 i = nextKek > maxKeks ? nextKek - maxKeks : 0;
        uint256 needed = Math.min(_amount, stakedBalance());
        IConvexFrax.LockedStake memory stake;
        uint256 liquidity;
        while (needed > 0 && i < nextKek) {
            stake = stakes[i];
            liquidity = stake.amount;

            if (liquidity > 0 && stake.ending_timestamp <= block.timestamp) {
                userVault.withdrawLockedAndUnwrap(stake.kek_id);

                if (liquidity < needed) {
                    unchecked {
                        needed -= liquidity;
                        i++;
                    }
                } else {
                    break;
                }
            } else {
                unchecked {
                    i++;
                }
            }
        }
    }

    //Will liquidate as much as possible at the time. May not be able to liquidate all if anything has been deposited in the last day
    // Would then have to be called again after locked period has expired
    function liquidateAllPositions() internal override returns (uint256) {
        withdrawSome(type(uint256).max);
        return balanceOfWant();
    }

    // we don't want for these tokens to be swept out. We allow gov to sweep out cvx vault tokens; we would only be holding these if things were really, really rekt.
    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {}

    /* ========== SETTERS ========== */

    // These functions are useful for setting parameters of the strategy that may need to be adjusted.

    //Returns the total amount that cannot yet be withdrawn from the staking contract
    function stillLockedStake() public view returns (uint256 stillLocked) {
        IConvexFrax.LockedStake[] memory stakes = stakingAddress.lockedStakesOf(
            address(this)
        );
        IConvexFrax.LockedStake memory stake;
        uint256 time = block.timestamp;
        uint256 _nextKek = nextKek;
        uint256 _maxKeks = maxKeks;
        uint256 i = _nextKek > _maxKeks ? _nextKek - _maxKeks : 0;
        for (i; i < _nextKek; i++) {
            stake = stakes[i];

            if (stake.ending_timestamp > time) {
                unchecked {
                    stillLocked += stake.amount;
                }
            }
        }
    }

    //Function available to Governance to manually withdraw a specific kek
    //Available if the counter or loops fail
    //Pass the index of the kek to withdraw as the param
    function manualWithdraw(uint256 index) external onlyEmergencyAuthorized {
        userVault.withdrawLockedAndUnwrap(
            stakingAddress.lockedStakesOf(address(this))[index].kek_id
        );
    }

    //Function to change the allowed amount of max keks
    //Will withdraw funds if lowering the max. Should harvest after maxKeks is lowered
    function setMaxKeks(uint256 _maxKeks) external onlyVaultManagers {
        //If we are lowering the max we need to withdraw the diff if we are already over the new max
        if (_maxKeks < maxKeks && nextKek > _maxKeks) {
            uint256 toWithdraw = maxKeks - _maxKeks;
            IConvexFrax.LockedStake[] memory stakes = stakingAddress
                .lockedStakesOf(address(this));
            IConvexFrax.LockedStake memory stake;
            for (uint256 i; i < toWithdraw; i++) {
                stake = stakes[nextKek - maxKeks + i];

                //Need to make sure the kek can be withdrawn and is > 0
                if (stake.amount > 0) {
                    require(
                        stake.ending_timestamp < block.timestamp,
                        "Not liquid"
                    );
                    userVault.withdrawLockedAndUnwrap(stake.kek_id);
                }
            }
        }
        maxKeks = _maxKeks;
    }

    //This can be used to update how long the tokens are locked when staked
    //Care should be taken when increasing the time to only update directly before a harvest
    //Otherwise the timestamp checks when withdrawing could be inaccurate
    function setLockTime(uint256 _lockTime) external onlyVaultManagers {
        require(
            594000 < _lockTime && _lockTime < 31536000,
            "1 week < x < 1 year"
        );
        lockTime = _lockTime;
    }

    function updateTradeFactory(
        address _newTradeFactory
    ) external onlyGovernance {
        if (tradeFactory != address(0)) {
            _removeTradeFactoryPermissions();
        }

        tradeFactory = _newTradeFactory;
        if (_newTradeFactory != address(0)) {
            _setUpTradeFactory();
        }
    }

    function updateVoters(
        address _curveVoter,
        address _convexVoter,
        address _convexFraxVoter
    ) external onlyGovernance {
        curveVoter = _curveVoter;
        convexVoter = _convexVoter;
        fraxVoter = _convexFraxVoter;
    }

    // once this is called setupTradefactory must be called to get things working again
    function removeTradeFactoryPermissions() external onlyEmergencyAuthorized {
        _removeTradeFactoryPermissions();
    }

    function _removeTradeFactoryPermissions() internal {
        address _tradeFactory = tradeFactory;
        if (_tradeFactory == address(0)) {
            return;
        }
        ITradeFactory tf = ITradeFactory(_tradeFactory);

        address _want = address(want);
        crv.approve(_tradeFactory, 0);
        tf.disable(address(crv), _want);

        convexToken.approve(_tradeFactory, 0);
        tf.disable(address(convexToken), _want);

        fxs.approve(_tradeFactory, 0);
        tf.disable(address(fxs), _want);

        (address[] memory tokenAddresses, ) = userVault.earned();
        uint256 rewardsLength = tokenAddresses.length;

        // enable for any other rewards tokens too
        if (rewardsLength > 3) {
            for (uint256 i = 1; i < rewardsLength - 2; ++i) {
                address _rewardsToken = tokenAddresses[i];
                IERC20(_rewardsToken).approve(_tradeFactory, 0);
                tf.disable(_rewardsToken, _want);
            }
        }

        tradeFactory = address(0);
    }

    /**
     * @notice
     * Here we set various parameters to optimize our harvestTrigger.
     * @param _harvestProfitMin The amount of profit (in USDC, 6 decimals)
     * that will trigger a harvest if gas price is acceptable.
     * @param _harvestProfitMax The amount of profit in USDC that
     * will trigger a harvest regardless of gas price.
     */
    function setHarvestTriggerParams(
        uint256 _harvestProfitMin,
        uint256 _harvestProfitMax
    ) external onlyVaultManagers {
        harvestProfitMin = _harvestProfitMin;
        harvestProfitMax = _harvestProfitMax;
    }
}
