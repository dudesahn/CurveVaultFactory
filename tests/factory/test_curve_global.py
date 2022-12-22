import brownie
from brownie import Contract, ZERO_ADDRESS, config
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
    steth_gauge,
    steth_lp,
):
    # deploying curve global with frax strategies doesn't work unless with tenderly;
    # ganache crashes because of the try-catch in the fraxPid function
    # however, I usually do hacky coverage testing (commenting out section in curveGlobal)

    # for most pids below 100, we already have a vault, and any legacy vault will revert when trying to deploy permissionlessly
    if pid < 100:
        print("PID less than 100, skipping permissionless vault testing")
        return

    # make sure our curve global can own vaults and endorse them
    assert new_registry.approvedVaultsOwner(curve_global)
    assert new_registry.vaultEndorsers(curve_global)
    assert curve_global.registry() == new_registry.address
    print("Our factory can endorse vaults")

    # update the strategy on our voter
    voter.setStrategy(new_proxy.address, {"from": gov})

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
    assert curve_global.latestStandardVaultFromGauge(steth_gauge) != ZERO_ADDRESS
    assert not curve_global.canCreateVaultPermissionlessly(steth_gauge)
    assert not curve_global.canCreateVaultPermissionlessly(gauge)
    assert curve_global.doesStrategyProxyHaveGauge(gauge)


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
    token,
    steth_gauge,
    deployer,
):

    # set owner of factory to yChad
    curve_global.setOwner(gov, {"from": deployer})
    curve_global.acceptOwner({"from": gov})
    print("Factory ownership transferred")

    if pid == 25:
        stvault = new_registry.latestVault(token)
        print("Here's our newest stETH Vault", stvault)

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
    assert not curve_global.canCreateVaultPermissionlessly(steth_gauge)

    # this one should always be yes (SDT/ETH) as we will almost certainly never make a vault for this
    assert curve_global.canCreateVaultPermissionlessly(
        "0x60355587a8D4aa67c2E64060Ab36e566B9bCC000"
    )

    # this one should be yes (stETH)
    assert curve_global.doesStrategyProxyHaveGauge(steth_gauge)

    # check our latest vault for stETH
    latest = curve_global.latestStandardVaultFromGauge(steth_gauge)
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
