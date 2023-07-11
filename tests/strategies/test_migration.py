import pytest
from utils import harvest_strategy
from brownie import accounts, interface, chain
import brownie

# test migrating a strategy
def test_migration(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    sleep_time,
    contract_name,
    profit_whale,
    profit_amount,
    target,
    trade_factory,
    use_yswaps,
    is_slippery,
    no_profit,
    which_strategy,
    pid,
    new_proxy,
    booster,
    convex_token,
    gauge,
    crv,
    frax_booster,
    frax_pid,
    staking_address,
    fxs,
):

    ## deposit to the vault after approving
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

    # record our current strategy's assets
    total_old = strategy.estimatedTotalAssets()

    # sleep to collect earnings
    chain.sleep(sleep_time)

    ######### THIS WILL NEED TO BE UPDATED BASED ON STRATEGY CONSTRUCTOR #########
    if which_strategy == 0:  # convex
        new_strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            pid,
            10_000 * 1e6,
            25_000 * 1e6,
            booster,
            convex_token,
        )
    elif which_strategy == 1:  # curve
        new_strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            new_proxy,
            gauge,
        )
    else:  # frax
        new_strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            frax_pid,
            staking_address,
            10_000 * 1e6,
            25_000 * 1e6,
            frax_booster,
        )

    # since curve strats auto-detect gauge tokens in voter, all strategies will show the same TVL
    # this is why we can never have 2 curve strategies for the same gauge, even on different vaults, at the same time
    if which_strategy != 1:
        # can we harvest an unactivated strategy? should be no
        tx = new_strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be False.", tx)
        assert tx == False

    ######### ADD LOGIC TO TEST CLAIMING OF ASSETS FOR TRANSFER TO NEW STRATEGY AS NEEDED #########
    # for some reason withdrawing via our user vault doesn't include the same getReward() call that the staking pool does natively
    # since emergencyExit doesn't enter prepareReturn, we have to manually claim these rewards
    # also, FXS profit accrues every block, so we will still get some dust rewards after we exit as well if we were to call getReward() again
    if which_strategy == 2:
        with brownie.reverts():
            vault.migrateStrategy(strategy, new_strategy, {"from": gov})
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

        user_vault = interface.IFraxVault(strategy.userVault())
        user_vault.getReward({"from": gov})

    # we don't need to do this, but good to do so for checking on our CRV
    if which_strategy == 1:
        new_proxy.harvest(gauge, {"from": strategy})

    # migrate our old strategy, need to claim rewards for convex when withdrawing for convex
    if which_strategy == 0:
        strategy.setClaimRewards(True, {"from": gov})
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})

    # if a curve strat, whitelist on our strategy proxy
    if which_strategy == 1:
        new_proxy.approveStrategy(strategy.gauge(), new_strategy, {"from": gov})

    ####### ADD LOGIC TO MAKE SURE ASSET TRANSFER WENT AS EXPECTED #######
    assert crv.balanceOf(strategy) == 0
    assert crv.balanceOf(new_strategy) > 0

    if which_strategy != 1:
        assert convex_token.balanceOf(strategy) == 0
        assert convex_token.balanceOf(new_strategy) > 0

    if which_strategy == 2:
        assert fxs.balanceOf(strategy) == 0
        assert fxs.balanceOf(new_strategy) > 0

    # assert that our old strategy is empty
    updated_total_old = strategy.estimatedTotalAssets()
    assert updated_total_old == 0

    # harvest to get funds back in new strategy
    (profit, loss) = harvest_strategy(
        use_yswaps,
        new_strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    new_strat_balance = new_strategy.estimatedTotalAssets()

    # confirm that we have the same amount of assets in our new strategy as old
    if no_profit:
        assert pytest.approx(new_strat_balance, rel=RELATIVE_APPROX) == total_old
    else:
        assert new_strat_balance > total_old

    # record our new assets
    vault_new_assets = vault.totalAssets()

    # simulate earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # Test out our migrated strategy, confirm we're making a profit
    (profit, loss) = harvest_strategy(
        use_yswaps,
        new_strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    vault_newer_assets = vault.totalAssets()
    # confirm we made money, or at least that we have about the same
    if no_profit:
        assert (
            pytest.approx(vault_newer_assets, rel=RELATIVE_APPROX) == vault_new_assets
        )
    else:
        assert vault_newer_assets > vault_new_assets


# make sure we can still migrate when we don't have funds
def test_empty_migration(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    sleep_time,
    contract_name,
    profit_whale,
    profit_amount,
    target,
    trade_factory,
    use_yswaps,
    is_slippery,
    RELATIVE_APPROX,
    which_strategy,
    pid,
    new_proxy,
    booster,
    convex_token,
    gauge,
    crv,
    frax_booster,
    frax_pid,
    staking_address,
):

    ## deposit to the vault after approving
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

    # record our current strategy's assets
    total_old = strategy.estimatedTotalAssets()

    # sleep to collect earnings
    chain.sleep(sleep_time)

    ######### THIS WILL NEED TO BE UPDATED BASED ON STRATEGY CONSTRUCTOR #########
    if which_strategy == 0:  # convex
        new_strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            pid,
            10_000 * 1e6,
            25_000 * 1e6,
            booster,
            convex_token,
        )
    elif which_strategy == 1:  # curve
        new_strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            new_proxy,
            gauge,
        )
    else:  # frax
        new_strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            frax_pid,
            staking_address,
            10_000 * 1e6,
            25_000 * 1e6,
            frax_booster,
        )

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

    # set our debtRatio to zero so our harvest sends all funds back to vault
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # yswaps needs another harvest to get the final bit of profit to the vault
    if use_yswaps:
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    # shouldn't have any assets, unless we have slippage, then this might leave dust
    # for complete emptying in this situtation, use emergencyExit
    if is_slippery:
        assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == 0
        strategy.setEmergencyExit({"from": gov})

        # turn off health check since taking profit on no debt
        strategy.setDoHealthCheck(False, {"from": gov})
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    assert strategy.estimatedTotalAssets() == 0

    # make sure we transferred strat params over
    total_debt = vault.strategies(strategy)["totalDebt"]
    debt_ratio = vault.strategies(strategy)["debtRatio"]

    # migrate our old strategy
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})

    # new strategy should also be empty
    assert new_strategy.estimatedTotalAssets() == 0

    # make sure we took our gains and losses with us
    assert total_debt == vault.strategies(new_strategy)["totalDebt"]
    assert debt_ratio == vault.strategies(new_strategy)["debtRatio"] == 0
