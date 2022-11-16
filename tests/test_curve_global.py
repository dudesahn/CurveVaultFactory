import brownie
from brownie import Contract, ZERO_ADDRESS
from brownie import config
import math


def test_vault_deployment(
    StrategyConvexFactoryClonable,
    StrategyCurveBoostedFactoryClonable,
    StrategyConvexFraxFactoryClonable,
    strategist,
    curve_global,
    gov,
    accounts,
    guardian,
    token,
    healthCheck,
    chain,
    pid,
    gasOracle,
    new_registry,
    gauge,
    new_proxy,
    voter,
    whale,
    tests_using_tenderly,
    keeper_contract,
    amount,
    interface,
    booster,
    staking_address,
):
    # deploying curve global with frax strategies doesn't work unless with tenderly;
    # ganache crashes because of the try-catch in the fraxPid function
    # comment this out when doing hacky coverage testing (commenting out section in curveGlobal)
    #     if pid != 25:
    #         if not tests_using_tenderly:
    #             return

    # for most pids below 100, we already have a vault
    if pid < 100:
        print("PID less than 100, skipping permissionless vault testing")
        return

    # once our factory is deployed, setup the factory from gov
    registry_owner = accounts.at(new_registry.owner(), force=True)
    new_registry.setApprovedVaultsOwner(curve_global, True, {"from": registry_owner})
    new_registry.setVaultEndorsers(curve_global, True, {"from": registry_owner})

    # make sure our curve global can own vaults and endorse them
    assert new_registry.approvedVaultsOwner(curve_global)
    assert new_registry.vaultEndorsers(curve_global)
    assert curve_global.registry() == new_registry.address
    print("Our factory can endorse vaults")

    # update the strategy on our voter
    voter.setStrategy(new_proxy.address, {"from": gov})

    # set our factory address on the strategy proxy
    new_proxy.setFactory(curve_global.address, {"from": gov})
    print("New proxy updated, factory added to proxy")

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
    assert curve_global.canCreateVaultPermissionlessly(gauge)

    # before we deploy, check our gauge. we shouldn't have added this to our proxy yet
    answer = curve_global.doesStrategyProxyHaveGauge(gauge)
    print("Is this gauge already paired with a strategy on our proxy?", answer)
    assert not answer

    # tenderly RPC can't do brownie.reverts
    if not tests_using_tenderly:
        with brownie.reverts():
            curve_global.createNewVaultsAndStrategies(whale, {"from": whale})
        print("Can't create a vault for something that's not actually a gauge")

    # turn on keeps
    curve_global.setKeepCRV(69, curve_global.curveVoter(), {"from": gov})
    curve_global.setKeepCVX(69, gov, {"from": gov})
    curve_global.setKeepFXS(69, gov, {"from": gov})
    print(
        "Set our global keeps, don't mess with curve voter or we will revert on deploy"
    )

    tx = curve_global.createNewVaultsAndStrategies(gauge, {"from": whale})
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
    assert convex_strategy.creditThreshold() == 1e24
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
        assert curve_strategy.creditThreshold() == 1e24
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
        assert frax_strategy.creditThreshold() == 1e24
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
    assert convex_strategy.keeper() == keeper_contract
    assert curve_strategy.keeper() == keeper_contract
    assert frax_strategy.keeper() == keeper_contract
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2**256 - 1, {"from": whale})
    vault.deposit(amount, {"from": whale})

    keeper_contract.harvestStrategy(convex_strategy, {"from": rando})
    if curve_strat != ZERO_ADDRESS:
        keeper_contract.harvestStrategy(curve_strategy, {"from": rando})
    if frax_strat != ZERO_ADDRESS:
        keeper_contract.harvestStrategy(frax_strategy, {"from": rando})

    # assert that money deposited to convex
    assert convex_strategy.stakedBalance() + frax_strategy.stakedBalance() > 0

    # wait a week for our funds to unlock
    chain.sleep(86400 * 7)
    chain.mine(1)

    # force our funds out of frax, then sweep them away
    user_vault = Contract(frax_strategy.userVault())
    staking_contract = Contract(staking_address)
    staking_token = Contract(staking_contract.stakingToken())
    stake = staking_contract.lockedStakesOf(user_vault)[0]
    kek = stake[0]
    user_vault.withdrawLocked(kek, {"from": frax_strategy})
    assert staking_token.balanceOf(frax_strategy) > 0
    frax_strategy.sweep(staking_token, {"from": gov})

    if not tests_using_tenderly:
        with brownie.reverts():
            keeper_contract.harvestStrategy(frax_strategy, {"from": rando})

    # turn off healthcheck
    frax_strategy.setDoHealthCheck(False, {"from": gov})
    keeper_contract.harvestStrategy(frax_strategy, {"from": rando})

    # we can deploy another stETH vault since this is the first automated one
    tx = curve_global.createNewVaultsAndStrategies(
        "0x182B723a58739a9c974cFDB385ceaDb237453c28", {"from": whale}
    )

    if not tests_using_tenderly:
        # can't deploy another frax vault permissionlessly
        with brownie.reverts():
            tx = curve_global.createNewVaultsAndStrategies(gauge, {"from": whale})

        # we can't do a second stETH vault either
        with brownie.reverts():
            tx = curve_global.createNewVaultsAndStrategies(
                "0x182B723a58739a9c974cFDB385ceaDb237453c28", {"from": whale}
            )


