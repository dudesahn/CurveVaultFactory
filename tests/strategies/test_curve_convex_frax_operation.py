import brownie
from brownie import chain, ZERO_ADDRESS, Contract
import pytest
from utils import harvest_strategy


# this test makes sure we can use keepCVX and keepCRV
def test_keep(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    voter,
    crv,
    fxs,
    amount,
    sleep_time,
    convex_token,
    no_profit,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    which_strategy,
    new_proxy,
    yprisma,
):
    # don't do for FXN, no keep
    if which_strategy == 3:
        print("\n🚫 FXN strategy has no keep, skipping...\n")
        return

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})

    # harvest as-is before we have yield to hit all parts of our if statement
    if which_strategy == 0:
        # need to set voters first if we're trying to set keep
        with brownie.reverts():
            strategy.setLocalKeepCrvs(1000, 1000, {"from": gov})
        strategy.setVoters(gov, gov, {"from": gov})
        strategy.setLocalKeepCrvs(1000, 1000, {"from": gov})
    elif which_strategy == 1:
        strategy.setVoter(ZERO_ADDRESS, {"from": gov})
        # need to set voters first if we're trying to set keep
        with brownie.reverts():
            strategy.setLocalKeepCrv(1000, {"from": gov})
        strategy.setVoter(voter, {"from": gov})
        strategy.setLocalKeepCrv(1000, {"from": gov})
    elif which_strategy == 2:
        # need to set voters first if we're trying to set keep
        with brownie.reverts():
            strategy.setLocalKeepCrvs(1000, 1000, 1000, {"from": gov})
        strategy.setVoters(gov, gov, gov, {"from": gov})
        strategy.setLocalKeepCrvs(1000, 1000, 1000, {"from": gov})
    else:
        with brownie.reverts():
            strategy.setLocalKeepCrvs(1000, 1000, 1000, {"from": gov})
        with brownie.reverts():
            strategy.setLocalKeepCrvs(0, 1000, 1000, {"from": gov})
        with brownie.reverts():
            strategy.setLocalKeepCrvs(0, 0, 1000, {"from": gov})
        strategy.setVoters(gov, gov, gov, {"from": gov})
        strategy.setLocalKeepCrvs(1000, 1000, 1000, {"from": gov})

    # harvest our funds in
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep to get some profit
    chain.sleep(sleep_time)
    chain.mine(1)

    # normal operation
    if which_strategy == 0:
        treasury_before = convex_token.balanceOf(strategy.convexVoter())

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = convex_token.balanceOf(strategy.convexVoter())
        if not no_profit:
            assert treasury_after > treasury_before
    elif which_strategy == 1:
        treasury_before = crv.balanceOf(strategy.curveVoter())

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = crv.balanceOf(strategy.curveVoter())
        if not no_profit:
            assert treasury_after > treasury_before
    elif which_strategy == 2:
        treasury_before = yprisma.balanceOf(strategy.yprismaVoter())

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = yprisma.balanceOf(strategy.yprismaVoter())
        if not no_profit:
            assert treasury_after > treasury_before
    else:
        treasury_before = fxs.balanceOf(strategy.fraxVoter())

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = fxs.balanceOf(strategy.fraxVoter())
        if not no_profit:
            assert treasury_after > treasury_before

    # keepCRV off only
    if which_strategy == 0:
        strategy.setLocalKeepCrvs(0, 0, {"from": gov})
        treasury_before = convex_token.balanceOf(strategy.convexVoter())

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = convex_token.balanceOf(strategy.convexVoter())
        assert treasury_after == treasury_before
    elif which_strategy == 1:
        strategy.setLocalKeepCrv(0, {"from": gov})
        treasury_before = crv.balanceOf(strategy.curveVoter())

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = crv.balanceOf(strategy.curveVoter())
        assert treasury_after == treasury_before
    elif which_strategy == 2:
        strategy.setLocalKeepCrvs(0, 0, 0, {"from": gov})
        treasury_before = crv.balanceOf(strategy.curveVoter())

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = crv.balanceOf(strategy.curveVoter())
        assert treasury_after == treasury_before
    else:
        strategy.setLocalKeepCrvs(0, 0, 0, {"from": gov})
        strategy.setVoters(gov, gov, gov, {"from": gov})
        treasury_before = fxs.balanceOf(strategy.fraxVoter())

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        treasury_after = fxs.balanceOf(strategy.fraxVoter())
        assert treasury_after == treasury_before

    # voter off only
    if which_strategy == 0:
        strategy.setLocalKeepCrvs(1000, 1000, {"from": gov})
        strategy.setVoters(ZERO_ADDRESS, ZERO_ADDRESS, {"from": gov})

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    elif which_strategy == 1:
        strategy.setLocalKeepCrv(1000, {"from": gov})
        strategy.setVoter(ZERO_ADDRESS, {"from": gov})

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    else:
        strategy.setLocalKeepCrvs(1000, 1000, 1000, {"from": gov})
        strategy.setVoters(ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS, {"from": gov})

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    # both off
    if which_strategy == 0:
        strategy.setLocalKeepCrvs(0, 0, {"from": gov})

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    elif which_strategy == 1:
        strategy.setLocalKeepCrv(0, {"from": gov})

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    else:
        strategy.setLocalKeepCrvs(0, 0, 0, {"from": gov})

        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )


