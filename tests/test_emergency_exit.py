import math
import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-06-26
def test_emergency_exit(
    gov,
    token,
    vault,
    whale,
    strategy,
    chain,
    amount,
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit({"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    assert strategy.estimatedTotalAssets() == 0

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    # withdraw and confirm we made money
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) >= startingWhale


def test_emergency_exit_with_profit(
    gov,
    token,
    vault,
    whale,
    strategy,
    chain,
    amount,
):
    ## deposit to the vault after approving. turn off health check since we're doing weird shit
    strategy.setDoHealthCheck(False, {"from": gov})
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # set emergency and exit, then confirm that the strategy has no funds
    donation = amount
    token.transfer(strategy, donation, {"from": whale})
    strategy.setDoHealthCheck(False, {"from": gov})
    strategy.setEmergencyExit({"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    assert strategy.estimatedTotalAssets() == 0

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    # withdraw and confirm we made money
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) + donation >= startingWhale


def test_emergency_exit_with_no_gain_or_loss(
    gov,
    token,
    vault,
    whale,
    strategy,
    chain,
    gauge,
    cvxDeposit,
    amount,
):
    ## deposit to the vault after approving. turn off health check since we're doing weird shit
    strategy.setDoHealthCheck(False, {"from": gov})
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    # send away all funds, will need to alter this based on strategy
    strategy.withdrawToConvexDepositTokens({"from": gov})
    to_send = cvxDeposit.balanceOf(strategy)
    print("cvxToken Balance of Strategy", to_send)
    cvxDeposit.transfer(gov, to_send, {"from": strategy})
    assert strategy.estimatedTotalAssets() == 0

    # have our whale send in exactly our debtOutstanding
    whale_to_give = vault.debtOutstanding(strategy)
    token.transfer(strategy, whale_to_give, {"from": whale})

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit({"from": gov})
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    assert strategy.estimatedTotalAssets() == 0

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    # withdraw and confirm we made money, accounting for all of the funds we lost lol
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) + amount + whale_to_give >= startingWhale


def test_emergency_withdraw_method_0(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    strategist_ms,
    rewardsContract,
    cvxDeposit,
    amount,
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # set emergency exit so no funds will go back to strategy, and we assume that deposit contract is borked so we go through staking contract
    # here we assume that the swap out to curve pool tokens is borked, so we stay in cvx vault tokens and send to gov
    # we also assume extra rewards are fine, so we will collect them on harvest and withdrawal
    strategy.setClaimRewards(True, {"from": gov})
    strategy.setEmergencyExit({"from": gov})

    strategy.withdrawToConvexDepositTokens({"from": gov})
    # turn off health check since we're doing weird shit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)
    assert strategy.estimatedTotalAssets() == 0
    assert rewardsContract.balanceOf(strategy) == 0
    assert cvxDeposit.balanceOf(strategy) > 0

    # sweep this from the strategy with gov and wait until we can figure out how to unwrap them
    strategy.sweep(cvxDeposit, {"from": gov})
    assert cvxDeposit.balanceOf(gov) > 0


def test_emergency_withdraw_method_1(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    strategist_ms,
    rewardsContract,
    cvxDeposit,
    amount,
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # set emergency exit so no funds will go back to strategy, and we assume that deposit contract is borked so we go through staking contract
    # here we assume that the swap out to curve pool tokens is borked, so we stay in cvx vault tokens and send to gov
    # we also assume extra rewards are borked so we don't want them when harvesting or withdrawing
    strategy.setClaimRewards(False, {"from": gov})
    strategy.setEmergencyExit({"from": gov})

    strategy.withdrawToConvexDepositTokens({"from": gov})
    # turn off health check since we're doing weird shit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    assert strategy.estimatedTotalAssets() == 0
    assert rewardsContract.balanceOf(strategy) == 0
    assert cvxDeposit.balanceOf(strategy) > 0

    strategy.sweep(cvxDeposit, {"from": gov})
    assert cvxDeposit.balanceOf(gov) > 0