def test_permissioned_vault(
    StrategyConvexFactoryClonable,
    StrategyCurveBoostedFactoryClonable,
    StrategyConvexFraxFactoryClonable,
    strategist,
    curve_global,
    gov,
    accounts,
    guardian,
    token,
    healthCheck,
    chain,
    pid,
    gasOracle,
    new_registry,
    gauge,
    new_proxy,
    voter,
    whale,
    tests_using_tenderly,
):
    # deploying curve global with frax strategies doesn't work unless with tenderly;
    # ganache crashes because of the try-catch in the fraxPid function
    # comment this out when doing hacky coverage testing (commenting out section in curveGlobal)
    #     if pid != 25:
    #         if not tests_using_tenderly:
    #             return

    # once our factory is deployed, setup the factory from gov
    registry_owner = accounts.at(new_registry.owner(), force=True)
    new_registry.setApprovedVaultsOwner(curve_global, True, {"from": registry_owner})
    new_registry.setVaultEndorsers(curve_global, True, {"from": registry_owner})

    # make sure our curve global can own vaults and endorse them
    assert new_registry.approvedVaultsOwner(curve_global)
    assert new_registry.vaultEndorsers(curve_global)
    assert curve_global.registry() == new_registry.address
    print("Our factory can endorse vaults")

    _pid = curve_global.getPid(gauge)
    assert _pid == pid
    print("\nOur pid workup works, pid:", pid)

    # update the strategy on our voter
    voter.setStrategy(new_proxy.address, {"from": gov})

    # set our factory address on the strategy proxy
    new_proxy.setFactory(curve_global.address, {"from": gov})
    print("New proxy updated, factory added to proxy")

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
        gauge, "", "", {"from": gov}
    )
    vault_address = tx.events["NewAutomatedVault"]["vault"]
    vault = Contract(vault_address)
    print("Vault name:", vault.name())

    print("Vault endorsed:", vault_address)
    info = tx.events["NewAutomatedVault"]

    print("Here's our new vault created event:", info, "\n")

    # print our addresses
    cvx_strat = tx.events["NewAutomatedVault"]["convexStrategy"]
    convex_strategy = StrategyConvexFactoryClonable.at(cvx_strat)

    curve_strat = tx.events["NewAutomatedVault"]["curveStrategy"]
    if curve_strat != ZERO_ADDRESS:
        curve_strategy = StrategyCurveBoostedFactoryClonable.at(curve_strat)

    frax_strat = tx.events["NewAutomatedVault"]["convexFraxStrategy"]
    if frax_strat != ZERO_ADDRESS:
        frax_strategy = StrategyConvexFraxFactoryClonable.at(frax_strat)

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
    assert convex_strategy.creditThreshold() == 1e24
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

    # curve
    assert vault.withdrawalQueue(1) == curve_strat
    assert vault.strategies(curve_strat)["performanceFee"] == 0
    assert curve_strategy.creditThreshold() == 1e24
    assert curve_strategy.healthCheck() == curve_global.healthCheck()
    assert curve_strategy.localKeepCRV() == curve_global.keepCRV()
    assert curve_strategy.curveVoter() == curve_global.curveVoter()
    assert curve_strategy.rewards() == curve_global.treasury()
    assert curve_strategy.strategist() == curve_global.management()
    assert curve_strategy.keeper() == curve_global.keeper()

    if pid > 100:
        # frax
        assert vault.withdrawalQueue(2) == frax_strat
        assert vault.strategies(frax_strat)["performanceFee"] == 0
        print("All three strategies attached in order")
        assert frax_strategy.creditThreshold() == 1e24
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

    # deploy another frax vault, this one shouldn't have any curve
    tx = curve_global.createNewVaultsAndStrategiesPermissioned(
        gauge, "test2", "test2", {"from": gov}
    )
    vault_address = tx.events["NewAutomatedVault"]["vault"]
    vault = Contract(vault_address)
    assert vault.withdrawawalQueue(2) == ZERO_ADDRESS
    print("Second frax vault done")
    chain.sleep(1)
    chain.mine(1)

    # THESE ARE REVERTING BECAUSE WE NEED TO DEPLOY THE NEW VERSION OF THE REGISTRY FROM PANDAf

    # deploy a stETH vault, should be two long as well (Convex and Curve)
    tx = curve_global.createNewVaultsAndStrategiesPermissioned(
        "0x182B723a58739a9c974cFDB385ceaDb237453c28", "test3", "test3", {"from": gov}
    )
    vault_address = tx.events["NewAutomatedVault"]["vault"]
    vault = Contract(vault_address)
    assert vault.withdrawawalQueue(2) == ZERO_ADDRESS
    print("First stETH vault done")
    chain.sleep(1)
    chain.mine(1)

    # deploy a second stETH vault, should only have convex
    tx = curve_global.createNewVaultsAndStrategiesPermissioned(
        "0x182B723a58739a9c974cFDB385ceaDb237453c28", "test4", "test4", {"from": gov}
    )
    vault_address = tx.events["NewAutomatedVault"]["vault"]
    vault = Contract(vault_address)
    assert vault.withdrawawalQueue(1) == ZERO_ADDRESS
    print("Second stETH vault done")


