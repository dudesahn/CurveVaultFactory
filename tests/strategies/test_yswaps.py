import brownie
from brownie import ZERO_ADDRESS, interface, chain
from utils import harvest_strategy

# test our permissionless swaps and our trade handler functions as intended
def test_keepers_and_trade_handler(
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
    keeper_wrapper,
    trade_factory,
    crv_whale,
    which_strategy,
):
    # no testing needed if we're not using yswaps
    if not use_yswaps:
        return

    ## deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    newWhale = token.balanceOf(whale)

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

    # simulate profits
    chain.sleep(sleep_time)
    chain.mine(1)

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

    # set our keeper up
    strategy.setKeeper(keeper_wrapper, {"from": gov})

    # here we make sure we can harvest through our keeper wrapper
    keeper_wrapper.harvest(strategy, {"from": profit_whale})
    print("Keeper wrapper harvest works")

    ####### ADD LOGIC AS NEEDED FOR SENDING REWARDS TO STRATEGY #######
    # send our strategy some CRV. normally it would be sitting waiting for trade handler but we automatically process it
    crv = interface.IERC20(strategy.crv())
    crv.transfer(strategy, 100e18, {"from": crv_whale})

    # whale can't sweep, but trade handler can
    with brownie.reverts():
        crv.transferFrom(strategy, whale, crv.balanceOf(strategy) / 2, {"from": whale})

    crv.transferFrom(
        strategy, whale, crv.balanceOf(strategy) / 2, {"from": trade_factory}
    )

    # remove our trade handler
    strategy.removeTradeFactoryPermissions(True, {"from": gov})
    assert strategy.tradeFactory() == ZERO_ADDRESS
    assert crv.balanceOf(strategy) > 0

    # trade factory now cant sweep
    with brownie.reverts():
        crv.transferFrom(
            strategy, whale, crv.balanceOf(strategy) / 2, {"from": trade_factory}
        )

    # give back those permissions, now trade factory can sweep
    strategy.updateTradeFactory(trade_factory, {"from": gov})
    crv.transferFrom(
        strategy, whale, crv.balanceOf(strategy) / 2, {"from": trade_factory}
    )

    # remove again!
    strategy.removeTradeFactoryPermissions(False, {"from": gov})

    # update again
    strategy.updateTradeFactory(trade_factory, {"from": gov})

    # simulate profits
    chain.sleep(sleep_time)
    chain.mine(1)

    # can't set trade factory to zero
    with brownie.reverts():
        strategy.updateTradeFactory(ZERO_ADDRESS, {"from": gov})

    # update our rewards again, shouldn't really change things
    if which_strategy != 1:
        strategy.updateRewards({"from": gov})
    else:
        strategy.updateRewards([], {"from": gov})

    # check out our rewardsTokens
    if which_strategy == 0:
        # for convex, 0 position may be occupied by wrapped CVX token
        with brownie.reverts():
            strategy.rewardsTokens(1)
    if which_strategy == 1:
        with brownie.reverts():
            strategy.rewardsTokens(0)
    if which_strategy == 2:
        with brownie.reverts():
            strategy.rewardsTokens(0)

    # only gov can update rewards
    if which_strategy != 1:
        with brownie.reverts():
            strategy.updateRewards({"from": whale})
    else:
        with brownie.reverts():
            strategy.updateRewards([], {"from": whale})
