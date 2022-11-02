import pytest
import brownie
from brownie import config, Wei, Contract
from brownie import network
import time, re, json, requests
import web3
from web3 import HTTPProvider

#@pytest.fixture(scope="module", autouse=True)
def tenderly_fork(web3):
    fork_base_url = "https://simulate.yearn.network/fork"
    payload = {"network_id": "1"}
    resp = requests.post(fork_base_url, headers={}, json=payload)
    fork_id = resp.json()["simulation_fork"]["id"]
    fork_rpc_url = f"https://rpc.tenderly.co/fork/{fork_id}"
    print(fork_rpc_url)
    tenderly_provider = web3.HTTPProvider(fork_rpc_url, {"timeout": 600})
    web3.provider = tenderly_provider
    print(f"https://dashboard.tenderly.co/yearn/yearn-web/fork/{fork_id}")


# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

@pytest.fixture(scope="module")
def steth_curve_lp(Contract):
    yield Contract("0x06325440D014e39736583c165C2963BA99fAf14E")



@pytest.fixture(scope="module")
def new_registry(interface):
    yield interface.IRegistry("0x78f73705105A63e06B932611643E0b210fAE93E9")


# put our pool's convex pid here; this is the only thing that should need to change up here **************
@pytest.fixture(scope="module")
def pid():
    # pid = 56
    pid = 99  # toke
    yield pid


@pytest.fixture(scope="module")
def whale(accounts, toke_gauge, token):
    # Totally in it for the tech
    # Update this with a large holder of your want token (the largest EOA holder of LP)

    whale = accounts.at("0x89eBCb7714bd0D2F33ce3a35C12dBEB7b94af169", force=True)
    token.transfer(whale, 1_000 * 1e18, {"from": toke_gauge})
    yield whale


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="module")
def amount():
    amount = 500e18
    yield amount


# this is the name we want to give our strategy
@pytest.fixture(scope="module")
def strategy_name():
    strategy_name = "StrategyConvexOUSD"
    yield strategy_name


# we need these next two fixtures for deploying our curve strategy, but not for convex. for convex we can pull them programmatically.
# this is the address of our rewards token, in this case it's a dummy (ALCX) that our whale happens to hold just used to test stuff
@pytest.fixture(scope="module")
def rewards_token():
    yield Contract("0x8207c1FfC5B6804F6024322CcF34F29c3541Ae26")


# this is whether our pool has extra rewards tokens or not, use this to confirm that our strategy set everything up correctly.
@pytest.fixture(scope="module")
def has_rewards():
    has_rewards = True
    yield has_rewards


# Only worry about changing things above this line, unless you want to make changes to the vault or strategy.
# ----------------------------------------------------------------------- #

# all contracts below should be able to stay static based on the pid
@pytest.fixture(scope="module")
def booster():  # this is the deposit contract
    yield Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")


@pytest.fixture(scope="function")
def voter():
    yield Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")


@pytest.fixture(scope="function")
def convexToken():
    yield Contract("0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B")


@pytest.fixture(scope="function")
def crv():
    yield Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")


@pytest.fixture(scope="function")
def dai():
    yield Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")


@pytest.fixture(scope="module")
def other_vault_strategy():
    yield Contract("0x8423590CD0343c4E18d35aA780DF50a5751bebae")


@pytest.fixture(scope="function")
def proxy():
    yield Contract("0xA420A63BbEFfbda3B147d0585F1852C358e2C152")


@pytest.fixture(scope="module")
def curve_registry():
    yield Contract("0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5")


@pytest.fixture(scope="module")
def healthCheck():
    yield Contract("0xDDCea799fF1699e98EDF118e0629A974Df7DF012")


@pytest.fixture(scope="function")
def live_spell_strat(trade_factory, ymechs_safe):
    strategy = Contract("0xeDB4B647524FC2B9985019190551b197c6AB6C5c")
    trade_factory.grantRole(trade_factory.STRATEGY(), strategy, {"from": ymechs_safe})
    yield strategy


