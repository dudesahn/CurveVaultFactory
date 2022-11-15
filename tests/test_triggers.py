import brownie
from brownie import Contract
from brownie import config
import math

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
    gasOracle,
    strategist_ms,
    is_slippery,
    no_profit,
    sleep_time,
    profit_amount,
    profit_whale,
    which_strategy,
):
    # frax strategy gets stuck on these views, so we call them instead
    if which_strategy == 2:
        # inactive strategy (0 DR and 0 assets) shouldn't be touched by keepers
        gasOracle.setMaxAcceptableBaseFee(10000 * 1e9, {"from": strategist_ms})
        currentDebtRatio = vault.strategies(strategy)["debtRatio"]
        vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
        strategy.harvest({"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        vault.updateStrategyDebtRatio(strategy, currentDebtRatio, {"from": gov})

        ## deposit to the vault after approving
        startingWhale = token.balanceOf(whale)
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

        # harvest the credit
        chain.sleep(1)
        strategy.harvest({"from": gov})
        chain.sleep(1)
        chain.mine(1)

        # should trigger false, nothing is ready yet
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False

        # simulate earnings
        chain.sleep(sleep_time)
        chain.mine(1)

        # set our max delay to 1 day so we trigger true, then set it back to 21 days
        strategy.setMaxReportDelay(sleep_time - 1)
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be True.", tx)
        assert tx == True
        strategy.setMaxReportDelay(86400 * 21)

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

        # harvest, wait
        chain.sleep(1)
        token.transfer(strategy, profit_amount, {"from": profit_whale})
        tx = strategy.harvest({"from": gov})
        print("Harvest info:", tx.events["Harvested"])
        chain.sleep(sleep_time)
        chain.mine(1)

        # harvest should trigger false because of oracle
        gasOracle.setManualBaseFeeBool(False, {"from": gov})
        tx = strategy.harvestTrigger.call(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        gasOracle.setManualBaseFeeBool(True, {"from": gov})
    else:
        # inactive strategy (0 DR and 0 assets) shouldn't be touched by keepers
        gasOracle.setMaxAcceptableBaseFee(10000 * 1e9, {"from": strategist_ms})
        currentDebtRatio = vault.strategies(strategy)["debtRatio"]
        vault.updateStrategyDebtRatio(strategy, 0, {"from": gov})
        strategy.harvest({"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        vault.updateStrategyDebtRatio(strategy, currentDebtRatio, {"from": gov})

        ## deposit to the vault after approving
        startingWhale = token.balanceOf(whale)
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

        # harvest the credit
        chain.sleep(1)
        strategy.harvest({"from": gov})
        chain.sleep(1)
        chain.mine(1)

        # should trigger false, nothing is ready yet
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False

        # simulate earnings
        chain.sleep(sleep_time)
        chain.mine(1)

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
                # update our minProfit so our harvest triggers true
                strategy.setHarvestTriggerParams(1, 1000000e6, False, {"from": gov})
                tx = strategy.harvestTrigger(0, {"from": gov})
                print("\nShould we harvest? Should be true.", tx)
                assert tx == True

                # update our maxProfit so harvest triggers true
                strategy.setHarvestTriggerParams(1000000e6, 1, False, {"from": gov})
                tx = strategy.harvestTrigger(0, {"from": gov})
                print("\nShould we harvest? Should be true.", tx)
                assert tx == True

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
        chain.sleep(1)
        token.transfer(strategy, profit_amount, {"from": profit_whale})
        tx = strategy.harvest({"from": gov})
        print("Harvest info:", tx.events["Harvested"])
        chain.sleep(sleep_time)
        chain.mine(1)

        # harvest should trigger false because of oracle
        gasOracle.setManualBaseFeeBool(False, {"from": gov})
        tx = strategy.harvestTrigger(0, {"from": gov})
        print("\nShould we harvest? Should be false.", tx)
        assert tx == False
        gasOracle.setManualBaseFeeBool(True, {"from": gov})

    if which_strategy == 2:
        # wait another week so our frax LPs are unlocked, need to do this when reducing debt or withdrawing
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