def test_curve_global_setters_and_views(
    gov,
    whale,
    chain,
    amount,
    curve_global,
    new_registry,
    accounts,
    gauge,
    pid,
    frax_pid,
):

    # once our factory is deployed, setup the factory from gov
    registry_owner = accounts.at(new_registry.owner(), force=True)
    new_registry.setApprovedVaultsOwner(curve_global, True, {"from": registry_owner})
    new_registry.setVaultEndorsers(curve_global, True, {"from": registry_owner})

    # make sure our curve global can own vaults and endorse them
    assert new_registry.approvedVaultsOwner(curve_global)
    assert new_registry.vaultEndorsers(curve_global)
    print("Our factory can endorse vaults")

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

    frax_info = curve_global.getFraxInfo(_pid)
    print("Is this a Frax pool?", frax_info[0])
    if frax_info[0]:
        assert frax_info[1] == frax_pid
        print("Our Frax PID matches")
    else:
        print("Not a Frax pool")

    # check if we can create vaults
    # this one should be yes for automatic vaults (stETH)
    assert curve_global.canCreateVaultPermissionlessly(
        "0x182B723a58739a9c974cFDB385ceaDb237453c28"
    )

    # this one should always be yes (SDT/ETH) as we will almost certainly never make a vault for this
    assert curve_global.canCreateVaultPermissionlessly(
        "0x60355587a8D4aa67c2E64060Ab36e566B9bCC000"
    )

    # this one should be no (stETH)
    assert not curve_global.doesStrategyProxyHaveGauge(
        "0x182B723a58739a9c974cFDB385ceaDb237453c28"
    )

    # check our latest vault for stETH
    latest = curve_global.latestDefaultOrAutomatedVaultFromGauge(
        "0x182B723a58739a9c974cFDB385ceaDb237453c28"
    )
    print("Latest stETH vault:", latest)

    # check our setters
    with brownie.reverts():
        curve_global.setKeepCVX(69, gov, {"from": whale})
    curve_global.setKeepCVX(0, gov, {"from": gov})
    curve_global.setKeepCVX(69, gov, {"from": gov})
    assert curve_global.keepCVX() == 69
    assert curve_global.convexVoter() == gov.address
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
    with brownie.reverts():
        curve_global.setKeepFXS(69, ZERO_ADDRESS, {"from": gov})
    with brownie.reverts():
        curve_global.setKeepFXS(10_001, gov, {"from": gov})

    with brownie.reverts():
        curve_global.setDepositLimit(69, {"from": whale})
    curve_global.setDepositLimit(0, {"from": gov})
    curve_global.setDepositLimit(69, {"from": curve_global.management()})
    assert curve_global.depositLimit() == 69

    with brownie.reverts():
        curve_global.setHarvestProfitMaxInUsdc(69, {"from": whale})
    curve_global.setHarvestProfitMaxInUsdc(0, {"from": gov})
    curve_global.setHarvestProfitMaxInUsdc(69, {"from": curve_global.management()})
    assert curve_global.harvestProfitMaxInUsdc() == 69

    with brownie.reverts():
        curve_global.setHarvestProfitMinInUsdc(69, {"from": whale})
    curve_global.setHarvestProfitMinInUsdc(0, {"from": gov})
    curve_global.setHarvestProfitMinInUsdc(69, {"from": curve_global.management()})
    assert curve_global.harvestProfitMinInUsdc() == 69

    with brownie.reverts():
        curve_global.setKeeper(gov, {"from": whale})
    curve_global.setKeeper(whale, {"from": gov})
    curve_global.setKeeper(gov, {"from": curve_global.management()})
    assert curve_global.keeper() == gov.address

    with brownie.reverts():
        curve_global.setHealthcheck(gov, {"from": whale})
    curve_global.setHealthcheck(whale, {"from": gov})
    curve_global.setHealthcheck(gov, {"from": curve_global.management()})
    assert curve_global.healthCheck() == gov.address

    with brownie.reverts():
        curve_global.setRegistry(gov, {"from": whale})
    curve_global.setRegistry(gov, {"from": gov})
    assert curve_global.registry() == gov.address

    with brownie.reverts():
        curve_global.setGuardian(gov, {"from": whale})
    curve_global.setGuardian(gov, {"from": gov})
    assert curve_global.guardian() == gov.address

    with brownie.reverts():
        curve_global.setConvexPoolManager(gov, {"from": whale})
    curve_global.setConvexPoolManager(gov, {"from": gov})
    assert curve_global.convexPoolManager() == gov.address

    with brownie.reverts():
        curve_global.setConvexFraxPoolRegistry(gov, {"from": whale})
    curve_global.setConvexFraxPoolRegistry(gov, {"from": gov})
    assert curve_global.convexFraxPoolRegistry() == gov.address

    with brownie.reverts():
        curve_global.setBooster(gov, {"from": whale})
    curve_global.setBooster(gov, {"from": gov})
    assert curve_global.booster() == gov.address

    with brownie.reverts():
        curve_global.setFraxBooster(gov, {"from": whale})
    curve_global.setFraxBooster(gov, {"from": gov})
    assert curve_global.fraxBooster() == gov.address

    with brownie.reverts():
        curve_global.setGovernance(gov, {"from": whale})
    curve_global.setGovernance(gov, {"from": gov})
    assert curve_global.governance() == gov.address

    with brownie.reverts():
        curve_global.setManagement(gov, {"from": whale})
    curve_global.setManagement(gov, {"from": gov})
    assert curve_global.management() == gov.address

    with brownie.reverts():
        curve_global.setGuardian(gov, {"from": whale})
    curve_global.setGuardian(gov, {"from": gov})
    assert curve_global.guardian() == gov.address

    with brownie.reverts():
        curve_global.setTreasury(gov, {"from": whale})
    curve_global.setTreasury(gov, {"from": gov})
    assert curve_global.treasury() == gov.address

    with brownie.reverts():
        curve_global.setTradeFactory(gov, {"from": whale})
    curve_global.setTradeFactory(gov, {"from": gov})
    assert curve_global.tradeFactory() == gov.address

    with brownie.reverts():
        curve_global.setBaseFeeOracle(gov, {"from": whale})
    curve_global.setBaseFeeOracle(gov, {"from": gov})
    assert curve_global.baseFeeOracle() == gov.address

    with brownie.reverts():
        curve_global.setConvexStratImplementation(gov, {"from": whale})
    curve_global.setConvexStratImplementation(gov, {"from": gov})
    assert curve_global.convexStratImplementation() == gov.address

    with brownie.reverts():
        curve_global.setCurveStratImplementation(gov, {"from": whale})
    curve_global.setCurveStratImplementation(gov, {"from": gov})
    assert curve_global.curveStratImplementation() == gov.address

    with brownie.reverts():
        curve_global.setConvexFraxStratImplementation(gov, {"from": whale})
    curve_global.setConvexFraxStratImplementation(gov, {"from": gov})
    assert curve_global.convexFraxStratImplementation() == gov.address

    with brownie.reverts():
        curve_global.setManagementFee(69, {"from": whale})
    curve_global.setManagementFee(69, {"from": gov})
    assert curve_global.managementFee() == 69
    with brownie.reverts():
        curve_global.setManagementFee(9999, {"from": gov})

    with brownie.reverts():
        curve_global.setPerformanceFee(69, {"from": whale})
    curve_global.setPerformanceFee(69, {"from": gov})
    assert curve_global.performanceFee() == 69
    with brownie.reverts():
        curve_global.setPerformanceFee(9999, {"from": gov})

    with brownie.reverts():
        curve_global.setOwner(gov, {"from": whale})
    curve_global.setOwner(whale, {"from": gov})
    with brownie.reverts():
        curve_global.acceptOwner({"from": gov})
    curve_global.acceptOwner({"from": whale})
    assert curve_global.owner() == whale.address
