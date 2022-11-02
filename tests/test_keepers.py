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
    pid,
    vault,
    interface,
    whale,
    strategy,
    amount,
):
    rando = accounts[5]
    assert strategy.keeper() == keeper_contract
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    

    keeper_contract.harvestStrategy(strategy, {'from': rando})

    #assert that money deposited to aura
    assert strategy.stakedBalance() > 0

    balboost = interface.ERC20(booster.poolInfo(strategy.pid())['token'])


    strategy.withdrawToConvexDepositTokens({'from': gov})
    assert balboost.balanceOf(strategy) > 0
    strategy.sweep(balboost, {'from': gov})

    with brownie.reverts():
        keeper_contract.harvestStrategy(strategy, {'from': rando})

    #turn off healthcheck
    strategy.setDoHealthCheck(False, {'from': gov})
    keeper_contract.harvestStrategy(strategy, {'from': rando})