@pytest.fixture(scope="function")
def live_yfi_strat(trade_factory, ymechs_safe):
    network.gas_limit(6_000_000)
    # network.gas_price(0)
    # network.max_fee(0)
    # network.priority_fee(0)
    # , "allow_revert": True
    strategy = Contract("0xa04947059831783C561e59A43B93dCB5bEE7cab2")

    trade_factory.grantRole(trade_factory.STRATEGY(), strategy, {"from": ymechs_safe})
    yield strategy


@pytest.fixture(scope="module")
def farmed():
    # this is the token that we are farming and selling for more of our want.
    yield Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")


@pytest.fixture(scope="module")
def weth(interface):
    yield interface.ERC20("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


@pytest.fixture(scope="module")
def uniswap_router(Contract):
    yield Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")


@pytest.fixture(scope="module")
def sushiswap_router(Contract):
    yield Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")


@pytest.fixture(scope="module")
def curve_zapper(Contract):
    yield Contract("0xA79828DF1850E8a3A3064576f380D90aECDD3359")


# Define relevant tokens and contracts in this section
@pytest.fixture(scope="module")
def token(pid, booster):
    # this should be the address of the ERC-20 used by the strategy/vault
    token_address = booster.poolInfo(pid)[0]
    yield Contract(token_address)


@pytest.fixture
def trade_factory():
    # yield Contract("0xBf26Ff7C7367ee7075443c4F95dEeeE77432614d")
    yield Contract("0x99d8679bE15011dEAD893EB4F5df474a4e6a8b29")

@pytest.fixture
def new_trade_factory():
    # yield Contract("0xBf26Ff7C7367ee7075443c4F95dEeeE77432614d")
    yield Contract("0xd6a8ae62f4d593DAf72E2D7c9f7bDB89AB069F06")

# zero address
@pytest.fixture(scope="module")
def zero_address():
    zero_address = "0x0000000000000000000000000000000000000000"
    yield zero_address


# gauge for the curve pool
@pytest.fixture(scope="module")
def gauge(pid, booster):
    # this should be the address of the convex deposit token
    gauge = booster.poolInfo(pid)[2]
    yield Contract(gauge)


# curve deposit pool
@pytest.fixture(scope="module")
def pool(token, curve_registry, zero_address):
    if curve_registry.get_pool_from_lp_token(token) == zero_address:
        poolAddress = token
    else:
        _poolAddress = curve_registry.get_pool_from_lp_token(token)
        poolAddress = Contract(_poolAddress)
    yield poolAddress


@pytest.fixture(scope="module")
def cvxDeposit(booster, pid):
    # this should be the address of the convex deposit token
    cvx_address = booster.poolInfo(pid)[1]
    yield Contract(cvx_address)


@pytest.fixture(scope="module")
def rewardsContract(pid, booster):
    rewardsContract = booster.poolInfo(pid)[3]
    yield Contract(rewardsContract)


@pytest.fixture(scope="module")
def gasOracle():
    yield Contract("0xb5e1CAcB567d98faaDB60a1fD4820720141f064F")


# Define any accounts in this section
# for live testing, governance is the strategist MS; we will update this before we endorse
# normal gov is ychad, 0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52
@pytest.fixture(scope="module")
def gov(accounts):

    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)


@pytest.fixture(scope="module")
def strategist_ms(accounts):
    # like governance, but better
    yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)


