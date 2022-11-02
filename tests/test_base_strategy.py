import brownie
from brownie import Contract
from brownie import config
import math


def test_base_strategy(
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
    newWhale = token.balanceOf(whale)

    # test our harvestTrigger for when we have a profit (don't normally need this)
    # our whale donates dust to the vault, what a nice person!
    donation = 1e16
    token.transfer(strategy, donation, {"from": whale})

    # comment this out since we no longer use harvestTrigger from baseStrategy
    # tx = strategy.harvestTrigger(0, {"from": gov})
    # print("\nShould we harvest? Should be true.", tx)
    # assert tx == True

    # test all of our random shit
    strategy.doHealthCheck()
    strategy.healthCheck()
    strategy.apiVersion()
    strategy.name()
    strategy.delegatedAssets()
    strategy.vault()
    strategy.strategist()
    strategy.rewards()
    strategy.keeper()
    strategy.want()
    strategy.minReportDelay()
    strategy.maxReportDelay()
    strategy.profitFactor()
    strategy.debtThreshold()
    strategy.emergencyExit()
