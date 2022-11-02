import brownie
from brownie import Contract
from brownie import config
import math

# test passes as of 21-06-26
def test_change_debt(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # evaluate our current total assets
    old_assets = vault.totalAssets()
    startingStrategy = strategy.estimatedTotalAssets()

    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    currentDebt = 10000
    vault.updateStrategyDebtRatio(strategy, currentDebt / 2, {"from": gov})
    chain.sleep(86400)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    assert strategy.estimatedTotalAssets() <= startingStrategy

    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, currentDebt, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # evaluate our current total assets
    new_assets = vault.totalAssets()

    # confirm we made money, or at least that we have about the same
    assert new_assets >= old_assets or math.isclose(new_assets, old_assets, abs_tol=5)

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    # withdraw and confirm our whale made money
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) >= startingWhale
