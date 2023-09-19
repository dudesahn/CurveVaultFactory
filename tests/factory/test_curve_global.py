import brownie
from brownie import Contract, ZERO_ADDRESS, interface, chain, accounts
import math
from utils import harvest_strategy, check_status

# note that because ganache crashes with the try-catch when checking for frax pids, we need to do this test and the next with tenderly
# for the vault deployment to not revert. additionally, best to do the first two individually.
# also important to note that these tests don't care about which_strategy, but good to test out PIDs with and without frax strategies
def test_vault_deployment(
    StrategyConvexFactoryClonable,
    StrategyCurveBoostedFactoryClonable,
    StrategyConvexFraxFactoryClonable,
    strategist,
    curve_global,
    gov,
    guardian,
    token,
    health_check,
    pid,
    base_fee_oracle,
    new_registry,
    gauge,
    new_proxy,
    voter,
    whale,
    tests_using_tenderly,
    keeper_wrapper,
    amount,
    booster,
    legacy_gauge,
    use_yswaps,
    profit_whale,
    profit_amount,
    target,
    convex_template,
    frax_template,
    curve_template,
    frax_booster,
):
    ############# skip all of this since factory is already live

    # once our factory is deployed, setup the factory from gov
    # registry_owner = accounts.at(new_registry.owner(), force=True)
    # new_registry.setApprovedVaultsOwner(curve_global, True, {"from": registry_owner})
    # new_registry.setVaultEndorsers(curve_global, True, {"from": registry_owner})

    # update the strategy on our voter
    # voter.setStrategy(new_proxy.address, {"from": gov})

    # set our factory address on the strategy proxy
    # new_proxy.setFactory(curve_global.address, {"from": gov})

    #############

    # this will crash if we're not using tenderly
    if not tests_using_tenderly:
        return

    # update our frax booster to v2
    if curve_global.fraxBooster() != frax_booster.address:
        curve_global.setFraxBooster(frax_booster, {"from": gov})
        print("Updated Frax Booster")

    print("New proxy updated, factory added to proxy")

    # make sure our curve global can own vaults and endorse them
    assert new_registry.approvedVaultsOwner(curve_global)
    assert new_registry.vaultEndorsers(curve_global)
    assert curve_global.registry() == new_registry.address
    print("Our factory can endorse vaults")

    # attach our new strategy templates
    curve_global.setConvexStratImplementation(convex_template, {"from": gov})
    curve_global.setConvexFraxStratImplementation(frax_template, {"from": gov})
    curve_global.setCurveStratImplementation(curve_template, {"from": gov})

    _pid = curve_global.getPid(gauge)
    assert _pid == pid
    print("\nOur pid workup works, pid:", pid)

    # check if this is a frax pool
    frax_pid = curve_global.getFraxInfo(_pid)
    if frax_pid[0]:
        print("We can pull Frax pids too:", frax_pid[1])
    else:
        print("This isn't a Frax pool")

    print("Let's deploy this vault")
    print("Factory address: ", curve_global)
    print("Gauge: ", gauge)

    # check if our current gauge has a strategy for it, but mostly just do this to update our proxy
    print(
        "Here is our strategy for the gauge (likely 0x000):",
        new_proxy.strategies(gauge),
    )

    # make sure we can create this vault permissionlessly
    assert curve_global.latestStandardVaultFromGauge(legacy_gauge) != ZERO_ADDRESS
    assert not curve_global.canCreateVaultPermissionlessly(legacy_gauge)
    assert curve_global.canCreateVaultPermissionlessly(
        gauge
    )  # obviously if we use a gauge with an existing legacy vault this will be false

    # before we deploy, check our gauge. we shouldn't have added this to our proxy yet
    answer = curve_global.doesStrategyProxyHaveGauge(gauge)
    print("Is this gauge already paired with a strategy on our proxy?", answer)
    assert not answer

    # tenderly RPC can't do brownie.reverts
    if not tests_using_tenderly:
        with brownie.reverts():
            curve_global.createNewVaultsAndStrategies(health_check, {"from": whale})
        print("Can't create a vault for something that's not actually a gauge")

    # turn on keeps
    curve_global.setKeepCRV(69, curve_global.curveVoter(), {"from": gov})
    curve_global.setKeepCVX(69, gov, {"from": gov})
    curve_global.setKeepFXS(69, gov, {"from": gov})
    print(
        "Set our global keeps, don't mess with curve voter or we will revert on deploy"
    )

    tx = curve_global.createNewVaultsAndStrategies(gauge, {"from": whale})
    assert curve_global.latestStandardVaultFromGauge(gauge) != ZERO_ADDRESS

    vault_address = tx.events["NewAutomatedVault"]["vault"]
    vault = Contract(vault_address)
    print("Vault name:", vault.name())

    print("Vault endorsed:", vault_address)
    info = tx.events["NewAutomatedVault"]

    print("Here's our new vault created event:", info, "\n")

    # print our addresses
    cvx_strat = tx.events["NewAutomatedVault"]["convexStrategy"]
    convex_strategy = StrategyConvexFactoryClonable.at(cvx_strat)

    # check that everything is setup properly for our vault
    assert vault.governance() == curve_global.address
    assert vault.management() == curve_global.management()
    assert vault.guardian() == curve_global.guardian()
    assert vault.guardian() == curve_global.guardian()
    assert vault.depositLimit() == curve_global.depositLimit()
    assert vault.rewards() == curve_global.treasury()
    assert vault.managementFee() == curve_global.managementFee()
    assert vault.performanceFee() == curve_global.performanceFee()

    # check that things are good on our strategies
    # convex
    assert vault.withdrawalQueue(0) == cvx_strat
    assert vault.strategies(cvx_strat)["performanceFee"] == 0
    assert convex_strategy.creditThreshold() == 5e22  # 50k
    assert convex_strategy.healthCheck() == curve_global.healthCheck()
    assert (
        convex_strategy.harvestProfitMaxInUsdc()
        == curve_global.harvestProfitMaxInUsdc()
    )
    assert (
        convex_strategy.harvestProfitMinInUsdc()
        == curve_global.harvestProfitMinInUsdc()
    )
    assert convex_strategy.healthCheck() == curve_global.healthCheck()
    assert convex_strategy.localKeepCRV() == curve_global.keepCRV()
    assert convex_strategy.localKeepCVX() == curve_global.keepCVX()
    assert convex_strategy.curveVoter() == curve_global.curveVoter()
    assert convex_strategy.convexVoter() == curve_global.convexVoter()
    assert convex_strategy.rewards() == curve_global.treasury()
    assert convex_strategy.strategist() == curve_global.management()
    assert convex_strategy.keeper() == curve_global.keeper()

    curve_strat = tx.events["NewAutomatedVault"]["curveStrategy"]
    if curve_strat != ZERO_ADDRESS:
        curve_strategy = StrategyCurveBoostedFactoryClonable.at(curve_strat)
        # curve
        assert vault.withdrawalQueue(1) == curve_strat
        assert vault.strategies(curve_strat)["performanceFee"] == 0
        assert curve_strategy.creditThreshold() == 5e22  # 50k
        assert curve_strategy.healthCheck() == curve_global.healthCheck()
        assert curve_strategy.localKeepCRV() == curve_global.keepCRV()
        assert curve_strategy.curveVoter() == curve_global.curveVoter()
        assert curve_strategy.rewards() == curve_global.treasury()
        assert curve_strategy.strategist() == curve_global.management()
        assert curve_strategy.keeper() == curve_global.keeper()

    frax_strat = tx.events["NewAutomatedVault"]["convexFraxStrategy"]
    if frax_strat != ZERO_ADDRESS:
        frax_strategy = StrategyConvexFraxFactoryClonable.at(frax_strat)
        # frax
        assert vault.withdrawalQueue(2) == frax_strat
        assert vault.strategies(frax_strat)["performanceFee"] == 0
        print("All three strategies attached in order")
        assert frax_strategy.creditThreshold() == 5e22  # 50k
        assert frax_strategy.healthCheck() == curve_global.healthCheck()
        assert (
            frax_strategy.harvestProfitMaxInUsdc()
            == curve_global.harvestProfitMaxInUsdc()
        )
        assert (
            frax_strategy.harvestProfitMinInUsdc()
            == curve_global.harvestProfitMinInUsdc()
        )
        assert frax_strategy.healthCheck() == curve_global.healthCheck()
        assert frax_strategy.localKeepCRV() == curve_global.keepCRV()
        assert frax_strategy.localKeepCVX() == curve_global.keepCVX()
        assert frax_strategy.localKeepFXS() == curve_global.keepFXS()
        assert frax_strategy.curveVoter() == curve_global.curveVoter()
        assert frax_strategy.convexVoter() == curve_global.convexVoter()
        assert frax_strategy.fraxVoter() == curve_global.fraxVoter()
        assert frax_strategy.rewards() == curve_global.treasury()
        assert frax_strategy.strategist() == curve_global.management()
        assert frax_strategy.keeper() == curve_global.keeper()

    # daddy needs to accept gov on all new vaults
    vault.acceptGovernance({"from": gov})
    assert vault.governance() == gov.address

    # check that anyone can harvest a strategy thanks to our keeper wrapper
    print(
        "Check out our keeper wrapper, make sure it works as intended for all strategies"
    )
    rando = accounts[5]
    assert convex_strategy.keeper() == keeper_wrapper
    if curve_strat != ZERO_ADDRESS:
        assert curve_strategy.keeper() == keeper_wrapper
    if frax_strat != ZERO_ADDRESS:
        assert frax_strategy.keeper() == keeper_wrapper
        vault.updateStrategyDebtRatio(frax_strategy, 0, {"from": gov})
        vault.updateStrategyDebtRatio(curve_strategy, 0, {"from": gov})
        vault.updateStrategyDebtRatio(convex_strategy, 0, {"from": gov})
        vault.updateStrategyDebtRatio(frax_strategy, 3000, {"from": gov})
        vault.updateStrategyDebtRatio(curve_strategy, 3000, {"from": gov})
        vault.updateStrategyDebtRatio(convex_strategy, 4000, {"from": gov})
        # for testing, let's deposit anything above 1e18 since we might be doing frxETH
        frax_strategy.setDepositParams(1e18, 5_000_000e18, True, {"from": gov})
    else:
        vault.updateStrategyDebtRatio(curve_strategy, 0, {"from": gov})
        vault.updateStrategyDebtRatio(convex_strategy, 0, {"from": gov})
        vault.updateStrategyDebtRatio(curve_strategy, 5000, {"from": gov})
        vault.updateStrategyDebtRatio(convex_strategy, 5000, {"from": gov})

    ## deposit to the vault after approving
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})

    # harvest, pass 9 to gov so we know this is a permissionless harvest
    keeper_wrapper.harvest(convex_strategy, {"from": rando})
    (profit, loss) = harvest_strategy(
        use_yswaps,
        convex_strategy,
        token,
        9,
        profit_whale,
        profit_amount,
        0,
    )

    if curve_strat != ZERO_ADDRESS:
        keeper_wrapper.harvest(curve_strategy, {"from": rando})
        (profit, loss) = harvest_strategy(
            use_yswaps,
            curve_strategy,
            token,
            9,
            profit_whale,
            profit_amount,
            1,
        )
    if frax_strat != ZERO_ADDRESS:
        keeper_wrapper.harvest(frax_strategy, {"from": rando})
        (profit, loss) = harvest_strategy(
            use_yswaps,
            frax_strategy,
            token,
            9,
            profit_whale,
            profit_amount,
            2,
        )

    # assert that money deposited to convex and curve
    assert convex_strategy.stakedBalance() > 0
    assert curve_strategy.stakedBalance() > 0
    if frax_strat != ZERO_ADDRESS:
        assert frax_strategy.stakedBalance() > 0

    # wait a week for our funds to unlock
    chain.sleep(86400 * 7)
    chain.mine(1)

    if frax_strat != ZERO_ADDRESS:
        print("Check that anyone can harvest again to remove all funds")
        vault.updateStrategyDebtRatio(frax_strategy, 0, {"from": gov})
        if not tests_using_tenderly:
            with brownie.reverts():
                vault.updateStrategyDebtRatio(frax_strategy, 10, {"from": whale})
        print("But only gov/management can adjust debt ratios")

        keeper_wrapper.harvest(frax_strategy, {"from": rando})
        (profit, loss) = harvest_strategy(
            use_yswaps,
            frax_strategy,
            token,
            9,
            profit_whale,
            profit_amount,
            2,
        )

        # harvest again so the strategy reports the profit
        if use_yswaps:
            print("Using ySwaps for harvests")
            (profit, loss) = harvest_strategy(
                use_yswaps,
                frax_strategy,
                token,
                gov,
                profit_whale,
                profit_amount,
                2,
            )

        assert frax_strategy.estimatedTotalAssets() == 0
    else:
        print("Check that anyone can harvest again to remove all funds")
        vault.updateStrategyDebtRatio(convex_strategy, 0, {"from": gov})
        if not tests_using_tenderly:
            with brownie.reverts():
                vault.updateStrategyDebtRatio(convex_strategy, 10, {"from": whale})
        print("But only gov/management can adjust debt ratios")

        keeper_wrapper.harvest(convex_strategy, {"from": rando})
        (profit, loss) = harvest_strategy(
            use_yswaps,
            convex_strategy,
            token,
            9,
            profit_whale,
            profit_amount,
            0,
        )

        # harvest again so the strategy reports the profit
        if use_yswaps:
            print("Using ySwaps for harvests")
            (profit, loss) = harvest_strategy(
                use_yswaps,
                convex_strategy,
                token,
                gov,
                profit_whale,
                profit_amount,
                0,
            )
        assert convex_strategy.estimatedTotalAssets() == 0

    assert not curve_global.canCreateVaultPermissionlessly(legacy_gauge)
    assert curve_global.latestStandardVaultFromGauge(legacy_gauge) != ZERO_ADDRESS
    print("Can't create vault permissionlessly if we had a legacy version")

    if not tests_using_tenderly:
        # can't deploy another of the same vault permissionlessly
        with brownie.reverts():
            tx = curve_global.createNewVaultsAndStrategies(gauge, {"from": whale})

        # we can't do our previously existing vault either
        with brownie.reverts():
            tx = curve_global.createNewVaultsAndStrategies(
                legacy_gauge, {"from": whale}
            )


