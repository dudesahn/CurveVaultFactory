import pytest
from utils import harvest_strategy, check_status
from brownie import chain

# test reducing the debtRatio on a strategy and then harvesting it
def test_change_debt(
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
    RELATIVE_APPROX,
    which_strategy,
):
    ## deposit to the vault after approving
    starting_whale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # check our current status
    print("\nAfter first harvest, before DR reduction")
    strategy_params = check_status(strategy, vault)

    # evaluate our current total assets
    old_assets = vault.totalAssets()
    initial_strategy_assets = strategy.estimatedTotalAssets()
    initial_debt = strategy_params["totalDebt"]
    starting_share_price = vault.pricePerShare()

    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    starting_debt_ratio = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, starting_debt_ratio / 2, {"from": gov})
    chain.sleep(sleep_time)

    # check our current status
    print("\nAfter reducing DR, before harvest")
    strategy_params = check_status(strategy, vault)

    # debtOutstanding should be ~ half of initial_debt. nothing else has changed yet
    assert (
        pytest.approx(vault.debtOutstanding(strategy), rel=RELATIVE_APPROX)
        == initial_debt / 2
    )
    assert strategy_params["totalDebt"] == initial_debt
    assert vault.creditAvailable(strategy) == 0

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

    # harvest to reduce our debt, send 50% of funds back to vault
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # check our current status
    print("\nAfter harvest to reduce debt")
    strategy_params = check_status(strategy, vault)

    # debtOutstanding should be zero, credit available will be much lower than 50% of vault but greater than zero (profits)
    assert vault.debtOutstanding(strategy) == 0
    # yswaps will not have taken this first batch of profit yet
    if use_yswaps:
        assert vault.creditAvailable(strategy) == 0
        assert strategy_params["totalGain"] == 0
    else:
        assert 0 < vault.creditAvailable(strategy) < strategy_params["totalDebt"] / 2
        assert strategy_params["totalGain"] > 0

    # strategy debt should be cut in half
    assert (
        pytest.approx(strategy_params["totalDebt"], rel=RELATIVE_APPROX)
        == initial_debt / 2
    )

    # no loss should have happened just by reducing the debt
    assert strategy_params["totalLoss"] == 0

    # make sure we reduced our assets properly, yswaps will also have profit sitting in strategy
    if use_yswaps:
        assert (
            pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
            == initial_strategy_assets / 2 + profit_amount
        )
    else:
        assert (
            pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
            == initial_strategy_assets / 2
        )

    # simulate earnings
    chain.sleep(sleep_time)

    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, starting_debt_ratio, {"from": gov})

    # check our current status
    print("\nAfter returning DR to 100%, before harvest")
    strategy_params = check_status(strategy, vault)

    # debtOutstanding should zero, credit available should be ~half of the vault
    assert vault.debtOutstanding(strategy) == 0
    assert (
        pytest.approx(vault.creditAvailable(strategy), rel=RELATIVE_APPROX)
        == vault.totalAssets() / 2
    )

    # strategy debt should still be ~half of starting as our profits haven't been sent to our strategy yet
    assert (
        pytest.approx(initial_debt / 2, rel=RELATIVE_APPROX)
        == strategy_params["totalDebt"]
    )

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

    # harvest to send our funds back to the strategy
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # check our current status
    print("\nAfter harvest to return DR to 100%")
    strategy_params = check_status(strategy, vault)

    ################# SET FALSE IF PROFIT EXPECTED. ADJUST AS NEEDED. #################
    # set this true if no profit on this test. it is normal for a strategy to not generate profit here.
    # realistically only wrapped tokens or every-block earners will see profits (convex, etc).
    # also checked in test_change_debt
    no_profit = False

    # debtOutstanding should be zero, credit available will be much lower than previously but greater than zero (profits)
    # however, if the strategy has no profit, or has inconsistent profit-taking, then we can have no credit here
    # also checked in test_emergency_exit_with_no_loss
    assert vault.debtOutstanding(strategy) == 0
    if no_profit:
        vault.creditAvailable(strategy) == 0
    else:
        assert 0 < vault.creditAvailable(strategy) < vault.totalAssets() / 2

    # evaluate our current total assets
    new_assets = vault.totalAssets()

    # confirm we made money, or at least that we have about the same
    if no_profit:
        assert pytest.approx(new_assets, rel=RELATIVE_APPROX) == old_assets
    else:
        assert new_assets > old_assets

    # simulate five days of waiting for share price to bump back up
    chain.sleep(86400 * 5)
    chain.mine(1)

    # check our current status
    print("\nAfter share price sleep")
    strategy_params = check_status(strategy, vault)

    # share price should have gone up, without loss except for special cases
    if no_profit:
        assert (
            pytest.approx(vault.pricePerShare(), rel=RELATIVE_APPROX)
            == starting_share_price
        )
    else:
        assert vault.pricePerShare() > starting_share_price
        assert strategy_params["totalLoss"] == 0

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same (profit whale has to be different from normal whale)
    vault.withdraw({"from": whale})
    if no_profit:
        assert (
            pytest.approx(token.balanceOf(whale), rel=RELATIVE_APPROX) == starting_whale
        )
    else:
        assert token.balanceOf(whale) > starting_whale


