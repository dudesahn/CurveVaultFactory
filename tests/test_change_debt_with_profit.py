import brownie
from brownie import chain
import math

# test changing the debtRatio on a strategy, donating some assets, and then harvesting it
def test_change_debt_with_profit(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})

    # store our values before we start doing weird stuff
    prev_params = vault.strategies(strategy)
    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, currentDebt / 2, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == currentDebt / 2

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 10
    token.transfer(strategy, donation, {"from": whale})

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # check that we've recorded a gain
    assert profit > 0

    # specifically check that our gain is greater than our donation or confirm we're no more than 5 wei off.
    assert new_params["totalGain"] - prev_params[
        "totalGain"
    ] > donation or math.isclose(
        new_params["totalGain"] - prev_params["totalGain"], donation, abs_tol=5
    )

    # check to make sure that our debtRatio is about half of our previous debt
    assert new_params["debtRatio"] == currentDebt / 2

    # check that we didn't add any more loss, or at least no more than 2 wei
    assert new_params["totalLoss"] == prev_params["totalLoss"] or math.isclose(
        new_params["totalLoss"], prev_params["totalLoss"], abs_tol=2
    )

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available (within 1 token)
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # we sleep 10 hours above specifically for this check
    assert math.isclose(
        vault.totalAssets() * new_params["debtRatio"] / 10_000,
        strategy.estimatedTotalAssets() + vault.creditAvailable(strategy),
        abs_tol=1e18,
    )


# test changing the debtRatio on a strategy, donating some assets, and then harvesting it
def test_change_debt_with_profit_some_lost(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    sleep_time,
    profit_amount,
    profit_whale,
    rewardsContract,
    cvxDeposit,
    which_strategy,
    crv,
    convexToken,
    has_rewards,
    rewards_token,
    gauge_is_not_tokenized,
    gauge,
    voter,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})

    # store our values before we start doing weird stuff
    prev_params = vault.strategies(strategy)
    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, currentDebt / 2, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == currentDebt / 2

    # send away a bit of funds, will need to alter this based on strategy
    if which_strategy == 0:
        # set claim rewards to true and send away CRV and CVX so we don't have dust leftover
        strategy.setClaimRewards(True, {"from": gov})

        # impersonate strategy to manually unwrap the funds and send back to strategy
        to_withdraw = amount / 11
        rewardsContract.withdraw(to_withdraw, True, {"from": strategy})
        chain.sleep(1)
        to_send = cvxDeposit.balanceOf(strategy)
        print("cvxToken Balance of Strategy", to_send)
        cvxDeposit.transfer(gov, to_send, {"from": strategy})
        to_send = crv.balanceOf(strategy)
        crv.transfer(gov, to_send, {"from": strategy})
        to_send = convexToken.balanceOf(strategy)
        convexToken.transfer(gov, to_send, {"from": strategy})
        if has_rewards:
            to_send = rewards_token.balanceOf(strategy)
            rewards_token.transfer(gov, to_send, {"from": strategy})
    elif which_strategy == 1:
        if gauge_is_not_tokenized:
            return
        # send all funds out of the gauge
        to_withdraw = amount / 11
        print("Gauge Balance to send", to_withdraw / 1e18)
        gauge.transfer(gov, to_withdraw, {"from": voter})
        to_send = crv.balanceOf(strategy)
        crv.transfer(gov, to_send, {"from": strategy})
        if has_rewards:
            to_send = rewards_token.balanceOf(strategy)
            rewards_token.transfer(gov, to_send, {"from": strategy})
    else:
        if which_strategy == 2:
            # wait another week so our frax LPs are unlocked
            chain.sleep(86400 * 7)
            chain.mine(1)

        # impersonate strategy to manually unwrap the funds and send back to strategy
        to_withdraw = amount / 11
        rewardsContract.withdraw(to_withdraw, True, {"from": strategy})
        chain.sleep(1)
        to_send = cvxDeposit.balanceOf(strategy)
        print("cvxToken Balance of Strategy", to_send)
        cvxDeposit.transfer(gov, to_send, {"from": strategy})
        to_send = crv.balanceOf(strategy)
        crv.transfer(gov, to_send, {"from": strategy})
        to_send = convexToken.balanceOf(strategy)
        convexToken.transfer(gov, to_send, {"from": strategy})

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 10
    token.transfer(strategy, donation, {"from": whale})

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # check that we've recorded a gain
    assert profit > 0

    # check the difference between our loss (manual withdrawal) and donation
    to_check = donation - to_withdraw
    assert to_check > 0

    # specifically check that our gain is greater than our donation or confirm we're no more than 5 wei off.
    assert new_params["totalGain"] - prev_params[
        "totalGain"
    ] > to_check or math.isclose(
        new_params["totalGain"] - prev_params["totalGain"], to_check, abs_tol=5
    )

    # check to make sure that our debtRatio is about half of our previous debt
    assert new_params["debtRatio"] == currentDebt / 2

    # check that we didn't add any more loss, or at least no more than 2 wei
    assert new_params["totalLoss"] == prev_params["totalLoss"] or math.isclose(
        new_params["totalLoss"], prev_params["totalLoss"], abs_tol=2
    )

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available (within 1 token)
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # we sleep 10 hours above specifically for this check
    assert math.isclose(
        vault.totalAssets() * new_params["debtRatio"] / 10_000,
        strategy.estimatedTotalAssets() + vault.creditAvailable(strategy),
        abs_tol=1e18,
    )


