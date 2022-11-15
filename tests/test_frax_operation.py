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
    if which_strategy != 2:
        return

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
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)
    
    print("First 3 harvests down")

    # check how much locked stake we have
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)
    
    print("Four more harvests down")

    # check how much locked stake we have
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # try to decrease our keks with locked funds, won't work
    with brownie.reverts():
        strategy.setMaxKeks(2, {"from": gov})

    # wait another week so our frax LPs are unlocked
    chain.sleep(86400 * 7)
    chain.mine(1)

    # check how much locked stake we have
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    # seems to be getting stuck somewhere after here

    # decrease our max keks
    strategy.setMaxKeks(2, {"from": gov})
    print("Lowered our keks to 2")

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # increase it again, deposit more to fill our keks back up
    strategy.setMaxKeks(5, {"from": gov})

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400 * 2)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
