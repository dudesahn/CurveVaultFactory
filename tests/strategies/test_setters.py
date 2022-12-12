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

    # test our setters in baseStrategy and our main strategy
    strategy.setMaxReportDelay(0, {"from": gov})
    strategy.setMaxReportDelay(1e18, {"from": gov})
    strategy.setMetadataURI(0, {"from": gov})
    strategy.setMinReportDelay(100, {"from": gov})
    strategy.setRewards(gov, {"from": strategist})

    # special setter for frax
    if which_strategy == 2:
        strategy.setLockTime(90000 * 7, {"from": gov})

        # whale can't call
        with brownie.reverts():
            strategy.setLockTime(90000, {"from": whale})
        # can't be too short
        with brownie.reverts():
            strategy.setLockTime(100, {"from": gov})
        # or too long
        with brownie.reverts():
            strategy.setLockTime(2**256 - 1, {"from": gov})

        # set our deposit params
        maxToStake = 1000
        minToStake = 100
        strategy.setDepositParams(minToStake, maxToStake, {"from": gov})
        with brownie.reverts():
            strategy.setDepositParams(maxToStake, minToStake, {"from": gov})

    # harvest our credit
    strategy.harvest({"from": gov})
    if which_strategy == 2:
        total_staked = strategy.stakedBalance()
        assert total_staked == maxToStake
        assert strategy.estimatedTotalAssets() > total_staked

        # get the rest of our funds staked
        chain.sleep(1)
        chain.mine(1)
        strategy.setDepositParams(1e21, 1e29, {"from": gov})
        strategy.harvest({"from": gov})
        assert strategy.estimatedTotalAssets() >= amount

    # check that we have claimable rewards, have to call for frax tho
    if which_strategy == 2:
        chain.sleep(86400 * 7)
        chain.mine(1)
        profit = strategy.claimableProfitInUsdc.call()
        assert profit > 0
        print("Claimable Profit:", profit / 1e6)
    elif which_strategy == 0:
        chain.sleep(86400 * 7)
        chain.mine(1)
        profit = strategy.claimableProfitInUsdc()
        assert profit > 0
        print("Claimable Profit:", profit / 1e6)

    if which_strategy == 0:
        strategy.setVoters(gov, gov, {"from": gov})
        strategy.setLocalKeepCrvs(10, 10, {"from": gov})
        strategy.setClaimRewards(True, {"from": gov})

        # test our reverts as well
        with brownie.reverts():
            strategy.setLocalKeepCrvs(1000000, 0, {"from": gov})
        with brownie.reverts():
            strategy.setLocalKeepCrvs(0, 100000000, {"from": gov})
    elif which_strategy == 1:
        strategy.setVoter(gov, {"from": gov})
        strategy.setLocalKeepCrv(10, {"from": gov})

        # test our reverts as well
        with brownie.reverts():
            strategy.setLocalKeepCrv(1000000, {"from": gov})
    else:
        strategy.setVoters(gov, gov, gov, {"from": gov})
        strategy.setLocalKeepCrvs(10, 10, 10, {"from": gov})

        # test our reverts as well
        with brownie.reverts():
            strategy.setLocalKeepCrvs(1000000, 0, 0, {"from": gov})
        with brownie.reverts():
            strategy.setLocalKeepCrvs(0, 100000000, 0, {"from": gov})
        with brownie.reverts():
            strategy.setLocalKeepCrvs(0, 0, 10000000, {"from": gov})

    strategy.setStrategist(strategist, {"from": gov})
    name = strategy.name()
    print("Strategy Name:", name)
