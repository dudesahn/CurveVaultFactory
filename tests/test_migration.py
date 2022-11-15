import brownie
from brownie import Contract
from brownie import config
import math

# test migrating a strategy
def test_migration(
    StrategyConvexFactoryClonable,
    StrategyCurveBoostedFactoryClonable,
    StrategyConvexFraxFactoryClonable,
    gov,
    token,
    vault,
    guardian,
    strategist,
    sleep_time,
    whale,
    strategy,
    chain,
    new_proxy,
    strategist_ms,
    new_trade_factory,
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
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    if which_strategy == 0:  # convex
        new_strategy = strategist.deploy(
            StrategyConvexFactoryClonable,
            vault,
            new_trade_factory,
            pid,
            10_000 * 1e6,
            25_000 * 1e6,
            booster,
            convexToken,
        )

        # can we harvest an unactivated strategy? should be no
        tx = new_strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be False.", tx)
        assert tx == False
    elif which_strategy == 1:  # curve
        new_strategy = strategist.deploy(
            StrategyCurveBoostedFactoryClonable,
            vault,
            new_trade_factory,
            new_proxy,
            gauge,
        )
    else:  # frax
        new_strategy = strategist.deploy(
            StrategyConvexFraxFactoryClonable,
            vault,
            new_trade_factory,
            frax_pid,
            staking_address,
            10_000 * 1e6,
            25_000 * 1e6,
            frax_booster,
        )

        # can we harvest an unactivated strategy? should be no
        tx = new_strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be False.", tx)
        assert tx == False

    total_old = strategy.estimatedTotalAssets()

    # sleep to collect earnings
    chain.sleep(sleep_time)

    if which_strategy == 2:
        with brownie.reverts():
            vault.migrateStrategy(strategy, new_strategy, {"from": gov})
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

    # migrate our old strategy
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    new_strategy.setHealthCheck(healthCheck, {"from": gov})
    new_strategy.setDoHealthCheck(True, {"from": gov})

    # if a curve strat, whitelist on our strategy proxy
    if which_strategy == 1:
        new_proxy.approveStrategy(strategy.gauge(), new_strategy, {"from": gov})

    # assert that our old strategy is empty
    updated_total_old = strategy.estimatedTotalAssets()
    assert updated_total_old == 0

    # harvest to get funds back in strategy
    chain.sleep(1)
    new_strategy.harvest({"from": gov})
    new_strat_balance = new_strategy.estimatedTotalAssets()

    # confirm we made money, or at least that we have about the same
    assert new_strat_balance >= total_old or math.isclose(
        new_strat_balance, total_old, abs_tol=5
    )

    startingVault = vault.totalAssets()
    print("\nVault starting assets with new strategy: ", startingVault)

    # simulate earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # Test out our migrated strategy, confirm we're making a profit
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    new_strategy.harvest({"from": gov})
    vaultAssets_2 = vault.totalAssets()
    # confirm we made money, or at least that we have about the same
    assert vaultAssets_2 >= startingVault or math.isclose(
        vaultAssets_2, startingVault, abs_tol=5
    )
    print("\nAssets after 1 day harvest: ", vaultAssets_2)