def test_permissioned_vault(
    StrategyConvexFactoryClonable,
    StrategyCurveBoostedFactoryClonable,
    StrategyConvexFraxFactoryClonable,
    strategist,
    curve_global,
    gov,
    guardian,
    token,
    health_check,
    pid,
    base_fee_oracle,
    new_registry,
    gauge,
    new_proxy,
    voter,
    whale,
    tests_using_tenderly,
    legacy_gauge,
    convex_template,
    frax_template,
    curve_template,
    frax_booster,
):
    ############# skip all of this since factory is already live

    # deploying curve global with frax strategies doesn't work unless with tenderly;
    # ganache crashes because of the try-catch in the fraxPid function
    # however, I usually do hacky coverage testing (commenting out section in curveGlobal)

    # once our factory is deployed, setup the factory from gov
    # registry_owner = accounts.at(new_registry.owner(), force=True)
    # new_registry.setApprovedVaultsOwner(curve_global, True, {"from": registry_owner})
    # new_registry.setVaultEndorsers(curve_global, True, {"from": registry_owner})

    # update the strategy on our voter
    # voter.setStrategy(new_proxy.address, {"from": gov})

    # set our factory address on the strategy proxy
    # new_proxy.setFactory(curve_global.address, {"from": gov})

    #############

    # this will crash if we're not using tenderly
    if not tests_using_tenderly:
        return

    # update our frax booster to v2
    if curve_global.fraxBooster() != frax_booster.address:
        curve_global.setFraxBooster(frax_booster, {"from": gov})
        print("Updated Frax Booster")

    print("New proxy updated, factory added to proxy")

    # make sure our curve global can own vaults and endorse them
    assert new_registry.approvedVaultsOwner(curve_global)
    assert new_registry.vaultEndorsers(curve_global)
    assert curve_global.registry() == new_registry.address
    print("Our factory can endorse vaults")

    _pid = curve_global.getPid(gauge)
    assert _pid == pid
    print("\nOur pid workup works, pid:", pid)

    # check if this is a frax pool
    frax_pid = curve_global.getFraxInfo(_pid)
    if frax_pid[0]:
        print("We can pull Frax pids too:", frax_pid[1])
    else:
        print("This isn't a Frax pool")

    # attach our new strategy templates
    curve_global.setConvexStratImplementation(convex_template, {"from": gov})
    curve_global.setConvexFraxStratImplementation(frax_template, {"from": gov})
    curve_global.setCurveStratImplementation(curve_template, {"from": gov})

    print("New proxy updated, factory added to proxy")
    print("Let's deploy this vault")
    print("Factory address: ", curve_global)
    print("Gauge: ", gauge)

    # check if our current gauge has a strategy for it, but mostly just do this to update our proxy
    print(
        "Here is our strategy for the gauge (likely 0x000):",
        new_proxy.strategies(gauge),
    )

    # check if we can create this vault permissionlessly
    print(
        "Can we create this vault permissionlessly?",
        curve_global.canCreateVaultPermissionlessly(gauge),
    )

    # turn on keeps
    curve_global.setKeepCRV(69, curve_global.curveVoter(), {"from": gov})
    curve_global.setKeepCVX(69, gov, {"from": gov})
    curve_global.setKeepFXS(69, gov, {"from": gov})
    print(
        "Set our global keeps, don't mess with curve voter or we will revert on deploy"
    )

    # make sure not just anyone can create a permissioned vault
    if not tests_using_tenderly:
        with brownie.reverts():
            curve_global.createNewVaultsAndStrategiesPermissioned(
                gauge, "poop", "poop", {"from": whale}
            )

    tx = curve_global.createNewVaultsAndStrategiesPermissioned(
        gauge, "stuff", "stuff", {"from": gov}
    )
    vault_address = tx.events["NewAutomatedVault"]["vault"]
    vault = Contract(vault_address)
    print("Vault name:", vault.name())

    print("Vault endorsed:", vault_address)
    info = tx.events["NewAutomatedVault"]

    # check that everything is setup properly for our vault
    assert vault.governance() == curve_global.address
    assert vault.management() == curve_global.management()
    assert vault.guardian() == curve_global.guardian()
    assert vault.guardian() == curve_global.guardian()
    assert vault.depositLimit() == curve_global.depositLimit()
    assert vault.rewards() == curve_global.treasury()
    assert vault.managementFee() == curve_global.managementFee()
    assert vault.performanceFee() == curve_global.performanceFee()
    print("Asserts good for our vault")

    print("Here's our new vault created event:", info, "\n")

    # convex
    cvx_strat = tx.events["NewAutomatedVault"]["convexStrategy"]
    convex_strategy = StrategyConvexFactoryClonable.at(cvx_strat)
    print("Convex strategy:", cvx_strat)

    assert vault.withdrawalQueue(0) == cvx_strat
    assert vault.strategies(cvx_strat)["performanceFee"] == 0
    assert convex_strategy.creditThreshold() == 5e22  # 50k
    assert convex_strategy.healthCheck() == curve_global.healthCheck()
    assert (
        convex_strategy.harvestProfitMaxInUsdc()
        == curve_global.harvestProfitMaxInUsdc()
    )
    assert (
        convex_strategy.harvestProfitMinInUsdc()
        == curve_global.harvestProfitMinInUsdc()
    )
    assert convex_strategy.healthCheck() == curve_global.healthCheck()
    assert convex_strategy.localKeepCRV() == curve_global.keepCRV()
    assert convex_strategy.localKeepCVX() == curve_global.keepCVX()
    assert convex_strategy.curveVoter() == curve_global.curveVoter()
    assert convex_strategy.convexVoter() == curve_global.convexVoter()
    assert convex_strategy.rewards() == curve_global.treasury()
    assert convex_strategy.strategist() == curve_global.management()
    assert convex_strategy.keeper() == curve_global.keeper()
    print("Asserts good for our convex strategy")

    # curve
    curve_strat = tx.events["NewAutomatedVault"]["curveStrategy"]
    curve_strategy = StrategyCurveBoostedFactoryClonable.at(curve_strat)
    print("Curve strategy:", curve_strat)

    # curve
    assert vault.withdrawalQueue(1) == curve_strat
    assert vault.strategies(curve_strat)["performanceFee"] == 0
    assert curve_strategy.creditThreshold() == 5e22  # 50k
    assert curve_strategy.healthCheck() == curve_global.healthCheck()
    assert curve_strategy.localKeepCRV() == curve_global.keepCRV()
    assert curve_strategy.curveVoter() == curve_global.curveVoter()
    assert curve_strategy.rewards() == curve_global.treasury()
    assert curve_strategy.strategist() == curve_global.management()
    assert curve_strategy.keeper() == curve_global.keeper()
    print("Asserts good for our curve strategy")

    # frax
    frax_strat = tx.events["NewAutomatedVault"]["convexFraxStrategy"]
    if frax_strat != ZERO_ADDRESS:
        frax_strategy = StrategyConvexFraxFactoryClonable.at(frax_strat)
        print("Frax strategy:", frax_strat)
        assert vault.withdrawalQueue(2) == frax_strat
        assert vault.strategies(frax_strat)["performanceFee"] == 0
        print("All three strategies attached in order")
        assert frax_strategy.creditThreshold() == 5e22  # 50k
        assert frax_strategy.healthCheck() == curve_global.healthCheck()
        assert (
            frax_strategy.harvestProfitMaxInUsdc()
            == curve_global.harvestProfitMaxInUsdc()
        )
        assert (
            frax_strategy.harvestProfitMinInUsdc()
            == curve_global.harvestProfitMinInUsdc()
        )
        assert frax_strategy.healthCheck() == curve_global.healthCheck()
        assert frax_strategy.localKeepCRV() == curve_global.keepCRV()
        assert frax_strategy.localKeepCVX() == curve_global.keepCVX()
        assert frax_strategy.localKeepFXS() == curve_global.keepFXS()
        assert frax_strategy.curveVoter() == curve_global.curveVoter()
        assert frax_strategy.convexVoter() == curve_global.convexVoter()
        assert frax_strategy.fraxVoter() == curve_global.fraxVoter()
        assert frax_strategy.rewards() == curve_global.treasury()
        assert frax_strategy.strategist() == curve_global.management()
        assert frax_strategy.keeper() == curve_global.keeper()
        print("Asserts good on frax")

    # daddy needs to accept gov on all new vaults
    vault.acceptGovernance({"from": gov})
    assert vault.governance() == gov.address
    print("Gov accepted by daddy")

    # deploy a factory version of a legacy vault
    tx = curve_global.createNewVaultsAndStrategiesPermissioned(
        legacy_gauge,
        "Legacy Vault",
        "yvCurve-Legacy",
        {"from": gov},
    )
    print("New factory vault deployed")

    if not tests_using_tenderly:
        # we can't deploy another frax vault because we already have a strategy on our proxy for that gauge
        with brownie.reverts():
            tx = curve_global.createNewVaultsAndStrategiesPermissioned(
                gauge, "test2", "test2", {"from": gov}
            )


