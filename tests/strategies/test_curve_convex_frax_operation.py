import brownie
from brownie import chain
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
):
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
        strategy.setVoter(gov, {"from": gov})
        strategy.setLocalKeepCrv(1000, {"from": gov})
    else:
        with brownie.reverts():
            strategy.setLocalKeepCrvs(1000, 1000, 1000, {"from": gov})
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
        strategy.setVoters(gov, gov, {"from": gov})

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
        strategy.setVoter(gov, {"from": gov})

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
        strategy.setVoters(gov, gov, gov, {"from": gov})

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
    if which_strategy != 2:
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
    if which_strategy != 2:
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
    if which_strategy != 2:
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
    if which_strategy != 2:
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
    print("Max keks:", strategy.maxKeks())
    print("Next kek:", strategy.nextKek())
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
    if which_strategy != 2:
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
    print("Max keks:", strategy.maxKeks())
    print("Next kek:", strategy.nextKek())
    locked = strategy.stillLockedStake() / 1e18
    print("Locked stake:", locked)

    # test withdrawing 1 kek manually at a time
    assert strategy.balanceOfWant() == profit_amount
    index_to_withdraw = strategy.nextKek() - 1

    # can't withdraw yet, need to wait
    with brownie.reverts():
        strategy.manualWithdraw(index_to_withdraw, {"from": gov})

    chain.sleep(86400 * 7)
    chain.mine(1)
    strategy.manualWithdraw(index_to_withdraw, {"from": gov})
    assert strategy.balanceOfWant() > 0