@pytest.fixture(scope="module")
def keeper(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


@pytest.fixture(scope="module")
def rewards(accounts):
    yield accounts.at("0x8Ef63b525fceF7f8662D98F77f5C9A86ae7dFE09", force=True)


@pytest.fixture(scope="module")
def guardian(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def management(accounts):
    yield accounts[3]


@pytest.fixture
def ymechs_safe():
    yield Contract("0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6")


@pytest.fixture(scope="module")
def multicall_swapper(interface):
    yield interface.MultiCallOptimizedSwapper(
        # "0xceB202F25B50e8fAF212dE3CA6C53512C37a01D2"
        "0xB2F65F254Ab636C96fb785cc9B4485cbeD39CDAA"
    )


@pytest.fixture(scope="module")
def strategist(accounts):
    yield accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)


# # list any existing strategies here
# @pytest.fixture(scope="module")
# def LiveStrategy_1():
#     yield Contract("0xC1810aa7F733269C39D640f240555d0A4ebF4264")


# use this if you need to deploy the vault
@pytest.fixture(scope="function")
def vault(
    pm, gov, rewards, guardian, strategy, management, strategist_ms, token, chain
):
    network.gas_price("0 gwei")
    network.gas_limit(6700000)
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at(strategy.vault())

    print(vault.symbol())
    print(vault.name())

    vault.acceptGovernance({"from": gov})

    vault.setManagementFee(0, {"from": gov})
    yield vault

@pytest.fixture(scope="module")
def keeper_contract(KeeperWrapper):
    yield KeeperWrapper.at('0x256e6a486075fbAdbB881516e9b6b507fd082B5D')

@pytest.fixture(scope="module")
def toke_gauge(Contract):
    yield Contract("0xa0C08C0Aede65a0306F7dD042D2560dA174c91fC")
@pytest.fixture(scope="module")
def other_gauge(Contract):
    yield Contract("0xa9A9BC60fc80478059A83f516D5215185eeC2fc0")


@pytest.fixture(scope="function")
def v2(pm, gov, rewards, guardian, management, token, chain):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, {"from": guardian})
    vault.setDepositLimit(2**256 - 1, {"from": gov})
    vault.setManagement(management, {"from": gov})
    chain.sleep(1)
    yield vault


# use this if your vault is already deployed
# @pytest.fixture(scope="function")
# def vault(pm, gov, rewards, guardian, management, token, chain):
#     vault = Contract("0x497590d2d57f05cf8B42A36062fA53eBAe283498")
#     yield vault
@pytest.fixture
def ymechs_safe():
    yield Contract("0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6")

@pytest.fixture(scope="function")
def curve_global(CurveGlobal, StrategyConvexFactoryClonable, new_trade_factory, strategist, new_registry, gov):
    s = strategist.deploy(StrategyConvexFactoryClonable, '0x6B5ce31AF687a671a804d8070Ddda99Cab926dfE', new_trade_factory, 87, 10_000*1e6, 25_000*1e6, '0xF403C135812408BFbE8713b5A23a04b3D48AAE31', '0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B')
    bg = strategist.deploy(CurveGlobal, new_registry, s, gov)
    
    yield bg

# replace the first value with the name of your strategy
@pytest.fixture(scope="function")
def strategy(
    StrategyConvexFactoryClonable,
    strategist,
    keeper,
    ymechs_safe,
    v2,
    curve_global,
    gov,
    accounts,
    CurveGlobal,
    guardian,
    token,
    healthCheck,
    chain,
    Contract,
    pid,
    proxy,
    gasOracle,
    new_registry,
    strategist_ms,
    toke_gauge,
):

    pid = curve_global.getPid(toke_gauge)
    print(pid)
    print(toke_gauge.lp_token())


    registry_owner = accounts.at(new_registry.owner(), force=True)
    new_registry.setApprovedVaultsOwner(curve_global, True, {"from": registry_owner})
    new_registry.setRole(curve_global, False, True, {"from": registry_owner})


    print("curve gloval: ", curve_global)
    print("toke guage: ", toke_gauge)
    print("strategist: ", strategist)
    
    t11 = curve_global.createNewVaultsAndStrategies(
        toke_gauge, {"from": strategist}
    )
    strat = t11.events['NewAutomatedVault']['strategy']
    print("endorsed")



    # make sure to include all constructor parameters needed here
    strategy = StrategyConvexFactoryClonable.at(strat)
    # print(strategy.rewards())
    # print("contributors: ", sharer.viewContributors(strategy))

    gasOracle.setMaxAcceptableBaseFee(20000000000000, {"from": strategist_ms})
    # set our management fee to zero so it doesn't mess with our profit checking

    chain.sleep(1)
    strategy.harvest({"from": strategist_ms})
    chain.sleep(1)
    yield strategy


# use this if your strategy is already deployed
# @pytest.fixture(scope="function")
# def strategy():
#     # parameters for this are: strategy, vault, max deposit, minTimePerInvest, slippage protection (10000 = 100% slippage allowed),
#     strategy = Contract("0xC1810aa7F733269C39D640f240555d0A4ebF4264")
#     yield strategy
