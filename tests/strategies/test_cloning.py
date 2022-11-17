import brownie
from brownie import Wei, accounts, Contract, config, ZERO_ADDRESS
import math

# test cloning our strategy, make sure the cloned strategy still works just fine by sending funds to it
def test_cloning(
    StrategyConvexFactoryClonable,
    StrategyCurveBoostedFactoryClonable,
    StrategyConvexFraxFactoryClonable,
    gov,
    token,
    vault,
    guardian,
    rewards,
    keeper,
    strategist,
    sleep_time,
    whale,
    strategy,
    chain,
    new_proxy,
    strategist_ms,
    new_trade_factory,
    rewardsContract,
    booster,
    convexToken,
    healthCheck,
    pid,
    gauge,
    amount,
    pool,
    strategy_name,
    profit_amount,
    profit_whale,
    which_strategy,
    staking_address,
    frax_pid,
    frax_booster,
    tests_using_tenderly,
    is_slippery,
    no_profit,
    rewards_token,
    is_clonable,
    has_rewards,
):

    # skip this test if we don't clone
    if not is_clonable:
        return

    # tenderly doesn't work for "with brownie.reverts"
    if tests_using_tenderly:
        if which_strategy == 0:  # convex
            tx = strategy.cloneStrategyConvex(
                vault,
                strategist,
                rewards,
                keeper,
                new_trade_factory,
                pid,
                10_000 * 1e6,
                25_000 * 1e6,
                booster,
                convexToken,
            )
            newStrategy = StrategyConvexFactoryClonable.at(tx.return_value)
        elif which_strategy == 1:  # curve
            tx = strategy.cloneStrategyCurveBoosted(
                vault,
                strategist,
                rewards,
                keeper,
                new_trade_factory,
                new_proxy,
                gauge,
                10_000 * 1e6,
                25_000 * 1e6,
            )
            newStrategy = StrategyCurveBoostedFactoryClonable.at(tx.return_value)
        else:  # frax
            tx = strategy.cloneStrategyConvexFrax(
                vault,
                strategist,
                rewards,
                keeper,
                new_trade_factory,
                frax_pid,
                staking_address,
                10_000 * 1e6,
                25_000 * 1e6,
                frax_booster,
            )
            newStrategy = StrategyConvexFraxFactoryClonable.at(tx.return_value)
    else:
        if which_strategy == 0:  # convex
            # Shouldn't be able to call initialize again
            with brownie.reverts():
                strategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    pid,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    booster,
                    convexToken,
                    {"from": gov},
                )

            tx = strategy.cloneStrategyConvex(
                vault,
                strategist,
                rewards,
                keeper,
                new_trade_factory,
                pid,
                10_000 * 1e6,
                25_000 * 1e6,
                booster,
                convexToken,
                {"from": gov},
            )

            newStrategy = StrategyConvexFactoryClonable.at(tx.return_value)

            # Shouldn't be able to call initialize again
            with brownie.reverts():
                newStrategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    pid,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    booster,
                    convexToken,
                    {"from": gov},
                )

            ## shouldn't be able to clone a clone
            with brownie.reverts():
                newStrategy.cloneStrategyConvex(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    pid,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    booster,
                    convexToken,
                    {"from": gov},
                )

        elif which_strategy == 1:  # curve
            # Shouldn't be able to call initialize again
            with brownie.reverts():
                strategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    new_proxy,
                    gauge,
                    {"from": gov},
                )
            tx = strategy.cloneStrategyCurveBoosted(
                vault,
                strategist,
                rewards,
                keeper,
                new_trade_factory,
                new_proxy,
                gauge,
                {"from": gov},
            )

            newStrategy = StrategyCurveBoostedFactoryClonable.at(tx.return_value)

            # Shouldn't be able to call initialize again
            with brownie.reverts():
                newStrategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    new_proxy,
                    gauge,
                    {"from": gov},
                )

            ## shouldn't be able to clone a clone
            with brownie.reverts():
                newStrategy.cloneStrategyCurveBoosted(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    new_proxy,
                    gauge,
                    {"from": gov},
                )

        else:  # frax
            # Shouldn't be able to call initialize again
            with brownie.reverts():
                strategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    frax_pid,
                    staking_address,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    frax_booster,
                    {"from": gov},
                )

            tx = strategy.cloneStrategyConvexFrax(
                vault,
                strategist,
                rewards,
                keeper,
                new_trade_factory,
                frax_pid,
                staking_address,
                10_000 * 1e6,
                25_000 * 1e6,
                frax_booster,
                {"from": gov},
            )

            newStrategy = StrategyConvexFraxFactoryClonable.at(tx.return_value)

            # Shouldn't be able to call initialize again
            with brownie.reverts():
                newStrategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    frax_pid,
                    staking_address,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    frax_booster,
                    {"from": gov},
                )

            ## shouldn't be able to clone a clone
            with brownie.reverts():
                newStrategy.cloneStrategyConvexFrax(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    new_trade_factory,
                    frax_pid,
                    staking_address,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    frax_booster,
                    {"from": gov},
                )

    # revoke and get funds back into vault
    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.revokeStrategy(strategy, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # attach our new strategy
    vault.addStrategy(newStrategy, currentDebt, 0, 2**256 - 1, 1_000, {"from": gov})

    assert vault.withdrawalQueue(1) == newStrategy
    assert vault.strategies(newStrategy)["debtRatio"] == currentDebt
    assert vault.strategies(strategy)["debtRatio"] == 0

    # add rewards token if needed
    if has_rewards:
        if which_strategy == 1:
            newStrategy.updateRewards([rewards_token], {"from": gov})
        else:
            newStrategy.updateRewards({"from": gov})

    ## deposit to the vault after approving; this is basically just our simple_harvest test
    before_pps = vault.pricePerShare()
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})

    # harvest, store asset amount
    if which_strategy == 1:  # make sure to update our proxy if a curve strategy
        new_proxy.approveStrategy(strategy.gauge(), newStrategy, {"from": gov})
    newStrategy.harvest({"from": gov})
    chain.sleep(1)
    old_assets = vault.totalAssets()
    assert old_assets > 0
    assert token.balanceOf(newStrategy) == 0
    assert newStrategy.estimatedTotalAssets() > 0
    print("\nStarting Assets: ", old_assets / 1e18)

    # try and include custom logic here to check that funds are in the staking contract (if needed)
    if which_strategy == 0:
        assert rewardsContract.balanceOf(newStrategy) > 0
        print("\nAssets Staked: ", rewardsContract.balanceOf(newStrategy) / 1e18)
    else:
        assert newStrategy.stakedBalance() > 0
        print("\nAssets Staked: ", newStrategy.stakedBalance() / 1e18)

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # harvest after a day, store new asset amount
    token.transfer(newStrategy, profit_amount, {"from": profit_whale})
    newStrategy.harvest({"from": gov})
    new_assets = vault.totalAssets()

    # we can't use strategyEstimated Assets because the profits are sent to the vault
    assert new_assets >= old_assets
    print("\nAssets after 2 days: ", new_assets / 1e18)

    # Display estimated APR based on the two days before the pay out
    print(
        "\nEstimated APR: ",
        "{:.2%}".format(
            ((new_assets - old_assets) * (365 * (86400 / sleep_time)))
            / (newStrategy.estimatedTotalAssets())
        ),
    )

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same
    vault.withdraw({"from": whale})
    if is_slippery and no_profit:
        assert (
            math.isclose(token.balanceOf(whale), startingWhale, abs_tol=10)
            or token.balanceOf(whale) >= startingWhale
        )
    else:
        assert token.balanceOf(whale) >= startingWhale
    assert vault.pricePerShare() >= before_pps
