import brownie
from brownie import Contract, ZERO_ADDRESS

# test the setters on our strategy
def test_setters(
    gov,
    strategy,
    strategist,
    chain,
    whale,
    token,
    vault,
    amount,
    gasOracle,
    strategist_ms,
    profit_amount,
    profit_whale,
    which_strategy,
):
    # frax strategy gets stuck on these views, so we call them instead
    if which_strategy == 2:
        # test our manual harvest trigger
        strategy.setForceHarvestTriggerOnce(True, {"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True

        # shouldn't manually harvest when gas is high
        gasOracle.setManualBaseFeeBool(False, {"from": strategist_ms})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        gasOracle.setManualBaseFeeBool(True, {"from": strategist_ms})

        strategy.setForceHarvestTriggerOnce(False, {"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False

        # test our manual harvest trigger, and that a harvest turns it off
        strategy.setForceHarvestTriggerOnce(True, {"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True
        strategy.harvest({"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
    else:
        # test our manual harvest trigger
        strategy.setForceHarvestTriggerOnce(True, {"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True

        # shouldn't manually harvest when gas is high
        gasOracle.setManualBaseFeeBool(False, {"from": strategist_ms})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        gasOracle.setManualBaseFeeBool(True, {"from": strategist_ms})

        strategy.setForceHarvestTriggerOnce(False, {"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False

        # test our manual harvest trigger, and that a harvest turns it off
        strategy.setForceHarvestTriggerOnce(True, {"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True
        strategy.harvest({"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False

    # deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # test our setters in baseStrategy and our main strategy
    strategy.setMaxReportDelay(0, {"from": gov})
    strategy.setMaxReportDelay(1e18, {"from": gov})
    strategy.setMetadataURI(0, {"from": gov})
    strategy.setMinReportDelay(100, {"from": gov})
    strategy.setRewards(gov, {"from": strategist})
    strategy.turnOffRewards({"from": gov})

    if which_strategy == 0:
        strategy.setCheckEarmark(False, {"from": gov})
        strategy.updateVoters(ZERO_ADDRESS, ZERO_ADDRESS, {"from": gov})
        strategy.updateLocalKeepCrvs(10, 10, {"from": gov})
        strategy.setClaimRewards(True, {"from": gov})

        # test our reverts as well
        with brownie.reverts():
            strategy.updateLocalKeepCrvs(1000000, 0, {"from": gov})
        with brownie.reverts():
            strategy.updateLocalKeepCrvs(0, 100000000, {"from": gov})
    elif which_strategy == 1:
        strategy.updateLocalKeepCrv(10, {"from": gov})

        # test our reverts as well
        with brownie.reverts():
            strategy.updateLocalKeepCrv(1000000, {"from": gov})
    else:
        strategy.updateVoters(ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, {"from": gov})
        strategy.updateLocalKeepCrvs(10, 10, 10, {"from": gov})

        # test our reverts as well
        with brownie.reverts():
            strategy.updateLocalKeepCrvs(1000000, 0, 0, {"from": gov})
        with brownie.reverts():
            strategy.updateLocalKeepCrvs(0, 100000000, 0, {"from": gov})
        with brownie.reverts():
            strategy.updateLocalKeepCrvs(0, 0, 10000000, {"from": gov})

    strategy.setStrategist(strategist, {"from": gov})
    name = strategy.name()
    print("Strategy Name:", name)