# this tests having multiple rewards tokens on our strategy proxy
def test_proxy_rewards(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    voter,
    crv,
    fxs,
    amount,
    sleep_time,
    convex_token,
    no_profit,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    which_strategy,
    new_proxy,
    has_rewards,
):
    # only do for curve strat
    if which_strategy != 1 or not has_rewards:
        print("\nNot Curve strategy and/or no extra rewards token\n")
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    newWhale = token.balanceOf(whale)

    # harvest funds in
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # simulate profits
    chain.sleep(sleep_time)
    chain.mine(1)

    # add a second rewards token to our array, doesn't matter what
    second_reward_token = fxs
    fxs_whale = accounts.at("0xc8418aF6358FFddA74e09Ca9CC3Fe03Ca6aDC5b0", force=True)
    fxs.transfer(voter, 100e18, {"from": fxs_whale})
    new_proxy.approveRewardToken(second_reward_token, {"from": gov})
    strategy.updateRewards([rewards_token, second_reward_token], {"from": gov})
    assert fxs.balanceOf(voter) > 0

    # harvest
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert fxs.balanceOf(voter) == 0

    crv_balance = crv.balanceOf(strategy)
    assert crv_balance > 0
    print("CRV Balance:", crv_balance / 1e18)

    rewards_balance = rewards_token.balanceOf(strategy)
    assert rewards_balance > 0
    print("Rewards Balance:", rewards_balance / 1e18)

    rewards_balance_too = second_reward_token.balanceOf(strategy)
    assert rewards_balance_too > 0
    print("Second Rewards Token Balance:", rewards_balance_too / 1e18)


# lower our number of keks
def test_lower_keks(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # can't do this yet since we're still locked
    with brownie.reverts():
        strategy.setMaxKeks(3, {"from": gov})

    # can't withdraw everything right now
    with brownie.reverts():
        vault.withdraw({"from": whale})

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # can't set to zero
    with brownie.reverts():
        strategy.setMaxKeks(0, {"from": gov})

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # can't harvest again as funds are locked, but only if we have something to harvest in
    with brownie.reverts():
        vault.deposit(amount / 20, {"from": whale})
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

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
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])

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
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])

    # lower now
    strategy.setMaxKeks(3, {"from": gov})
    print("Keks successfullly lowered to 3")

    # withdraw everything
    vault.withdraw({"from": whale})

    # should still be able to lower keks when strategy is empty
    strategy.setMaxKeks(1, {"from": gov})


# lower our number of keks after we get well above our maxKeks
def test_lower_keks_part_two(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # lower it immediately
    strategy.setMaxKeks(3, {"from": gov})

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep since our 3 keks are full
    chain.sleep(86400 * 7)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

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
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
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
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # sleep for 3 more days to fully unlock our first kek
    chain.sleep(86400 * 3)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

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
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # test withdrawing 1 kek manually at a time
    assert strategy.balanceOfWant() == profit_amount
    index_to_withdraw = strategy.kekInfo()["nextKek"] - 1

    # can't withdraw yet, need to wait
    with brownie.reverts():
        strategy.manualWithdraw(index_to_withdraw, {"from": gov})

    chain.sleep(86400 * 7)
    chain.mine(1)
    strategy.manualWithdraw(index_to_withdraw, {"from": gov})
    assert strategy.balanceOfWant() > 0


# lower our number of keks
def test_lower_keks_add_to_existing(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # set it so we don't add new keks and only deposit to existing ones, once we reach our max
    strategy.setDepositParams(1e18, 5_000_000e18, True, {"from": gov})

    # since we do so many harvests here, reduce our profit_amount
    profit_amount = profit_amount / 2.5

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # can't do this yet since we're still locked
    with brownie.reverts():
        strategy.setMaxKeks(3, {"from": gov})

    # can't withdraw everything right now
    with brownie.reverts():
        vault.withdraw({"from": whale})

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    chain.mine(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)
    chain.mine(1)

    # can't set to zero
    with brownie.reverts():
        strategy.setMaxKeks(0, {"from": gov})

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # can't harvest again as funds are locked, but only if we have something to harvest in
    # ^^ this is from the normal test, obvs not true here
    vault.deposit(amount / 20, {"from": whale})
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

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
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])

    # try to decrease our max keks again
    # ^^ again, doesn't revert like we expect since it's no longer new locking
    strategy.setMaxKeks(2, {"from": gov})
    print("Wait for unlock to lower the number of keks we have")

    # wait another week so our frax LPs are unlocked
    chain.sleep(86400 * 7)
    chain.mine(1)

    # check how much locked stake we have (should be zero)
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])

    # lower now
    strategy.setMaxKeks(3, {"from": gov})
    print("Keks successfullly lowered to 3")

    # withdraw everything
    vault.withdraw({"from": whale})

    # should still be able to lower keks when strategy is empty
    strategy.setMaxKeks(1, {"from": gov})


