import brownie
from brownie import Contract
from brownie import config
import math


def test_curve_global(
    gov,
    whale,
    chain,
    amount,
    curve_global,
    new_registry,
):

    print("\nSuccessful deployment of factory:", curve_global)

    # make sure our curve global can own vaults and endorse them
    assert new_registry.approvedVaultsOwner(curve_global)
    assert new_registry.vaultEndorsers(curve_global)
    print("Our factory can endorse vaults")


def test_vault_deployment(
    gov,
    whale,
    chain,
    amount,
    curve_global,
    new_registry,
    strategy,
    vault,
    gauge,
    pid,
):

    _pid = curve_global.getPid(gauge)
    assert _pid == pid
    print("\nOur pid workup works, pid:", pid)

    tx = curve_global.getFraxPid(_pid)
    print("We can pull FRAX pids too:", tx[0])

    print("Let's deploy this vault")