# test changing the debtRatio on a strategy, donating some assets, and then harvesting it
def test_change_debt_with_profit_all_lost(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    sleep_time,
    profit_amount,
    profit_whale,
    rewardsContract,
    cvxDeposit,
    which_strategy,
    crv,
    convexToken,
    has_rewards,
    rewards_token,
    gauge_is_not_tokenized,
    gauge,
    voter,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})

    # store our values before we start doing weird stuff
    prev_params = vault.strategies(strategy)
    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, currentDebt / 2, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == currentDebt / 2

    # send away all funds, will need to alter this based on strategy
    if which_strategy == 0:
        # set claim rewards to true and send away CRV and CVX
        strategy.setClaimRewards(True, {"from": gov})
        strategy.withdrawToConvexDepositTokens({"from": gov})
        chain.sleep(1)
        # call this again to hit both sides of the if statement
        strategy.withdrawToConvexDepositTokens({"from": gov})
        to_send = cvxDeposit.balanceOf(strategy)
        print("cvxToken Balance of Strategy", to_send)
        cvxDeposit.transfer(gov, to_send, {"from": strategy})
        to_send = crv.balanceOf(strategy)
        crv.transfer(gov, to_send, {"from": strategy})
        to_send = convexToken.balanceOf(strategy)
        convexToken.transfer(gov, to_send, {"from": strategy})
        if has_rewards:
            to_send = rewards_token.balanceOf(strategy)
            rewards_token.transfer(gov, to_send, {"from": strategy})
        assert strategy.estimatedTotalAssets() == 0
    else:
        if gauge_is_not_tokenized:
            return
        # send all funds out of the gauge
        to_send = gauge.balanceOf(voter)
        print("Gauge Balance of Vault", to_send / 1e18)
        gauge.transfer(gov, to_send, {"from": voter})
        to_send = crv.balanceOf(strategy)
        crv.transfer(gov, to_send, {"from": strategy})
        if has_rewards:
            to_send = rewards_token.balanceOf(strategy)
            rewards_token.transfer(gov, to_send, {"from": strategy})
        assert strategy.estimatedTotalAssets() == 0

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 10
    token.transfer(strategy, donation, {"from": whale})

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    chain.mine(1)
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # check that profit is zero
    assert profit == 0

    # check that we had a big loss
    assert new_params["totalLoss"] > prev_params["totalLoss"]

    # check that we have some assets left
    assert strategy.estimatedTotalAssets() > 0
