import pytest
from utils import harvest_strategy, check_status
import brownie
from brownie import ZERO_ADDRESS, chain, interface, Contract
from utils import harvest_strategy


def test_yprisma_claim(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    sleep_time,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    yprisma,
):
    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})

    # set this to false so we allow yPRISMA to accumulate in the strategy
    use_yswaps = False

    receiver = Contract(strategy.prismaReceiver())
    eid = receiver.emissionId()
    prisma_vault = Contract(strategy.prismaVault(), owner=receiver)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    claimable = receiver.claimableReward(strategy).dict()
    # Check if any non-zero values (shouldn't have any, should have small amounts for all assets)
    assert any(x for x in (claimable if isinstance(claimable, tuple) else (claimable,)))

    chain.sleep(sleep_time)

    # check that we have claimable profit, need this for min and max profit checks below
    claimable_profit = strategy.claimableProfitInUsdc()
    assert claimable_profit > 0
    print("🤑 Claimable profit >0:", claimable_profit / 1e6)

    # set our max delay to 1 day so we trigger true, then set it back to 21 days
    # but will be false because no max boost (I originally wrote this late in a week, will just be equal to if max boosted or not)
    strategy.setMaxReportDelay(sleep_time - 1)
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be False.", tx)
    assert tx == strategy.claimsAreMaxBoosted()
    strategy.setMaxReportDelay(86400 * 21)

    # we have tiny profit but that's okay; our triggers should be false because we don't have max boost
    # update our minProfit so our harvest should trigger true
    # will be true/false same as above based on max boost
    strategy.setHarvestTriggerParams(1, 1000000e6, {"from": gov})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be false.", tx)
    assert tx == strategy.claimsAreMaxBoosted()

    # update our maxProfit so harvest should trigger true (max profit ignores whether we have full boost or not)
    strategy.setHarvestTriggerParams(1000000e6, 1, {"from": gov})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    # turn off claiming entirely
    strategy.setClaimParams(False, False, {"from": vault.governance()})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be false.", tx)
    assert tx == False
    strategy.setClaimParams(False, True, {"from": vault.governance()})

    strategy.setHarvestTriggerParams(2000e6, 25000e6, {"from": gov})

    # turn on the force claim
    strategy.setClaimParams(True, True, {"from": vault.governance()})

    # update our minProfit so our harvest triggers true
    strategy.setHarvestTriggerParams(1, 1000000e6, {"from": gov})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    # turn off claiming entirely
    strategy.setClaimParams(True, False, {"from": vault.governance()})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be false.", tx)
    assert tx == False
    strategy.setClaimParams(True, True, {"from": vault.governance()})

    # update our maxProfit so harvest triggers true
    strategy.setHarvestTriggerParams(1000000e6, 1, {"from": gov})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    strategy.setHarvestTriggerParams(2000e6, 25000e6, {"from": gov})

    # set our max delay to 1 day so we trigger true, then set it back to 21 days
    strategy.setMaxReportDelay(sleep_time - 1)
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be True.", tx)
    assert tx == True
    strategy.setMaxReportDelay(86400 * 21)

    strategy.setClaimParams(False, True, {"from": vault.governance()})

    # Now harvest again
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    # This only works if we have exhausted our boost for current week (we won't have claimed any yPRISMA)
    if not strategy.claimsAreMaxBoosted():
        assert yprisma.balanceOf(strategy) == 0

    # sleep to get to the new epoch
    chain.sleep(60 * 60 * 24 * 7)
    chain.mine()

    claimable_profit = strategy.claimableProfitInUsdc()
    assert claimable_profit > 0
    print("🤑 Claimable profit next epoch:", claimable_profit / 1e6)

    prisma_vault.allocateNewEmissions(eid)
    receiver.claimableReward(strategy)
    y = "0x90be6DFEa8C80c184C442a36e17cB2439AAE25a7"
    boosted = prisma_vault.getClaimableWithBoost(y)
    assert boosted[0] > 0
    assert strategy.claimsAreMaxBoosted()

    # now we should be able to claim without forcing
    # update our minProfit so our harvest triggers true
    strategy.setHarvestTriggerParams(1, 1000000e6, {"from": gov})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    # update our maxProfit so harvest triggers true
    strategy.setHarvestTriggerParams(1000000e6, 1, {"from": gov})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True

    # we shouldn't get any more yPRISMA if we turn off claims, but we may have received some above if we were max boosted
    before = yprisma.balanceOf(strategy)
    strategy.setClaimParams(False, False, {"from": vault.governance()})

    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    assert yprisma.balanceOf(strategy) == before

    # turn claiming back on
    strategy.setClaimParams(False, True, {"from": vault.governance()})

    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    assert yprisma.balanceOf(strategy) > 0


