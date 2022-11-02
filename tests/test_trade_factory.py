import brownie
from brownie import Contract
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
):
    rando = accounts[5]
    assert strategy.keeper() == keeper_contract
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    

    keeper_contract.harvestStrategy(strategy, {'from': rando})
    chain.sleep(10*60*6)
    booster.earmarkRewards(strategy.pid(), {"from": rando})

    #wait and harvest again to get tokens
    chain.sleep(60*60*6)

    keeper_contract.harvestStrategy(strategy, {'from': rando})

    crv = interface.ERC20(strategy.crv())
    cvx = interface.ERC20(strategy.convexToken())

    assert crv.balanceOf(strategy) > 0
    assert cvx.balanceOf(strategy) > 0

    #rando cant sweep
    with brownie.reverts():
        crv.transferFrom(strategy, rando, crv.balanceOf(strategy)/2, {'from': rando})
    with brownie.reverts():
        cvx.transferFrom(strategy, rando, cvx.balanceOf(strategy)/2, {'from': rando})
    
    crv.transferFrom(strategy, rando, crv.balanceOf(strategy)/2, {'from': new_trade_factory})
    cvx.transferFrom(strategy, rando, cvx.balanceOf(strategy)/2, {'from': new_trade_factory})

    strategy.removeTradeFactoryPermissions( {'from': gov})
    assert crv.balanceOf(strategy) > 0
    assert cvx.balanceOf(strategy) > 0
    #trae factory now cant sweep
    with brownie.reverts():
        crv.transferFrom(strategy, rando, crv.balanceOf(strategy)/2, {'from': new_trade_factory})
    with brownie.reverts():
        cvx.transferFrom(strategy, rando, cvx.balanceOf(strategy)/2, {'from': new_trade_factory})


    #cahnge permissions
    strategy.updateTradeFactory(new_trade_factory, {'from': gov})
    
    crv.transferFrom(strategy, rando, crv.balanceOf(strategy)/2, {'from': new_trade_factory})
    cvx.transferFrom(strategy, rando, cvx.balanceOf(strategy)/2, {'from': new_trade_factory})
    
    