# lower our number of keks after we get well above our maxKeks
def test_lower_keks_part_two_add_to_existing(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # set it so we don't add new keks and only deposit to existing ones, once we reach our max
    strategy.setDepositParams(1e18, 5_000_000e18, True, {"from": gov})

    # lower it immediately
    strategy.setMaxKeks(3, {"from": gov})

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep since our 3 keks are full
    chain.sleep(86400 * 7)

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # sleep to free them all up
    chain.sleep(86400 * 7)

    # lower down to 2, this should hit the other branch in our setMaxKeks
    strategy.setMaxKeks(2, {"from": gov})


# increase our number of keks
def test_increase_keks_add_to_existing(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # set it so we don't add new keks and only deposit to existing ones, once we reach our max
    strategy.setDepositParams(1e18, 5_000_000e18, True, {"from": gov})

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # increase our max keks to 7
    strategy.setMaxKeks(7, {"from": gov})
    print("successfully increased our keks")


# increase our number of keks
def test_keks_add_to_existing(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    gauge,
    voter,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    crv,
    booster,
    pid,
    which_strategy,
    profit_amount,
    profit_whale,
    use_yswaps,
    trade_factory,
    new_proxy,
    convex_token,
    frax_pid,
    target,
):
    if which_strategy != 4:
        return

    # set it so we don't add new keks and only deposit to existing ones, once we reach our max
    strategy.setDepositParams(1e18, 5_000_000e18, True, {"from": gov})

    # since we do so many harvests here, reduce our profit_amount
    profit_amount = profit_amount / 2.5

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount / 20, {"from": whale})
    newWhale = token.balanceOf(whale)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    next_kek = strategy.kekInfo()["nextKek"]
    print("First 5 harvests down")
    print("Max keks:", strategy.kekInfo()["maxKeks"])
    print("Next kek:", strategy.kekInfo()["nextKek"])
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    staking = Contract(strategy.stakingAddress())

    # make sure that a different kek is increasing in size each time
    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())

    # check visually that we are adding to a different kek each time using the output printout
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5

    # deposit and harvest multiple separate times to increase our nextKek
    vault.deposit(amount / 20, {"from": whale})
    chain.sleep(86400)
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    assert next_kek == strategy.kekInfo()["nextKek"]
    output = staking.lockedStakesOf(strategy.userVault())
    print(
        "Kek info",
        "\n",
        output[0],
        "\n",
        output[1],
        "\n",
        output[2],
        "\n",
        output[3],
        "\n",
        output[4],
    )
    assert len(output) == 5
    chain.sleep(86400 * 5)
    chain.mine(1)

    # whale should be able to withdraw all of his funds now
    vault.withdraw({"from": whale})
    assert vault.totalAssets() == 0


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
    which_strategy,
):
    # only for prisma
    if which_strategy != 2:
        print("\n🚫🌈 Not a PRISMA strategy, skipping...\n")
        return

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
    strategy.setMaxReportDelay(1)
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", tx)
    assert tx == True
    strategy.setMaxReportDelay(86400 * 21)

    # we have tiny profit but that's okay; our triggers should be false because we don't have max boost
    # update our minProfit so our harvest should trigger true
    # will be true/false same as above based on max boost
    strategy.setHarvestTriggerParams(1, 1000000e6, {"from": gov})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be false.", tx)
    assert tx == strategy.claimsAreMaxBoosted()

    # update our maxProfit, but should still be false
    strategy.setHarvestTriggerParams(1000000e6, 1, {"from": gov})
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be false.", tx)
    assert tx == False

    # force claim so we should be true
    strategy.setClaimParams(True, True, {"from": vault.governance()})
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

# ADD SOME MORE STUFF HERE W/ NEW TRIGGER CLAIM!!!!!! TEST TRIGGER FLIPS AND NEXT HARVEST DOES WHAT WE EXPECT IT TO
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
    which_strategy,
):
    # only for prisma
    if which_strategy != 2:
        print("\n🚫🌈 Not a PRISMA strategy, skipping...\n")
        return

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
