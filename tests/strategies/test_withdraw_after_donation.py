import brownie
from brownie import chain, Contract, ZERO_ADDRESS
import math

# these tests all assess whether a strategy will hit accounting errors following donations to the strategy.
# lower debtRatio to 50%, donate, withdraw less than the donation, then harvest
def test_withdraw_after_donation_1(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    prev_params = vault.strategies(strategy)

    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, currentDebt / 2, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == currentDebt / 2

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 2
    token.transfer(strategy, donation, {"from": whale})

    # have our whale withdraw half of his donation, this ensures that we test withdrawing without pulling from the staked balance
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)
    vault.withdraw(donation / 2, {"from": whale})

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    tx = strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # specifically check that our gain is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery and no_profit:
        assert math.isclose(profit, donation, abs_tol=10) or profit >= donation
    else:
        assert profit >= donation
        assert profit >= 0

    # check that we didn't add any more loss, or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery:
        assert math.isclose(
            new_params["totalLoss"], prev_params["totalLoss"], abs_tol=10
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available (within 1 token)
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # we sleep 10 hours above specifically for this check
    assert math.isclose(
        vault.totalAssets() * new_params["debtRatio"] / 10_000,
        strategy.estimatedTotalAssets() + vault.creditAvailable(strategy),
        abs_tol=1e18,
    )


# lower debtRatio to 0, donate, withdraw less than the donation, then harvest
def test_withdraw_after_donation_2(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    prev_params = vault.strategies(strategy)

    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == 0

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 2
    token.transfer(strategy, donation, {"from": whale})

    # have our whale withdraw half of his donation, this ensures that we test withdrawing without pulling from the staked balance
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)
    vault.withdraw(donation / 2, {"from": whale})

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # specifically check that our gain is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery and no_profit:
        assert math.isclose(profit, donation, abs_tol=10) or profit >= donation
    else:
        assert profit >= donation
        assert profit >= 0

    # check that we didn't add any more loss, or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery:
        assert math.isclose(
            new_params["totalLoss"], prev_params["totalLoss"], abs_tol=10
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available (within 1 token)
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # we sleep 10 hours above specifically for this check
    assert math.isclose(
        vault.totalAssets() * new_params["debtRatio"] / 10_000,
        strategy.estimatedTotalAssets() + vault.creditAvailable(strategy),
        abs_tol=1e18,
    )


# lower debtRatio to 0, donate, withdraw more than the donation, then harvest
def test_withdraw_after_donation_3(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    prev_params = vault.strategies(strategy)

    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == 0

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 2
    token.transfer(strategy, donation, {"from": whale})

    # have our whale withdraws more than his donation, ensuring we pull from strategy
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)
    withdrawal = donation + amount / 4

    # convert since our PPS isn't 1 (live vault!)
    withdrawal_in_shares = withdrawal * 1e18 / vault.pricePerShare()
    vault.withdraw(withdrawal_in_shares, {"from": whale})

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # specifically check that our gain is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery and no_profit:
        assert math.isclose(profit, donation, abs_tol=10) or profit >= donation
    else:
        assert profit >= donation
        assert profit >= 0

    # check that we didn't add any more loss, or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery:
        assert math.isclose(
            new_params["totalLoss"], prev_params["totalLoss"], abs_tol=10
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available (within 1 token)
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # we sleep 10 hours above specifically for this check
    assert math.isclose(
        vault.totalAssets() * new_params["debtRatio"] / 10_000,
        strategy.estimatedTotalAssets() + vault.creditAvailable(strategy),
        abs_tol=1e18,
    )


# lower debtRatio to 50%, donate, withdraw more than the donation, then harvest
def test_withdraw_after_donation_4(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    prev_params = vault.strategies(strategy)

    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, currentDebt / 2, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == currentDebt / 2

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 2
    token.transfer(strategy, donation, {"from": whale})

    # have our whale withdraws more than his donation, ensuring we pull from strategy
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)
    withdrawal = donation + amount / 4

    # convert since our PPS isn't 1 (live vault!)
    withdrawal_in_shares = withdrawal * 1e18 / vault.pricePerShare()
    vault.withdraw(withdrawal_in_shares, {"from": whale})

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # specifically check that our gain is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery and no_profit:
        assert math.isclose(profit, donation, abs_tol=10) or profit >= donation
    else:
        assert profit >= donation
        assert profit >= 0

    # check that we didn't add any more loss, or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery:
        assert math.isclose(
            new_params["totalLoss"], prev_params["totalLoss"], abs_tol=10
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]

    # check to make sure that our debtRatio is about half of our previous debt
    assert new_params["debtRatio"] == currentDebt / 2

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available (within 1 token)
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # we sleep 10 hours above specifically for this check
    assert math.isclose(
        vault.totalAssets() * new_params["debtRatio"] / 10_000,
        strategy.estimatedTotalAssets() + vault.creditAvailable(strategy),
        abs_tol=1e18,
    )


# donate, withdraw more than the donation, then harvest
def test_withdraw_after_donation_5(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    prev_params = vault.strategies(strategy)

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 2
    token.transfer(strategy, donation, {"from": whale})

    # have our whale withdraws more than his donation, ensuring we pull from strategy
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)
    withdrawal = donation + amount / 4

    # convert since our PPS isn't 1 (live vault!)
    withdrawal_in_shares = withdrawal * 1e18 / vault.pricePerShare()
    vault.withdraw(withdrawal_in_shares, {"from": whale})

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # specifically check that our gain is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery and no_profit:
        assert math.isclose(profit, donation, abs_tol=10) or profit >= donation
    else:
        assert profit >= donation
        assert profit >= 0

    # check that we didn't add any more loss, or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery:
        assert math.isclose(
            new_params["totalLoss"], prev_params["totalLoss"], abs_tol=10
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available (within 1 token)
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # we sleep 10 hours above specifically for this check
    assert math.isclose(
        vault.totalAssets() * new_params["debtRatio"] / 10_000,
        strategy.estimatedTotalAssets() + vault.creditAvailable(strategy),
        abs_tol=1e18,
    )


# donate, withdraw less than the donation, then harvest
def test_withdraw_after_donation_6(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    is_slippery,
    no_profit,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    prev_params = vault.strategies(strategy)

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 2
    token.transfer(strategy, donation, {"from": whale})

    # have our whale withdraws more than his donation, ensuring we pull from strategy
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)
    vault.withdraw(donation / 2, {"from": whale})

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    chain.sleep(1)
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    strategy.harvest({"from": gov})
    new_params = vault.strategies(strategy)

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # specifically check that our gain is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery and no_profit:
        assert math.isclose(profit, donation, abs_tol=10) or profit >= donation
    else:
        assert profit >= donation
        assert profit >= 0

    # check that we didn't add any more loss, or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery:
        assert math.isclose(
            new_params["totalLoss"], prev_params["totalLoss"], abs_tol=10
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]

    # assert that our vault total assets, multiplied by our debtRatio, is about equal to our estimated total assets plus credit available (within 1 token)
    # we multiply this by the debtRatio of our strategy out of 10_000 total
    # we sleep 10 hours above specifically for this check
    assert math.isclose(
        vault.totalAssets() * new_params["debtRatio"] / 10_000,
        strategy.estimatedTotalAssets() + vault.creditAvailable(strategy),
        abs_tol=1e18,
    )


# lower debtRatio to 0, donate, withdraw more than the donation, then harvest
def test_withdraw_after_donation_7(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    is_slippery,
    no_profit,
    vault_address,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    prev_params = vault.strategies(strategy)
    prev_assets = vault.totalAssets()

    starting_total_vault_debt = vault.totalDebt()
    starting_strategy_debt = vault.strategies(strategy)["totalDebt"]
    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == 0

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 2
    token.transfer(strategy, donation, {"from": whale})

    # have our whale withdraws more than his donation, ensuring we pull from strategy
    withdrawal = donation + amount / 4

    # convert since our PPS isn't 1 (live vault!)
    withdrawal_in_shares = withdrawal * 1e18 / vault.pricePerShare()
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)
    vault.withdraw(withdrawal_in_shares, {"from": whale})

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # We harvest twice to take profits and then to send the funds to our strategy. This is for our last check below.
    chain.sleep(1)

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    strategy.harvest({"from": gov})

    # check everywhere to make sure we emptied out the strategy
    assert strategy.estimatedTotalAssets() == 0
    assert token.balanceOf(strategy) == 0
    current_assets = vault.totalAssets()

    # assert that our total assets have gone up or stayed the same when accounting for the donation and withdrawal, or that we're close if we have no yield and a funky token
    if is_slippery and no_profit:
        assert (
            math.isclose(
                donation - withdrawal + prev_assets, current_assets, abs_tol=10
            )
            or current_assets >= donation - withdrawal + prev_assets
        )
    else:
        assert current_assets >= donation - withdrawal + prev_assets

    new_params = vault.strategies(strategy)

    # assert that our strategy has no debt
    assert new_params["totalDebt"] == 0
    if vault_address == ZERO_ADDRESS:
        assert vault.totalDebt() == 0
    else:
        assert starting_total_vault_debt - starting_strategy_debt <= vault.totalDebt()

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # specifically check that our gain is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery and no_profit:
        assert math.isclose(profit, donation, abs_tol=10) or profit >= donation
    else:
        assert profit >= donation
        assert profit >= 0

    # check that we didn't add any more loss, or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery:
        assert math.isclose(
            new_params["totalLoss"], prev_params["totalLoss"], abs_tol=10
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]


# lower debtRatio to 0, donate, withdraw less than the donation, then harvest
def test_withdraw_after_donation_8(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    is_slippery,
    no_profit,
    vault_address,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})
    chain.sleep(1)
    strategy.harvest({"from": gov})
    chain.sleep(1)

    prev_params = vault.strategies(strategy)
    prev_assets = vault.totalAssets()

    starting_total_vault_debt = vault.totalDebt()
    starting_strategy_debt = vault.strategies(strategy)["totalDebt"]
    currentDebt = vault.strategies(strategy)["debtRatio"]
    vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
    assert vault.strategies(strategy)["debtRatio"] == 0

    # our whale donates dust to the vault, what a nice person!
    donation = amount / 2
    token.transfer(strategy, donation, {"from": whale})

    # have our whale withdraws less than his donation
    withdrawal = donation / 2

    # convert since our PPS isn't 1 (live vault!)
    withdrawal_in_shares = withdrawal * 1e18 / vault.pricePerShare()
    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked
        chain.sleep(86400 * 7)
        chain.mine(1)
    vault.withdraw(withdrawal_in_shares, {"from": whale})

    # simulate some earnings
    chain.sleep(sleep_time)
    chain.mine(1)

    # We harvest twice to take profits and then to send the funds to our strategy. This is for our last check below.
    chain.sleep(1)

    # turn off health check since we just took big profit
    strategy.setDoHealthCheck(False, {"from": gov})
    token.transfer(strategy, profit_amount, {"from": profit_whale})
    strategy.harvest({"from": gov})

    # check everywhere to make sure we emptied out the strategy
    assert strategy.estimatedTotalAssets() == 0
    assert token.balanceOf(strategy) == 0
    current_assets = vault.totalAssets()

    # assert that our total assets have gone up or stayed the same when accounting for the donation and withdrawal, or that we're close if we have no yield and a funky token
    if is_slippery and no_profit:
        assert (
            math.isclose(
                donation - withdrawal + prev_assets, current_assets, abs_tol=10
            )
            or current_assets >= donation - withdrawal + prev_assets
        )
    else:
        assert current_assets >= donation - withdrawal + prev_assets

    new_params = vault.strategies(strategy)

    # assert that our strategy has no debt
    assert new_params["totalDebt"] == 0
    if vault_address == ZERO_ADDRESS:
        assert vault.totalDebt() == 0
    else:
        assert starting_total_vault_debt - starting_strategy_debt <= vault.totalDebt()

    # sleep 10 hours to allow share price to normalize
    chain.sleep(60 * 60 * 10)
    chain.mine(1)

    profit = new_params["totalGain"] - prev_params["totalGain"]

    # specifically check that our gain is greater than our donation or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery and no_profit:
        assert math.isclose(profit, donation, abs_tol=10) or profit >= donation
    else:
        assert profit >= donation
        assert profit >= 0

    # check that we didn't add any more loss, or at least no more than 10 wei if we get slippage on deposit/withdrawal
    if is_slippery:
        assert math.isclose(
            new_params["totalLoss"], prev_params["totalLoss"], abs_tol=10
        )
    else:
        assert new_params["totalLoss"] == prev_params["totalLoss"]
