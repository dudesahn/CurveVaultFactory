import brownie
from brownie import Contract
from brownie import config
import math

# test the our strategy's ability to deposit, harvest, and withdraw, with different optimal deposit tokens if we have them
def test_frax_operation(
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
    if which_strategy != 2:
        return

    # to 4 keks
    with brownie.reverts():
        strategy.setMaxKeks(4, {"from": gov})
        print("Can't lower if we haven't maxed out yet")

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    chain.sleep(1)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    print("First 5 harvests down")
    print("Max keks:", strategy.maxKeks())
    print("Next kek:", strategy.nextKek())
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # can't harvest again as funds are locked, but only if we have something to harvest in
    with brownie.reverts():
        vault.deposit(amount / 20, {"from": whale})
        strategy.harvest({"from": gov})

    # sleep for 4 more days to fully unlock our first two keks
    chain.sleep(86400)
    with brownie.reverts():
        strategy.setMaxKeks(4, {"from": gov})
        print("Wait for more unlock to lower the number of keks we have")
    chain.sleep(86400 * 3)
    strategy.setMaxKeks(4, {"from": gov})

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.maxKeks())
    print("Next kek:", strategy.nextKek())

    # try to decrease our max keks again
    with brownie.reverts():
        strategy.setMaxKeks(2, {"from": gov})
        print("Wait for unlock to lower the number of keks we have")

    # wait another week so our frax LPs are unlocked
    chain.sleep(86400 * 7)
    chain.mine(1)

    # check how much locked stake we have (should be zero)
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.maxKeks())
    print("Next kek:", strategy.nextKek())

    # lower now
    strategy.setMaxKeks(3, {"from": gov})
    print("Keks successfullly lowered to 3")