# test changing the debtRatio on a strategy, donating some assets, and then harvesting it
def test_change_debt_with_profit(
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
    RELATIVE_APPROX,
    which_strategy,
):
    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # check our current status
    print("\nAfter first harvest, before DR reduction")
    strategy_params = check_status(strategy, vault)

    # evaluate our current total assets
    old_assets = vault.totalAssets()
    initial_debt = strategy_params["totalDebt"]
    starting_share_price = vault.pricePerShare()
    initial_strategy_assets = strategy.estimatedTotalAssets()

    # store our values before we start doing weird stuff
    prev_params = strategy_params
    starting_debt_ratio = strategy_params["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, starting_debt_ratio / 2, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == starting_debt_ratio / 2

    # check our current status
    print("\nAfter DR reduction, before donation")
    strategy_params = check_status(strategy, vault)

    # debtOutstanding should be ~half of initial_debt. nothing else has changed yet
    assert (
        pytest.approx(vault.debtOutstanding(strategy), rel=RELATIVE_APPROX)
        == initial_debt / 2
    )
    assert strategy_params["totalDebt"] == initial_debt
    assert vault.creditAvailable(strategy) == 0

    # our whale donates to the vault, what a nice person!
    donation = amount / 4
    token.transfer(strategy, donation, {"from": whale})

    # turn off health check since we just took big profit from our donation
    strategy.setDoHealthCheck(False, {"from": gov})

    # check our current status
    print("\nAfter token donation, before harvest")
    strategy_params = check_status(strategy, vault)

    # we should have more assets but the same debt
    assert strategy.estimatedTotalAssets() > initial_strategy_assets
    assert strategy_params["totalDebt"] == initial_debt

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
        chain.sleep(86400 * 7)
        chain.mine(1)

    # harvest to reduce our debt, send 50% of funds back to vault
    (profit, loss) = harvest_strategy(
        use_yswaps,
        strategy,
        token,
        gov,
        profit_whale,
        profit_amount,
        target,
    )

    # check our current status
    print("\nAfter harvest to reduce debt")
    strategy_params = check_status(strategy, vault)

    # record our new strategy params
    new_params = strategy_params

    # no loss should have happened just by reducing the debt
    assert strategy_params["totalLoss"] == 0

    # debtOutstanding should be zero, credit available will be much lower than 50% of vault but greater than zero (profits)
    assert vault.debtOutstanding(strategy) == 0
    if not no_profit:
        assert 0 < vault.creditAvailable(strategy) < vault.totalAssets() / 2
    else:
        vault.creditAvailable(strategy) == 0

    # we should have gain now, whether using yswaps or not thanks to the donation
    assert strategy_params["totalGain"] > 0

    # strategy debt should be cut in half, profit hasn't been sent back to strategy yet
    assert (
        pytest.approx(strategy_params["totalDebt"], rel=RELATIVE_APPROX)
        == initial_debt / 2
    )

    # make sure we reduced our assets properly, yswaps will also have profit sitting in strategy
    if use_yswaps:
        assert (
            pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
            == initial_strategy_assets / 2 + profit_amount
        )
    else:
        assert (
            pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX)
            == initial_strategy_assets / 2
        )

    # sleep 5 days hours to allow share price to normalize
    chain.sleep(5 * 86400)
    chain.mine(1)

    # check our current status
    print("\nAfter share price sleep")
    strategy_params = check_status(strategy, vault)

    # share price should have gone up, without loss except for special cases
    if no_profit:
        assert (
            pytest.approx(vault.pricePerShare(), rel=RELATIVE_APPROX)
            == starting_share_price
        )
    else:
        assert vault.pricePerShare() > starting_share_price
        assert strategy_params["totalLoss"] == 0

    # check to make sure that our debtRatio is about half of our previous debt
    assert new_params["debtRatio"] == starting_debt_ratio / 2

    # specifically check that our profit is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    # yswaps also will not have seen profit from the first donation after only one harvest
    profit = new_params["totalGain"] - prev_params["totalGain"]
    if is_slippery and no_profit or use_yswaps:
        assert pytest.approx(profit, rel=RELATIVE_APPROX) == donation
    else:
        assert profit > donation
        assert profit > 0

    # check that we didn't add any more loss, and if we did only a little bit if slippery
    if is_slippery:
        assert (
            pytest.approx(new_params["totalLoss"], rel=RELATIVE_APPROX)
            == prev_params["totalLoss"]
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # a vault only knows it has assets if the strategy has reported. yswaps has extra profit donated to the strategy as well that has not yet been reported.
    if use_yswaps:
        assert pytest.approx(
            vault.totalAssets() * new_params["debtRatio"] / 10_000 + profit_amount,
            rel=RELATIVE_APPROX,
        ) == strategy.estimatedTotalAssets() + vault.creditAvailable(strategy)
    else:
        assert pytest.approx(
            vault.totalAssets() * new_params["debtRatio"] / 10_000, rel=RELATIVE_APPROX
        ) == strategy.estimatedTotalAssets() + vault.creditAvailable(strategy)
