import brownie
from brownie import Contract
from brownie import config
import math

# test the our strategy's ability to deposit, harvest, and withdraw, with different optimal deposit tokens if we have them
def test_simple_harvest(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    strategist_ms,
    gauge,
    voter,
    rewardsContract,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    accounts,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    newWhale = token.balanceOf(whale)
    chain.sleep(1)
    chain.mine(1)

    # this is part of our check into the staking contract balance
    if which_strategy == 0:
        stakingBeforeHarvest = rewardsContract.balanceOf(strategy)
    else:
        stakingBeforeHarvest = strategy.stakedBalance()

    # harvest, store asset amount
    tx = strategy.harvest({"from": gov})
    print("Harvest info:", tx.events["Harvested"])
    chain.sleep(1)
    chain.mine(1)
    old_assets = vault.totalAssets()
    assert old_assets > 0
    assert token.balanceOf(strategy) == 0
    assert strategy.estimatedTotalAssets() > 0
    print("Starting Assets: ", old_assets / 1e18)
    
    if which_strategy == 2:
        staking_address = Contract(strategy.stakingAddress())
        liq = staking_address.lockedLiquidityOf(strategy.userVault())
        print("Locked stakes:", liq)
        print("Next kek:", strategy.nextKek())

    # try and include custom logic here to check that funds are in the staking contract (if needed)
    if which_strategy == 0:
        stakingBeforeHarvest < rewardsContract.balanceOf(strategy)
    else:
        stakingBeforeHarvest < strategy.stakedBalance()

    # simulate profits
    chain.sleep(sleep_time)
    chain.mine(1)

    # harvest, store new asset amount
    chain.sleep(1)
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    new_assets = vault.totalAssets()
    # confirm we made money, or at least that we have about the same
    assert new_assets >= old_assets
    print("\nAssets after 1 day: ", new_assets / 1e18)

    if which_strategy == 2:
        staking_address = Contract(strategy.stakingAddress())
        liq = staking_address.lockedLiquidityOf(strategy.userVault())
        print("Locked stakes:", liq)
        print("Next kek:", strategy.nextKek())

    # Display estimated APR
    print(
        "\nEstimated APR: ",
        "{:.2%}".format(
            ((new_assets - old_assets) * (365 * 86400 / sleep_time))
            / (strategy.estimatedTotalAssets())
        ),
    )
    print("Harvest info:", tx.events["Harvested"])
    if not no_profit:
        assert tx.events["Harvested"]["profit"] > 0

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)
    
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same
    tx = vault.withdraw({"from": whale})
    if is_slippery and no_profit:
        assert (
            math.isclose(token.balanceOf(whale), startingWhale, abs_tol=10)
            or token.balanceOf(whale) >= startingWhale
        )
    else:
        assert token.balanceOf(whale) >= startingWhale