def test_yprisma_force_claim(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    sleep_time,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    yprisma,
):
    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})

    # set this to false so we allow yPRISMA to accumulate in the strategy
    use_yswaps = False

    receiver = Contract(strategy.prismaReceiver())
    eid = receiver.emissionId()
    prisma_vault = Contract(strategy.prismaVault(), owner=receiver)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )
    claimable = receiver.claimableReward(strategy).dict()
    # Check if any non-zero values (shouldn't have any, should have small amounts for all assets)
    assert any(x for x in (claimable if isinstance(claimable, tuple) else (claimable,)))

    chain.sleep(sleep_time)

    # force claim from convex's receiver
    assert yprisma.balanceOf(strategy) == 0
    convex_delegate = "0x8ad7a9e2B3Cd9214f36Cb871336d8ab34DdFdD5b"
    strategy.claimRewards(convex_delegate, 5000, {"from": vault.governance()})
    assert yprisma.balanceOf(strategy) > 0
    balance_1 = yprisma.balanceOf(strategy)

    # sleep to get to the new epoch
    chain.sleep(60 * 60 * 24 * 7)
    chain.mine()

    # turn off claims to not add any more yprisma with the next harvest
    strategy.setClaimParams(False, False, {"from": vault.governance()})

    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )

    # make sure we didn't add more yprisma
    balance_2 = yprisma.balanceOf(strategy)
    assert balance_1 == balance_2

    # turn claiming back on
    strategy.setClaimParams(False, True, {"from": vault.governance()})

    claimable_profit = strategy.claimableProfitInUsdc()
    assert claimable_profit > 0
    print("🤑 Claimable profit next epoch:", claimable_profit / 1e6)

    prisma_vault.allocateNewEmissions(eid)
    receiver.claimableReward(strategy)
    y = "0x90be6DFEa8C80c184C442a36e17cB2439AAE25a7"
    boosted = prisma_vault.getClaimableWithBoost(y)
    assert boosted[0] > 0
    assert strategy.claimsAreMaxBoosted()
    assert yprisma.balanceOf(strategy) == balance_1 == balance_2

    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
        force_claim=False,
    )

    # now we should have more yprisma claimed
    assert yprisma.balanceOf(strategy) > balance_2


# test removing a strategy from the withdrawal queue
def test_remove_from_withdrawal_queue(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    sleep_time,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
):
    ## deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
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

    # simulate earnings, harvest
    chain.sleep(sleep_time)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # removing a strategy from the queue shouldn't change its assets
    before = strategy.estimatedTotalAssets()
    vault.removeStrategyFromQueue(strategy, {"from": gov})
    after = strategy.estimatedTotalAssets()
    assert before == after

    # check that our strategy is no longer in the withdrawal queue's 20 addresses
    addresses = []
    for x in range(19):
        address = vault.withdrawalQueue(x)
        addresses.append(address)
    print(
        "Strategy Address: ",
        strategy.address,
        "\nWithdrawal Queue Addresses: ",
        addresses,
    )
    assert not strategy.address in addresses


# test revoking a strategy from the vault
def test_revoke_strategy_from_vault(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    RELATIVE_APPROX,
    which_strategy,
):

    ## deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
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

    # sleep to earn some yield
    chain.sleep(sleep_time)

    # record our assets everywhere
    vault_assets_starting = vault.totalAssets()
    vault_holdings_starting = token.balanceOf(vault)
    strategy_starting = strategy.estimatedTotalAssets()

    # revoke and harvest
    vault.revokeStrategy(strategy.address, {"from": gov})

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # harvest again to get the last of our profit with ySwaps
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

        # check our current status
        print("\nAfter yswaps extra harvest")
        strategy_params = check_status(strategy, vault)

        # make sure we recorded our gain properly
        if not no_profit:
            assert profit > 0

    # confirm we made money, or at least that we have about the same
    vault_assets_after_revoke = vault.totalAssets()
    strategy_assets_after_revoke = strategy.estimatedTotalAssets()

    if no_profit:
        assert (
            pytest.approx(vault_assets_after_revoke, rel=RELATIVE_APPROX)
            == vault_assets_starting
        )
        assert (
            pytest.approx(token.balanceOf(vault), rel=RELATIVE_APPROX)
            == vault_holdings_starting + strategy_starting
        )
    else:
        assert vault_assets_after_revoke > vault_assets_starting
        assert token.balanceOf(vault) > vault_holdings_starting + strategy_starting

    # should be zero in our strategy
    assert pytest.approx(strategy_assets_after_revoke, rel=RELATIVE_APPROX) == 0

    # simulate five days of waiting for share price to bump back up
    chain.sleep(86400 * 5)
    chain.mine(1)

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same (profit whale has to be different from normal whale)
    vault.withdraw({"from": whale})
    if no_profit:
        assert (
            pytest.approx(token.balanceOf(whale), rel=RELATIVE_APPROX) == starting_whale
        )
    else:
        assert token.balanceOf(whale) > starting_whale


