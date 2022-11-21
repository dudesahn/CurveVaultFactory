import brownie
from brownie import Contract
from brownie import config
import math

# lower our number of keks
def test_lower_keks(
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

# lower our number of keks after we get well above our maxKeks
def test_lower_keks_part_two(
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
        
    # lower it immediately
    strategy.setMaxKeks(3, {"from": gov})

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

    # sleep since our 3 keks are full
    chain.sleep(86400 * 7)

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

    # sleep to free them all up
    chain.sleep(86400 * 7)
    
    # lower down to 2, this should hit the other branch in our setMaxKeks
    strategy.setMaxKeks(2, {"from": gov})

# increase our number of keks
def test_increase_keks(
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
    
    # increase our max keks to 7
    strategy.setMaxKeks(7, {"from": gov})
    print("successfully increased our keks")

# withdraw from the only unlocked kek
def test_withdraw_with_some_locked(
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

    # sleep for 3 more days to fully unlock our first kek
    chain.sleep(86400 * 3)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)
    
    # withdraw from our first kek
    vault.withdraw(1e18, {"from": whale})



# test manual withdrawals
def test_manual_withdrawal(
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
    
    # test withdrawing 1 kek manually at a time
    assert strategy.balanceOfWant() == 0
    index_to_withdraw = strategy.nextKek() - 1
    
    # can't withdraw yet, need to wait
    with brownie.reverts():
        strategy.manualWithdraw(index_to_withdraw)
        
    chain.sleep(86400 * 7)
    chain.mine(1)
    strategy.manualWithdraw(index_to_withdraw)
    assert strategy.balanceOfWant() > 0
    
    
    

