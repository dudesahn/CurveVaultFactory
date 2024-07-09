from brownie import chain, Contract, ZERO_ADDRESS, interface
from utils import harvest_strategy
import pytest


# test the our strategy's ability to deposit, harvest, and withdraw, with different optimal deposit tokens if we have them
def test_simple_harvest(
    gov,
    token,
    vault,
    whale,
    strategy,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    profit_whale,
    profit_amount,
    target,
    use_yswaps,
    which_strategy,
    staking_address,
    rewards_token,
    crv_whale,
    rewards_contract,
    tests_using_tenderly,
    RELATIVE_APPROX,
):
    ## deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    newWhale = token.balanceOf(whale)

    # for frax, we should have an adjustable minDeposit
    if which_strategy == 4:
        strategy.setDepositParams(0, amount / 10, False, {"from": gov})

    # harvest, store asset amount
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    old_assets = vault.totalAssets()
    assert old_assets > 0
    assert strategy.estimatedTotalAssets() > 0
    if which_strategy != 4:
        assert token.balanceOf(strategy) == 0

    if which_strategy == 4:
        assert vault.creditAvailable() == 0
        assert strategy.claimableProfitInUsdc() < strategy.harvestProfitMinInUsdc()
        assert strategy.claimableProfitInUsdc() < strategy.harvestProfitMaxInUsdc()
        assert strategy.balanceOfWant() > 0
        assert strategy.forceHarvestTriggerOnce() == False

        assert (
            chain.time() - vault.strategies(strategy.address)["lastReport"]
            < strategy.maxReportDelay()
        )
        chain.sleep(2)

        assert (
            chain.time() - vault.strategies(strategy.address)["lastReport"]
            > strategy.minReportDelay()
        )

        strategy.setMinReportDelay(2**256 - 1, {"from": gov})

        assert (
            chain.time() - vault.strategies(strategy.address)["lastReport"]
            < strategy.minReportDelay()
        )

        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False

        chain.sleep(50)

        strategy.setMinReportDelay(49, {"from": gov})

        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True

        staking_contract = Contract(staking_address)
        liq = staking_contract.lockedLiquidityOf(strategy.userVault())
        print("Locked stakes:", liq)
        print("Next kek:", strategy.kekInfo()["nextKek"])

    # simulate profits, the mine is needed for anvil
    chain.sleep(sleep_time)
    chain.mine(1)

    # check our pending profit for frax
    if which_strategy == 4:
        pending = strategy.getEarnedTokens()
        print("Strategy", strategy.name(), "pid:", strategy.fraxPid())
        print("Pending:", pending.dict())

    # check our claimable from prisma receiver
    if which_strategy == 2:
        receiver = Contract(strategy.prismaReceiver())
        print("Claimable from receiver:", receiver.claimableReward(strategy))

    # curve and FXN don't have a claimable amount readable
    if which_strategy not in [1, 3]:
        print(
            "🤑 Claimable profit for second harvest:",
            strategy.claimableProfitInUsdc() / 1e6,
        )

    # harvest, store new asset amount
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )
    # record this here so it isn't affected if we donate via ySwaps
    strategy_assets = strategy.estimatedTotalAssets()

    if which_strategy == 4:
        staking_address = Contract(strategy.stakingAddress())
        liq = staking_address.lockedLiquidityOf(strategy.userVault())
        print("Locked stakes:", liq)
        print("Next kek:", strategy.kekInfo()["nextKek"])

    # harvest again so the strategy reports the profit
    if use_yswaps:
        print("Using ySwaps for harvests")
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

    # evaluate our current total assets
    new_assets = vault.totalAssets()

    # confirm we made money, or at least that we have about the same
    if no_profit:
        assert pytest.approx(new_assets, rel=RELATIVE_APPROX) == old_assets
    else:
        new_assets > old_assets

    # simulate five days of waiting for share price to bump back up
    chain.sleep(86400 * 5)
    chain.mine(1)

    # Display estimated APR
    print(
        "\nEstimated APR: ",
        "{:.2%}".format(
            ((new_assets - old_assets) * (365 * 86400 / sleep_time)) / (strategy_assets)
        ),
    )

    if which_strategy == 4:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same
    vault.withdraw({"from": whale})
    if no_profit:
        assert (
            pytest.approx(token.balanceOf(whale), rel=RELATIVE_APPROX) == starting_whale
        )
    else:
        if profit_whale != whale:
            # note that if our profit whale and whale are the same we will have made no profits (since we just recycled funds around)
            assert token.balanceOf(whale) > starting_whale


# basic rewards check
def test_check_rewards(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    keeper,
    rewards,
    chain,
    contract_name,
    voter,
    new_proxy,
    pid,
    amount,
    pool,
    strategy_name,
    gauge,
    has_rewards,
    convex_token,
    which_strategy,
    sleep_time,
    rewards_template,
    rewards_whale,
    rewards_amount,
    rewards_token,
    test_donation,
    try_blocks,
    use_yswaps,
    profit_whale,
    profit_amount,
    target,
):
    # skip this test if we don't use rewards in this template
    if not rewards_template:
        return

    # if we're supposed to have a rewards token, make sure it's not CVX
    if has_rewards:
        assert rewards_token.address == strategy.rewardsTokens(0)
        print("\nThis is our rewards token:", rewards_token.name())
        assert convex_token != rewards_token
    else:
        assert ZERO_ADDRESS == strategy.rewardsTokens(0)

    # make sure we get our reward token when we harvest
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})

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

    if test_donation:
        # setup our rewards if we need to
        if not has_rewards:
            if which_strategy == 1:
                strategy.updateRewards(rewards_token, {"from": gov})
            else:
                strategy.updateRewards({"from": gov})

        if which_strategy == 1 and try_blocks:
            # test our proxy, some old gauges use blocks instead of seconds. make sure we're earning!
            chain.mine(240)
            assert gauge.balanceOf(voter) > 0
            balance_1 = gauge.claimable_reward(voter)
            print("Earned balance:", balance_1)
            chain.sleep(1)
            chain.mine(240)
            chain.sleep(1)
            balance_2 = gauge.claimable_reward(voter)
            print("Earned balance:", balance_2)
            assert balance_2 > balance_1
            tx = strategy.harvest({"from": gov})
            chain.mine(240)
            chain.sleep(1)
            balance_3 = gauge.claimable_reward(voter)
            print("Earned balance:", balance_3)
            assert balance_3 > balance_2
            proxy.claimRewards(gauge, rewards_token, {"from": strategy})
            assert rewards_token.balanceOf(strategy) > 0

        chain.sleep(sleep_time)

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

    if use_yswaps:
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

    normal_profit = profit
    print("Normal Profit:", normal_profit)

    if test_donation:
        rewards_token.transfer(strategy, rewards_amount, {"from": rewards_whale})
        chain.sleep(sleep_time)
        strategy.setDoHealthCheck(False, {"from": gov})

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

    reward_address = strategy.rewardsTokens(0)
    if reward_address != ZERO_ADDRESS:
        reward_token = interface.IERC20(reward_address)
        if reward_token.balanceOf(strategy) > 0:
            print("We have a reward token balance, send double profit")
            token.transfer(strategy, profit_amount, {"from": profit_whale})

    if use_yswaps:
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

    print("Rewards Profit:", profit)
    assert profit > normal_profit
