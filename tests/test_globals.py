import brownie


def test_keepers(
    strategist,
    vault,
    toke_gauge,
    curve_global,
):
    print(curve_global.allDeployedVaults())
    assert curve_global.numVaults() == 1

    assert vault == curve_global.deployedVaults(0)

    with brownie.reverts("Vault already exists"):
        curve_global.createNewVaultsAndStrategies(toke_gauge, {"from": strategist})

    # test a default type
    assert (
        curve_global.alreadyExistsFromToken(
            "0xC4C319E2D4d66CcA4464C0c2B32c9Bd23ebe784e"
        )
        == "0x718AbE90777F5B778B52D553a5aBaa148DD0dc5D"
    )


def test_keeps(
    gov,
    whale,
    other_gauge,
    strategy,
    StrategyConvexFactoryClonable,
    curve_global,
):
    assert curve_global.numVaults() == 1

    new_keep_crv = 4_000
    new_keep_cvx = 6_000
    voter_crv = whale
    voter_cvx = strategy

    curve_global.setKeepCRV(new_keep_crv, voter_crv, {"from": gov})
    curve_global.setKeepCVX(new_keep_cvx, voter_cvx, {"from": gov})

    t1 = curve_global.createNewVaultsAndStrategies(other_gauge, {"from": gov})

    new_strategy = StrategyConvexFactoryClonable.at(
        t1.events["NewAutomatedVault"]["strategy"]
    )

    assert new_strategy.localKeepCRV() == new_keep_crv
    assert new_strategy.localKeepCVX() == new_keep_cvx
    assert new_strategy.curveVoter() == voter_crv
    assert new_strategy.convexVoter() == voter_cvx
