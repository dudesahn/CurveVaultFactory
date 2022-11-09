import brownie
from brownie import Contract
from brownie import config
import math


def test_triggers(
    gov,
    token,
    vault,
    booster,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    gasOracle,
    strategist_ms,
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    newWhale = token.balanceOf(whale)
    starting_assets = vault.totalAssets()
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # simulate 1 days of earnings
    chain.sleep(1 * 86400)
    chain.mine(1)
    booster.earmarkRewards(strategy.pid(), {"from": strategist})

    # harvest should trigger false
    t1 = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be False.", t1)
    assert t1 == False

    # turn on our check for earmark. Shouldn't block anything. Turn off earmark check after.
    strategy.setCheckEarmark(True, {"from": gov})
    t1 = strategy.harvestTrigger(0, {"from": gov})
    if strategy.needsEarmarkReward():
        print("\nShould we harvest? Should be no since we need to earmark.", t1)
        assert t1 == False
    else:
        print("\nShould we harvest? Should be false since it was already false.", t1)
        assert t1 == False
    strategy.setCheckEarmark(False, {"from": gov})
    # simulate 1 days of earnings
    chain.sleep(30 * 86400)
    chain.mine(1)
    # update our minProfit so our harvest triggers true
    print("claimable profit:", strategy.claimableProfitInUsdt() / 1e6)
    strategy.setHarvestProfitNeeded(1e6, 1000000e6, {"from": gov})
    t1 = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", t1)
    assert t1 == True

    # update our maxProfit so harvest triggers true
    strategy.setHarvestProfitNeeded(1000000e6, 1e6, {"from": gov})
    t1 = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", t1)
    assert t1 == True

    # earmark should be false now (it's been too long), turn it off after
    chain.sleep(86400 * 21)
    strategy.setCheckEarmark(True, {"from": gov})
    assert strategy.needsEarmarkReward() == True
    t1 = strategy.harvestTrigger(0, {"from": gov})
    print(
        "\nShould we harvest? Should be false, even though it was true before because of earmark.",
        t1,
    )
    assert t1 == False
    strategy.setCheckEarmark(False, {"from": gov})

    # harvest, wait
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(86400)
    chain.mine(1)

    # withdraw and confirm we made money
    vault.withdraw({"from": whale, "gas": 10_000_000})
    assert token.balanceOf(whale) >= startingWhale

    # harvest should trigger false due to high gas price
    gasOracle.setMaxAcceptableBaseFee(1 * 1e9, {"from": strategist_ms})
    t1 = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be false.", t1)
    assert t1 == False


def test_less_useful_triggers(
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
    starting_assets = vault.totalAssets()
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    strategy.setMinReportDelay(100, {"from": gov})
    t1 = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be False.", t1)
    assert t1 == False

    chain.sleep(200)