# test the setters on our strategy
def test_setters(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    which_strategy,
    use_yswaps,
    profit_whale,
    profit_amount,
    target,
    strategist,
    tests_using_tenderly,
):
    # deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    name = strategy.name()

    # test our setters in baseStrategy
    strategy.setMaxReportDelay(1e18, {"from": gov})
    strategy.setMinReportDelay(100, {"from": gov})
    strategy.setRewards(gov, {"from": gov})
    strategy.setStrategist(gov, {"from": gov})

    ######### BELOW WILL NEED TO BE UPDATED BASED SETTERS OUR STRATEGY HAS #########
    # special setter for frax
    if which_strategy == 4:
        strategy.setLockTime(90000 * 7, {"from": gov})

        if not tests_using_tenderly:
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
        maxToStake = amount * 0.75
        minToStake = 100
        strategy.setDepositParams(minToStake, maxToStake, False, {"from": gov})
        with brownie.reverts():
            strategy.setDepositParams(maxToStake, minToStake, False, {"from": gov})

    # harvest our credit
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    if which_strategy == 4:
        total_staked = strategy.stakedBalance()
        assert total_staked == maxToStake
        assert strategy.estimatedTotalAssets() > total_staked

        # get the rest of our funds staked
        chain.sleep(1)
        chain.mine(1)
        strategy.setDepositParams(1e21, 1e29, False, {"from": gov})
        strategy.harvest({"from": gov})
        assert strategy.estimatedTotalAssets() >= amount

    # check that we have claimable rewards, have to call for frax tho
    if which_strategy == 4:
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

        if not tests_using_tenderly:
            # test our reverts as well
            with brownie.reverts():
                strategy.setLocalKeepCrvs(1000000, 0, {"from": gov})
            with brownie.reverts():
                strategy.setLocalKeepCrvs(0, 100000000, {"from": gov})
    elif which_strategy == 1:
        strategy.setVoter(gov, {"from": gov})
        strategy.setLocalKeepCrv(10, {"from": gov})

        if not tests_using_tenderly:
            # test our reverts as well
            with brownie.reverts():
                strategy.setLocalKeepCrv(1000000, {"from": gov})

    if which_strategy == 2:
        strategy.setVoters(gov, gov, gov, {"from": gov})
        strategy.setLocalKeepCrvs(10, 10, 10, {"from": gov})
        if not tests_using_tenderly:
            # test our reverts as well
            with brownie.reverts():
                strategy.setLocalKeepCrvs(1000000, 0, 0, {"from": gov})
            with brownie.reverts():
                strategy.setLocalKeepCrvs(0, 100000000, 0, {"from": gov})

    if which_strategy == 3:
        strategy.setVoter(gov, {"from": gov})
        strategy.setLocalKeepCrv(10, {"from": gov})
        if not tests_using_tenderly:
            # test our reverts as well
            with brownie.reverts():
                strategy.setLocalKeepCrv(1000000, 0, 0, {"from": gov})

    elif which_strategy == 4:
        strategy.setVoters(gov, gov, gov, {"from": gov})
        strategy.setLocalKeepCrvs(10, 10, 10, {"from": gov})

        if not tests_using_tenderly:
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


# test sweeping out tokens
def test_sweep(
    gov,
    token,
    vault,
    whale,
    strategy,
    to_sweep,
    amount,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    tests_using_tenderly,
):
    # deposit to the vault after approving
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

    # we can sweep out non-want tokens
    strategy.sweep(to_sweep, {"from": gov})

    # Strategy want token doesn't work
    token.transfer(strategy.address, amount, {"from": whale})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0

    if not tests_using_tenderly:
        with brownie.reverts():
            strategy.sweep(token, {"from": gov})
        with brownie.reverts():
            strategy.sweep(to_sweep, {"from": whale})

        # Vault share token doesn't work
        with brownie.reverts():
            strategy.sweep(vault.address, {"from": gov})
