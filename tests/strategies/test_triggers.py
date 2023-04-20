import brownie
from brownie import chain, Contract, ZERO_ADDRESS, accounts
import pytest
from utils import harvest_strategy, check_status

# test our harvest triggers
def test_triggers(
    gov,
    token,
    vault,
    strategist,
    whale,
    strategy,
    chain,
    amount,
    sleep_time,
    is_slippery,
    no_profit,
    profit_whale,
    profit_amount,
    target,
    base_fee_oracle,
    use_yswaps,
    which_strategy,
):
    # frax strategy gets stuck on these views, so we call them instead
    if which_strategy == 2:
        # inactive strategy (0 DR and 0 assets) shouldn't be touched by keepers
        currentDebtRatio = vault.strategies(strategy)["debtRatio"]
        vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        vault.updateStrategyDebtRatio(strategy, currentDebtRatio, {"from": gov})

        ## deposit to the vault after approving, no harvest yet
        starting_whale = token.balanceOf(whale)
        token.approve(vault, 2**256 - 1, {"from": whale})
        vault.deposit(amount, {"from": whale})
        newWhale = token.balanceOf(whale)
        starting_assets = vault.totalAssets()

        # update our min credit so harvest triggers true
        strategy.setCreditThreshold(1, {"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True
        strategy.setCreditThreshold(1e24, {"from": gov})

        # test our manual harvest trigger
        strategy.setForceHarvestTriggerOnce(True, {"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True

        # harvest the credit
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        # should trigger false, nothing is ready yet, just harvested
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False

        # simulate earnings
        chain.sleep(sleep_time)

        ################# GENERATE CLAIMABLE PROFIT HERE AS NEEDED #################
        # we simulate minting LUSD fees from liquity's borrower operations to the staking contract so we have claimable yield
        # for curve vaults, we shouldn't have to worry about a lack of claimable profit, should auto-generate

        # check that we have claimable profit, need this for min and max profit checks below
        claimable_profit = strategy.claimableProfitInUsdc()
        assert claimable_profit > 0

        if not (is_slippery and no_profit):
            # update our minProfit so our harvest triggers true
            strategy.setHarvestTriggerParams(1, 1000000e6, {"from": gov})
            tx = strategy.harvestTrigger.call(0, {"from": gov})
            print("\nShould we harvest? Should be true.", tx)
            assert tx == True

            # update our maxProfit so harvest triggers true
            strategy.setHarvestTriggerParams(1000000e6, 1, {"from": gov})
            tx = strategy.harvestTrigger.call(0, {"from": gov})
            print("\nShould we harvest? Should be true.", tx)
            assert tx == True
            strategy.setHarvestTriggerParams(90000e6, 150000e6, {"from": gov})

        # set our max delay to 1 day so we trigger true, then set it back to 21 days
        strategy.setMaxReportDelay(sleep_time - 1)
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be True.", tx)
        assert tx == True
        strategy.setMaxReportDelay(86400 * 21)

        # harvest, wait
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )
        print("Profit:", profit, "Loss:", loss)
        chain.sleep(sleep_time)

        # harvest should trigger false because of oracle
        base_fee_oracle.setManualBaseFeeBool(False, {"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        base_fee_oracle.setManualBaseFeeBool(True, {"from": gov})

        # harvest again to get the last of our profit with ySwaps
        if use_yswaps:
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
            print("\nAfter yswaps extra harvest")
            strategy_params = check_status(strategy, vault)

            # make sure we recorded our gain properly
            if not no_profit:
                assert profit > 0

        # simulate seven days of waiting for share price to bump back up and LPs to unlock
        chain.sleep(86400 * 7)
        chain.mine(1)
    else:
        # inactive strategy (0 DR and 0 assets) shouldn't be touched by keepers
        currentDebtRatio = vault.strategies(strategy)["debtRatio"]
        vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        vault.updateStrategyDebtRatio(strategy, currentDebtRatio, {"from": gov})

        ## deposit to the vault after approving, no harvest yet
        starting_whale = token.balanceOf(whale)
        token.approve(vault, 2**256 - 1, {"from": whale})
        vault.deposit(amount, {"from": whale})
        newWhale = token.balanceOf(whale)
        starting_assets = vault.totalAssets()

        # update our min credit so harvest triggers true
        strategy.setCreditThreshold(1, {"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True
        strategy.setCreditThreshold(1e24, {"from": gov})

        # test our manual harvest trigger
        strategy.setForceHarvestTriggerOnce(True, {"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be true.", tx)
        assert tx == True

        # harvest the credit
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )

        # should trigger false, nothing is ready yet, just harvested
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False

        # simulate earnings
        chain.sleep(sleep_time)

        ################# GENERATE CLAIMABLE PROFIT HERE AS NEEDED #################
        # we simulate minting LUSD fees from liquity's borrower operations to the staking contract so we have claimable yield
        # for curve vaults, we shouldn't have to worry about a lack of claimable profit, should auto-generate

        # set our max delay to 1 day so we trigger true, then set it back to 21 days
        strategy.setMaxReportDelay(sleep_time - 1)
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be True.", tx)
        assert tx == True
        strategy.setMaxReportDelay(86400 * 21)

        # only convex does this mess with earmarking
        if which_strategy == 0:
            # turn on our check for earmark. Shouldn't block anything. Turn off earmark check after.
            strategy.setHarvestTriggerParams(90000e6, 150000e6, True, {"from": gov})
            tx = strategy.harvestTrigger(0, {"from": gov})
            if strategy.needsEarmarkReward():
                print("\nShould we harvest? Should be no since we need to earmark.", tx)
                assert tx == False
            else:
                print(
                    "\nShould we harvest? Should be false since it was already false and we don't need to earmark.",
                    tx,
                )
                assert tx == False
            strategy.setHarvestTriggerParams(90000e6, 150000e6, False, {"from": gov})

            if not (is_slippery and no_profit):
                # check that we have claimable profit, need this for min and max profit checks below
                claimable_profit = strategy.claimableProfitInUsdc()
                assert claimable_profit > 0

                # update our minProfit so our harvest triggers true
                strategy.setHarvestTriggerParams(
                    1, 1000000e6, strategy.checkEarmark(), {"from": gov}
                )
                tx = strategy.harvestTrigger(0, {"from": gov})
                print("\nShould we harvest? Should be true.", tx)
                assert tx == True

                # update our maxProfit so harvest triggers true
                strategy.setHarvestTriggerParams(
                    1000000e6, 1, strategy.checkEarmark(), {"from": gov}
                )
                tx = strategy.harvestTrigger(0, {"from": gov})
                print("\nShould we harvest? Should be true.", tx)
                assert tx == True
                strategy.setHarvestTriggerParams(
                    90000e6, 150000e6, strategy.checkEarmark(), {"from": gov}
                )

            # earmark should be false now (it's been too long), turn it off after
            chain.sleep(86400 * 21)
            strategy.setHarvestTriggerParams(90000e6, 150000e6, True, {"from": gov})
            assert strategy.needsEarmarkReward() == True
            tx = strategy.harvestTrigger(0, {"from": gov})
            print(
                "\nShould we harvest? Should be false, even though it was true before because of earmark.",
                tx,
            )
            assert tx == False
            strategy.setHarvestTriggerParams(90000e6, 150000e6, False, {"from": gov})
        else:  # curve uses minDelay as well
            strategy.setMinReportDelay(sleep_time - 1)
            tx = strategy.harvestTrigger(0, {"from": gov})
            print("\nShould we harvest? Should be True.", tx)
            assert tx == True

        # harvest, wait
        (profit, loss) = harvest_strategy(
            use_yswaps,
            strategy,
            token,
            gov,
            profit_whale,
            profit_amount,
            target,
        )
        print("Profit:", profit, "Loss:", loss)
        chain.sleep(sleep_time)

        # harvest should trigger false because of oracle
        base_fee_oracle.setManualBaseFeeBool(False, {"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        base_fee_oracle.setManualBaseFeeBool(True, {"from": gov})

        # harvest again to get the last of our profit with ySwaps
        if use_yswaps:
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
            print("\nAfter yswaps extra harvest")
            strategy_params = check_status(strategy, vault)

            # make sure we recorded our gain properly
            if not no_profit:
                assert profit > 0

        # simulate five days of waiting for share price to bump back up
        chain.sleep(86400 * 5)
        chain.mine(1)

    # withdraw and confirm we made money, or at least that we have about the same
    vault.withdraw({"from": whale})
    if no_profit:
        assert (
            pytest.approx(token.balanceOf(whale), rel=RELATIVE_APPROX) == starting_whale
        )
    else:
        assert token.balanceOf(whale) > starting_whale