def test_curve_global_setters_and_views(
    gov,
    whale,
    amount,
    curve_global,
    new_registry,
    gauge,
    pid,
    token,
    legacy_gauge,
    voter,
    new_proxy,
    convex_template,
    frax_template,
    curve_template,
    tests_using_tenderly,
):
    ############# skip all of this since factory is already live

    # once our factory is deployed, setup the factory from gov
    # registry_owner = accounts.at(new_registry.owner(), force=True)
    # new_registry.setApprovedVaultsOwner(curve_global, True, {"from": registry_owner})
    # new_registry.setVaultEndorsers(curve_global, True, {"from": registry_owner})

    # update the strategy on our voter
    # voter.setStrategy(new_proxy.address, {"from": gov})

    # set our factory address on the strategy proxy
    # new_proxy.setFactory(curve_global.address, {"from": gov})

    #############

    print("New proxy updated, factory added to proxy")

    # make sure our curve global can own vaults and endorse them
    assert new_registry.approvedVaultsOwner(curve_global)
    assert new_registry.vaultEndorsers(curve_global)
    assert curve_global.registry() == new_registry.address
    print("Our factory can endorse vaults")

    # attach our new strategy templates
    curve_global.setConvexStratImplementation(convex_template, {"from": gov})
    curve_global.setConvexFraxStratImplementation(frax_template, {"from": gov})
    curve_global.setCurveStratImplementation(curve_template, {"from": gov})

    # check our views
    print("Time to check the views")

    # this one causes our coverage tests to crash, so make it call only
    _pid = curve_global.getPid.call(gauge)
    assert _pid == pid
    print("PID is good")

    # trying to pull a PID for an address that doesn't have one should return max uint
    fake_pid = curve_global.getPid.call(gov)
    assert fake_pid == 2**256 - 1
    print("Fake gauge gives max uint")

    # check our deployed vaults
    all_vaults = curve_global.allDeployedVaults()
    print("All vaults:", all_vaults)

    length = curve_global.numVaults()
    print("Number of vaults:", length)

    # check if we can create vaults
    assert not curve_global.canCreateVaultPermissionlessly(legacy_gauge)

    # this one should always be yes (SDT/ETH) as we will almost certainly never make a vault for this
    assert curve_global.canCreateVaultPermissionlessly(
        "0x60355587a8D4aa67c2E64060Ab36e566B9bCC000"
    )

    # update the strategy on our voter
    voter.setStrategy(new_proxy.address, {"from": gov})

    # we already have a legacy vault but it's only convex, should be false
    assert not curve_global.doesStrategyProxyHaveGauge(legacy_gauge)

    # check our latest vault for legacy gauge
    latest = curve_global.latestStandardVaultFromGauge(legacy_gauge)
    print("Latest vault for legacy gauge:", latest)

    # check our setters
    if not tests_using_tenderly:
        with brownie.reverts():
            curve_global.setKeepCVX(69, gov, {"from": whale})
    curve_global.setKeepCVX(0, gov, {"from": gov})
    curve_global.setKeepCVX(69, gov, {"from": gov})
    assert curve_global.keepCVX() == 69
    assert curve_global.convexVoter() == gov.address
    if not tests_using_tenderly:
        with brownie.reverts():
            curve_global.setKeepCVX(69, ZERO_ADDRESS, {"from": gov})
        with brownie.reverts():
            curve_global.setKeepCVX(10_001, gov, {"from": gov})
        with brownie.reverts():
            curve_global.setKeepCRV(69, gov, {"from": whale})

    curve_global.setKeepCRV(0, gov, {"from": gov})
    curve_global.setKeepCRV(69, gov, {"from": gov})
    assert curve_global.keepCRV() == 69
    assert curve_global.curveVoter() == gov.address
    if not tests_using_tenderly:
        with brownie.reverts():
            curve_global.setKeepCRV(69, ZERO_ADDRESS, {"from": gov})
        with brownie.reverts():
            curve_global.setKeepCRV(10_001, gov, {"from": gov})
        with brownie.reverts():
            curve_global.setKeepFXS(69, gov, {"from": whale})

    curve_global.setKeepFXS(0, gov, {"from": gov})
    curve_global.setKeepFXS(69, gov, {"from": gov})
    assert curve_global.keepFXS() == 69
    assert curve_global.fraxVoter() == gov.address
    if not tests_using_tenderly:
        with brownie.reverts():
            curve_global.setKeepFXS(69, ZERO_ADDRESS, {"from": gov})
        with brownie.reverts():
            curve_global.setKeepFXS(10_001, gov, {"from": gov})
        with brownie.reverts():
            curve_global.setDepositLimit(69, {"from": whale})

    curve_global.setDepositLimit(0, {"from": gov})
    curve_global.setDepositLimit(69, {"from": curve_global.management()})
    assert curve_global.depositLimit() == 69

    if not tests_using_tenderly:
        with brownie.reverts():
            curve_global.setHarvestProfitMaxInUsdc(69, {"from": whale})
        with brownie.reverts():
            curve_global.setHarvestProfitMinInUsdc(69, {"from": whale})
        with brownie.reverts():
            curve_global.setKeeper(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setHealthcheck(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setRegistry(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setGuardian(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setConvexPoolManager(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setBooster(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setGovernance(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setManagement(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setTreasury(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setGuardian(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setTradeFactory(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setBaseFeeOracle(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setConvexStratImplementation(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setCurveStratImplementation(gov, {"from": whale})
        with brownie.reverts():
            curve_global.setManagementFee(69, {"from": whale})
        with brownie.reverts():
            curve_global.setPerformanceFee(69, {"from": whale})
        with brownie.reverts():
            curve_global.setPerformanceFee(9999, {"from": gov})
        with brownie.reverts():
            curve_global.setManagementFee(9999, {"from": gov})
        with brownie.reverts():
            curve_global.setOwner(gov, {"from": whale})
        with brownie.reverts():
            curve_global.acceptOwner({"from": whale})

    curve_global.setHarvestProfitMaxInUsdc(0, {"from": gov})
    curve_global.setHarvestProfitMaxInUsdc(69, {"from": curve_global.management()})
    assert curve_global.harvestProfitMaxInUsdc() == 69
    curve_global.setHarvestProfitMinInUsdc(0, {"from": gov})
    curve_global.setHarvestProfitMinInUsdc(69, {"from": curve_global.management()})
    assert curve_global.harvestProfitMinInUsdc() == 69
    curve_global.setKeeper(whale, {"from": gov})
    curve_global.setKeeper(gov, {"from": curve_global.management()})
    assert curve_global.keeper() == gov.address
    curve_global.setHealthcheck(whale, {"from": gov})
    curve_global.setHealthcheck(gov, {"from": curve_global.management()})
    assert curve_global.healthCheck() == gov.address
    curve_global.setRegistry(gov, {"from": gov})
    assert curve_global.registry() == gov.address
    curve_global.setGuardian(gov, {"from": gov})
    assert curve_global.guardian() == gov.address
    curve_global.setConvexPoolManager(gov, {"from": gov})
    assert curve_global.convexPoolManager() == gov.address
    curve_global.setBooster(gov, {"from": gov})
    assert curve_global.booster() == gov.address
    curve_global.setGovernance(gov, {"from": gov})
    assert curve_global.governance() == gov.address
    curve_global.setManagement(gov, {"from": gov})
    assert curve_global.management() == gov.address
    curve_global.setGuardian(gov, {"from": gov})
    assert curve_global.guardian() == gov.address
    curve_global.setTreasury(gov, {"from": gov})
    assert curve_global.treasury() == gov.address
    curve_global.setTradeFactory(gov, {"from": gov})
    assert curve_global.tradeFactory() == gov.address
    curve_global.setBaseFeeOracle(gov, {"from": gov})
    assert curve_global.baseFeeOracle() == gov.address
    curve_global.setConvexStratImplementation(gov, {"from": gov})
    assert curve_global.convexStratImplementation() == gov.address
    curve_global.setCurveStratImplementation(gov, {"from": gov})
    assert curve_global.curveStratImplementation() == gov.address
    curve_global.setManagementFee(69, {"from": gov})
    assert curve_global.managementFee() == 69
    curve_global.setPerformanceFee(69, {"from": gov})
    assert curve_global.performanceFee() == 69
    curve_global.setOwner(whale, {"from": gov})
    curve_global.acceptOwner({"from": whale})
    assert curve_global.owner() == whale.address
