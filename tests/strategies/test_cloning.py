import brownie
from brownie import chain
import pytest
from utils import harvest_strategy

# make sure cloned strategy works just like normal
def test_cloning(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    rewards,
    keeper,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    contract_name,
    is_clonable,
    tests_using_tenderly,
    strategy_name,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    which_strategy,
    trade_factory,
    pid,
    new_proxy,
    booster,
    convex_token,
    gauge,
    frax_pid,
    staking_address,
    frax_booster,
    has_rewards,
    rewards_token,
):

    # skip this test if we don't clone
    if not is_clonable:
        return

    ## deposit to the vault after approving like normal
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    before_pps = vault.pricePerShare()

    # tenderly doesn't work for "with brownie.reverts"
    if tests_using_tenderly:
        if which_strategy == 0:  # convex
            tx = strategy.cloneStrategyConvex(
                vault,
                strategist,
                rewards,
                keeper,
                trade_factory,
                pid,
                10_000 * 1e6,
                25_000 * 1e6,
                booster,
                convex_token,
            )
            new_strategy = contract_name.at(tx.return_value)
        elif which_strategy == 1:  # curve
            tx = strategy.cloneStrategyCurveBoosted(
                vault,
                strategist,
                rewards,
                keeper,
                trade_factory,
                new_proxy,
                gauge,
                10_000 * 1e6,
                25_000 * 1e6,
            )
            new_strategy = contract_name.at(tx.return_value)
        else:  # frax
            tx = strategy.cloneStrategyConvexFrax(
                vault,
                strategist,
                rewards,
                keeper,
                trade_factory,
                frax_pid,
                staking_address,
                10_000 * 1e6,
                25_000 * 1e6,
                frax_booster,
            )
            new_strategy = contract_name.at(tx.return_value)
    else:
        if which_strategy == 0:  # convex
            # Shouldn't be able to call initialize again
            with brownie.reverts():
                strategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    trade_factory,
                    pid,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    booster,
                    convex_token,
                    {"from": gov},
                )

            tx = strategy.cloneStrategyConvex(
                vault,
                strategist,
                rewards,
                keeper,
                trade_factory,
                pid,
                10_000 * 1e6,
                25_000 * 1e6,
                booster,
                convex_token,
                {"from": gov},
            )

            new_strategy = contract_name.at(tx.return_value)

            # Shouldn't be able to call initialize again
            with brownie.reverts():
                new_strategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    trade_factory,
                    pid,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    booster,
                    convex_token,
                    {"from": gov},
                )

            ## shouldn't be able to clone a clone
            with brownie.reverts():
                new_strategy.cloneStrategyConvex(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    trade_factory,
                    pid,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    booster,
                    convex_token,
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
                    trade_factory,
                    new_proxy,
                    gauge,
                    {"from": gov},
                )
            tx = strategy.cloneStrategyCurveBoosted(
                vault,
                strategist,
                rewards,
                keeper,
                trade_factory,
                new_proxy,
                gauge,
                {"from": gov},
            )

            new_strategy = contract_name.at(tx.return_value)

            # Shouldn't be able to call initialize again
            with brownie.reverts():
                new_strategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    trade_factory,
                    new_proxy,
                    gauge,
                    {"from": gov},
                )

            ## shouldn't be able to clone a clone
            with brownie.reverts():
                new_strategy.cloneStrategyCurveBoosted(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    trade_factory,
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
                    trade_factory,
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
                trade_factory,
                frax_pid,
                staking_address,
                10_000 * 1e6,
                25_000 * 1e6,
                frax_booster,
                {"from": gov},
            )

            new_strategy = contract_name.at(tx.return_value)

            # Shouldn't be able to call initialize again
            with brownie.reverts():
                new_strategy.initialize(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    trade_factory,
                    frax_pid,
                    staking_address,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    frax_booster,
                    {"from": gov},
                )

            ## shouldn't be able to clone a clone
            with brownie.reverts():
                new_strategy.cloneStrategyConvexFrax(
                    vault,
                    strategist,
                    rewards,
                    keeper,
                    trade_factory,
                    frax_pid,
                    staking_address,
                    10_000 * 1e6,
                    25_000 * 1e6,
                    frax_booster,
                    {"from": gov},
                )

    # revoke, get funds back into vault, remove old strat from queue
    vault.revokeStrategy(strategy, {"from": gov})

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    vault.removeStrategyFromQueue(strategy.address, {"from": gov})

    # attach our new strategy, ensure it's the only one
    vault.addStrategy(new_strategy.address, 10_000, 0, 2**256 - 1, 0, {"from": gov})
    assert vault.withdrawalQueue(0) == new_strategy.address
    assert vault.strategies(new_strategy)["debtRatio"] == 10_000
    assert vault.strategies(strategy)["debtRatio"] == 0

    # add rewards token if needed
    if has_rewards:
        if which_strategy == 1:
            newStrategy.updateRewards([rewards_token], {"from": gov})
        else:
            newStrategy.updateRewards({"from": gov})

    # make sure to update our proxy if a curve strategy
    if which_strategy == 1:
        new_proxy.approveStrategy(strategy.gauge(), new_strategy, {"from": gov})

    # harvest, store asset amount
    (profit, loss) = harvest_strategy(
        use_yswaps,
        new_strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    old_assets = vault.totalAssets()
    assert old_assets > 0
    assert token.balanceOf(new_strategy) == 0
    assert new_strategy.estimatedTotalAssets() > 0

    # simulate some earnings
    chain.sleep(sleep_time)

    # harvest after a day, store new asset amount
    (profit, loss) = harvest_strategy(
        use_yswaps,
        new_strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # can't harvest our old strategy anymore since the proxy only takes 1 strategy
    if which_strategy == 1:
        if not tests_using_tenderly:
            with brownie.reverts("!strategy"):
                (profit, loss) = harvest_strategy(
                    use_yswaps,
                    strategy,
                    token,
                    gov,
                    profit_whale,
                    profit_amount,
                    target,
                )

    # harvest again so the strategy reports the profit
    if use_yswaps:
        print("Using ySwaps for harvests")
        (profit, loss) = harvest_strategy(
            use_yswaps,
            new_strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )
    new_assets = vault.totalAssets()

    # we can't use strategyEstimated Assets because the profits are sent to the vault
    assert new_assets >= old_assets

    # Display estimated APR based on the two days before the pay out
    print(
        "\nEstimated APR: ",
        "{:.2%}".format(
            ((new_assets - old_assets) * (365 * (86400 / sleep_time)))
            / (new_strategy.estimatedTotalAssets())
        ),
    )

    # simulate five days of waiting for share price to bump back up
    chain.sleep(86400 * 5)
    chain.mine(1)

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same (profit whale has to be different from normal whale)
    vault.withdraw({"from": whale})
    if no_profit:
        assert (
            pytest.approx(token.balanceOf(whale), rel=RELATIVE_APPROX) == starting_whale
        )
    else:
        assert token.balanceOf(whale) > starting_whale

    # make sure our PPS went us as well
    assert vault.pricePerShare() >= before_pps
