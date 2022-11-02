import brownie
from brownie import chain
import math

# test passes as of 21-06-26
def test_change_debt_with_profit(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})

    # sleep long enough to make uniswap v3 happy (need minimum out)
    chain.sleep(86400)

    prev_params = vault.strategies(strategy).dict()

    currentDebt = vault.strategies(strategy)[2]
    vault.updateStrategyDebtRatio(strategy, currentDebt / 2, {"from": gov})
    assert vault.strategies(strategy)[2] == 5000

    # comment this out since we no longer use harvestTrigger from baseStrategy
    # tx = strategy.harvestTrigger(0, {"from": gov})
    # print("\nShould we harvest? Should be true.", tx)
    # assert tx == True

    # our whale donates dust to the vault, what a nice person!
    donation = 1e16
    token.transfer(strategy, donation, {"from": whale})

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy).dict()

    # sleep 10 hours to increase our credit available for last assert at the bottom.
    chain.sleep(60 * 60 * 10)

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
