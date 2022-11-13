import brownie
from brownie import Contract, ZERO_ADDRESS
from brownie import config
import math


def test_keepers(
    gov,
    accounts,
    keeper_contract,
    token,
    booster,
    interface,
    new_trade_factory,
    pid,
    vault,
    whale,
    strategy,
    chain,
    amount,
    crv,
    convexToken,
    sleep_time,
    profit_whale,
    profit_amount,
    which_strategy,
    rewards_token,
    has_rewards,
):
    rando = accounts[5]
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})

    # harvest to send funds to earn
    chain.sleep(1)
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)

    # simulate profits
    chain.sleep(sleep_time)
    chain.mine(1)

    # harvest, store new asset amount
    chain.sleep(1)
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    tx = strategy.harvest({"from": gov})
    chain.sleep(1)

    assert crv.balanceOf(strategy) > 0
    if which_strategy != 1:
        assert convexToken.balanceOf(strategy) > 0

    # rando cant sweep
    with brownie.reverts():
        crv.transferFrom(strategy, rando, crv.balanceOf(strategy) / 2, {"from": rando})
    if which_strategy != 1:
        with brownie.reverts():
            convexToken.transferFrom(strategy, rando, convexToken.balanceOf(strategy) / 2, {"from": rando})

    crv.transferFrom(
        strategy, rando, crv.balanceOf(strategy) / 2, {"from": new_trade_factory}
    )
    
    if which_strategy != 1:
        convexToken.transferFrom(
            strategy, rando, convexToken.balanceOf(strategy) / 2, {"from": new_trade_factory}
        )

    strategy.removeTradeFactoryPermissions({"from": gov})
    assert strategy.tradeFactory() == ZERO_ADDRESS
    
    # do it twice to hit both arms of the if statement
    strategy.removeTradeFactoryPermissions({"from": gov})
    
    assert crv.balanceOf(strategy) > 0
    if which_strategy != 1:
        assert convexToken.balanceOf(strategy) > 0
    
    # trade factory now cant sweep
    with brownie.reverts():
        crv.transferFrom(
            strategy, rando, crv.balanceOf(strategy) / 2, {"from": new_trade_factory}
        )
    if which_strategy != 1:
        with brownie.reverts():
            convexToken.transferFrom(
                strategy, rando, convexToken.balanceOf(strategy) / 2, {"from": new_trade_factory}
            )

    # change permissions
    strategy.updateTradeFactory(new_trade_factory, {"from": gov})

    crv.transferFrom(
        strategy, rando, crv.balanceOf(strategy) / 2, {"from": new_trade_factory}
    )

    if which_strategy != 1:
        convexToken.transferFrom(
            strategy, rando, convexToken.balanceOf(strategy) / 2, {"from": new_trade_factory}
        )

    # update again
    strategy.updateTradeFactory(new_trade_factory, {"from": gov})
    
    # update rewards
    if which_strategy == 1:
        strategy.updateRewards([rewards_token.address], {"from": gov})
    else:
        strategy.updateRewards({"from": gov})

    # simulate profits
    chain.sleep(sleep_time)
    chain.mine(1)

    # harvest, store new asset amount
    if has_rewards:
        chain.sleep(1)
        token.transfer(strategy, profit_amount, {"from": profit_whale})
        tx = strategy.harvest({"from": gov})
        chain.sleep(1)
    
    # set trade factory to zero
    strategy.updateTradeFactory(ZERO_ADDRESS, {"from": gov})
    
