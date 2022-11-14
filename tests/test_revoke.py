import brownie
from brownie import Contract
from brownie import config
import math

# test revoking a strategy from the vault
def test_revoke_strategy_from_vault(
    gov,
    token,
    vault,
    whale,
    chain,
    strategy,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # sleep to earn some yield
    chain.sleep(sleep_time)
    chain.mine(1)

    vaultAssets_starting = vault.totalAssets()
    vault_holdings_starting = token.balanceOf(vault)
    strategy_starting = strategy.estimatedTotalAssets()
    vault.revokeStrategy(strategy.address, {"from": gov})

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

    chain.sleep(1)
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    strategy.harvest({"from": gov})
    chain.sleep(1)
    vaultAssets_after_revoke = vault.totalAssets()

    # confirm we made money, or at least that we have about the same
    assert vaultAssets_after_revoke >= vaultAssets_starting or math.isclose(
        vaultAssets_after_revoke, vaultAssets_starting, abs_tol=5
    )
    assert strategy.estimatedTotalAssets() == 0
    assert token.balanceOf(vault) >= vault_holdings_starting + strategy_starting

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same
    vault.withdraw({"from": whale})
    if is_slippery and no_profit:
        assert (
            math.isclose(token.balanceOf(whale), startingWhale, abs_tol=10)
            or token.balanceOf(whale) >= startingWhale
        )
    else:
        assert token.balanceOf(whale) >= startingWhale
