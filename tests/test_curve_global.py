import brownie
from brownie import Contract
from brownie import config
import math


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
    # deploying curve global with frax strategies doesn't work unless with tenderly
    if pid != 25:
        if not tests_using_tenderly:
            return

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
