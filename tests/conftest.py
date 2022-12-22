import pytest
import brownie
from brownie import config, Wei, Contract, ZERO_ADDRESS
from brownie import network
import time, re, json, requests
import web3
from web3 import HTTPProvider

# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


# set this for if we want to use tenderly or not; mostly helpful because with brownie.reverts fails in tenderly forks.
use_tenderly = False


################################################## TENDERLY DEBUGGING ##################################################

# change autouse to True if we want to use this fork to help debug tests
@pytest.fixture(scope="session", autouse=use_tenderly)
def tenderly_fork(web3, chain):
    fork_base_url = "https://simulate.yearn.network/fork"
    payload = {"network_id": str(chain.id)}
    resp = requests.post(fork_base_url, headers={}, json=payload)
    fork_id = resp.json()["simulation_fork"]["id"]
    fork_rpc_url = f"https://rpc.tenderly.co/fork/{fork_id}"
    print(fork_rpc_url)
    tenderly_provider = web3.HTTPProvider(fork_rpc_url, {"timeout": 600})
    web3.provider = tenderly_provider
    print(f"https://dashboard.tenderly.co/yearn/yearn-web/fork/{fork_id}")


################################################ UPDATE THINGS BELOW HERE ################################################


@pytest.fixture(scope="session")
def tests_using_tenderly():
    yes_or_no = use_tenderly
    yield yes_or_no


# use this to set what chain we use. 1 for ETH, 250 for fantom
chain_used = 1


# put our test pool's convex pid here
# if you change this, make sure to update addresses/values below too
@pytest.fixture(scope="session")
def pid():
    pid = 100  # 100 FRAX-USDC (do for frax), 25 stETH
    yield pid


# put our pool's frax pid here
@pytest.fixture(scope="session")
def frax_pid():
    frax_pid = 9  # 27 DOLA-FRAXBP, 9 FRAX-USDC
    yield frax_pid


# put our pool's staking address here
@pytest.fixture(scope="session")
def staking_address():
    staking_address = "0x963f487796d54d2f27bA6F3Fbe91154cA103b199"  # 0x963f487796d54d2f27bA6F3Fbe91154cA103b199 FRAX-USDC, 0xE7211E87D60177575846936F2123b5FA6f0ce8Ab DOLA-FRAXBP
    yield staking_address


# put our test pool's convex pid here
@pytest.fixture(scope="session")
def test_pid():
    test_pid = 115  # 115 DOLA FRAXBP, 100 FRAX-USDC
    yield test_pid


# put our pool's frax pid here
@pytest.fixture(scope="session")
def test_frax_pid():
    test_frax_pid = 27  # 27 DOLA-FRAXBP, 9 FRAX-USDC
    yield test_frax_pid


# put our pool's staking address here
@pytest.fixture(scope="session")
def test_staking_address():
    test_staking_address = "0xE7211E87D60177575846936F2123b5FA6f0ce8Ab"  # 0x963f487796d54d2f27bA6F3Fbe91154cA103b199 FRAX-USDC, 0xE7211E87D60177575846936F2123b5FA6f0ce8Ab DOLA-FRAXBP
    yield test_staking_address


# put our pool's convex pid here
@pytest.fixture(scope="session")
def which_strategy():
    # must be 0, 1, or 2 for convex, curve, and frax. Only test 2 (Frax) for pools that actually have frax.
    which_strategy = 2
    yield which_strategy


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="session")
def amount():
    amount = 500_000e18  # 500k for FRAX-USDC, 300 for stETH
    yield amount


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="session")
def profit_amount():
    profit_amount = 1_000e18  # 1k for FRAX-USDC, 2 for stETH
    yield profit_amount


@pytest.fixture(scope="session")
def profit_whale(accounts, profit_amount, token):
    # Totally in it for the tech
    # Update this with a large holder of your want token (the largest EOA holder of LP)
    # use the FRAX-USDC pool for now
    # ideally not the same whale as the main whale, or else they will lose money
    profit_whale = accounts.at(
        "0x8fdb0bB9365a46B145Db80D0B1C5C5e979C84190", force=True
    )  # 0x8fdb0bB9365a46B145Db80D0B1C5C5e979C84190, BUSD pool, 17m tokens, stETH: 0xF31501905Bdb035119031510c724C4a4d67acA14, 500 tokens
    if token.balanceOf(profit_whale) < 5 * profit_amount:
        raise ValueError(
            "Our profit whale needs more funds. Find another whale or reduce your profit_amount variable."
        )
    yield profit_whale


@pytest.fixture(scope="session")
def whale(accounts, amount, token):
    # Totally in it for the tech
    # Update this with a large holder of your want token (the largest EOA holder of LP)
    # use the FRAX-USDC pool for now
    whale = accounts.at(
        "0xE57180685E3348589E9521aa53Af0BCD497E884d", force=True
    )  # 0xE57180685E3348589E9521aa53Af0BCD497E884d, DOLA pool, 23.6m tokens, stETH: 0x43378368D84D4bA00D1C8E97EC2E6016A82fC062, 730 tokens
    if token.balanceOf(whale) < 2 * amount:
        raise ValueError(
            "Our whale needs more funds. Find another whale or reduce your amount variable."
        )
    yield whale


# set address if already deployed, use ZERO_ADDRESS if not
@pytest.fixture(scope="session")
def vault_address():
    vault_address = (
        "0x1A5ebfF0E881Aec34837845e4D0EB430a1B4b737"  # FRAX-USDC factory vault
    )
    yield vault_address


# curve deposit pool for old pools, set to ZERO_ADDRESS otherwise
@pytest.fixture(scope="session")
def old_pool():
    old_pool = ZERO_ADDRESS
    yield old_pool


# this is the name we want to give our strategy
@pytest.fixture(scope="session")
def strategy_name():
    strategy_name = "StrategyConvexFRAX-USDC"
    yield strategy_name


# this is the address of our rewards token
@pytest.fixture(scope="session")
def rewards_token():  # OGN 0x8207c1FfC5B6804F6024322CcF34F29c3541Ae26, SPELL 0x090185f2135308BaD17527004364eBcC2D37e5F6
    # SNX 0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F, ANGLE 0x31429d1856aD1377A8A0079410B297e1a9e214c2, LDO 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32
    yield Contract("0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32")


# sUSD gauge uses blocks instead of seconds to determine rewards, so this needs to be true for that to test if we're earning
@pytest.fixture(scope="session")
def try_blocks():
    try_blocks = False  # True for sUSD
    yield try_blocks


# whether or not we should try a test donation of our rewards token to make sure the strategy handles them correctly
# if you want to bother with whale and amount below, this needs to be true
@pytest.fixture(scope="session")
def test_donation():
    test_donation = False
    yield test_donation


@pytest.fixture(scope="session")
def rewards_whale(accounts):
    # SNX whale: 0x8D6F396D210d385033b348bCae9e4f9Ea4e045bD, >600k SNX
    # SPELL whale: 0x46f80018211D5cBBc988e853A8683501FCA4ee9b, >10b SPELL
    # ANGLE whale: 0x2Fc443960971e53FD6223806F0114D5fAa8C7C4e, 11.6m ANGLE
    yield accounts.at("0x2Fc443960971e53FD6223806F0114D5fAa8C7C4e", force=True)


@pytest.fixture(scope="session")
def rewards_amount():
    rewards_amount = 10_000_000e18
    # SNX 50_000e18
    # SPELL 1_000_000e18
    # ANGLE 10_000_000e18
    yield rewards_amount


# whether or not a strategy is clonable. if true, don't forget to update what our cloning function is called in test_cloning.py
@pytest.fixture(scope="session")
def is_clonable():
    is_clonable = False  # any live strategy is a clone, so we don't test cloning on it
    yield is_clonable


# whether or not a strategy has ever had rewards, even if they are zero currently. essentially checking if the infra is there for rewards.
@pytest.fixture(scope="session")
def rewards_template():
    rewards_template = False
    yield rewards_template


# this is whether our pool currently has extra reward emissions (SNX, SPELL, etc)
@pytest.fixture(scope="session")
def has_rewards():
    has_rewards = False
    yield has_rewards


# if our curve gauge deposits aren't tokenized (older pools), we can't as easily do some tests and we skip them
@pytest.fixture(scope="session")
def gauge_is_not_tokenized():
    gauge_is_not_tokenized = False
    yield gauge_is_not_tokenized


# use this to test our strategy in case there are no profits
@pytest.fixture(scope="session")
def no_profit():
    no_profit = False
    yield no_profit


# use this when we might lose a few wei on conversions between want and another deposit token
# generally this will always be true if no_profit is true, even for curve/convex since we can lose a wei converting
@pytest.fixture(scope="session")
def is_slippery(no_profit):
    is_slippery = False
    if no_profit:
        is_slippery = True
    yield is_slippery


# use this to set the standard amount of time we sleep between harvests.
# generally 1 day, but can be less if dealing with smaller windows (oracles) or longer if we need to trigger weekly earnings.
@pytest.fixture(scope="session")
def sleep_time():
    hour = 3600

    # change this one right here
    hours_to_sleep = 24

    sleep_time = hour * hours_to_sleep
    yield sleep_time


################################################ UPDATE THINGS ABOVE HERE ################################################

# Only worry about changing things above this line, unless you want to make changes to the vault or strategy.
# ----------------------------------------------------------------------- #

if chain_used == 1:  # mainnet

    ########################################## FACTORY TESTING CONTRACTS BELOW ##########################################

    @pytest.fixture(scope="module")
    def live_spell_strat(trade_factory, ymechs_safe):
        strategy = Contract("0xeDB4B647524FC2B9985019190551b197c6AB6C5c")
        trade_factory.grantRole(
            trade_factory.STRATEGY(), strategy, {"from": ymechs_safe}
        )
        yield strategy

    @pytest.fixture(scope="module")
    def live_yfi_strat(trade_factory, ymechs_safe):
        network.gas_limit(6_000_000)
        # network.gas_price(0)
        # network.max_fee(0)
        # network.priority_fee(0)
        # , "allow_revert": True
        strategy = Contract("0xa04947059831783C561e59A43B93dCB5bEE7cab2")

        trade_factory.grantRole(
            trade_factory.STRATEGY(), strategy, {"from": ymechs_safe}
        )
        yield strategy

    @pytest.fixture(scope="session")
    def dai():
        yield Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")

    @pytest.fixture(scope="session")
    def weth(interface):
        yield interface.ERC20("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    @pytest.fixture(scope="session")
    def uniswap_router(Contract):
        yield Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

    @pytest.fixture(scope="session")
    def fxs(Contract):
        yield Contract("0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0")

    @pytest.fixture(scope="session")
    def curve_zapper(Contract):
        yield Contract("0xA79828DF1850E8a3A3064576f380D90aECDD3359")

    @pytest.fixture(scope="session")
    def trade_factory():
        # yield Contract("0xBf26Ff7C7367ee7075443c4F95dEeeE77432614d")
        yield Contract("0x99d8679bE15011dEAD893EB4F5df474a4e6a8b29")

    @pytest.fixture(scope="session")
    def new_trade_factory():
        # yield Contract("0xBf26Ff7C7367ee7075443c4F95dEeeE77432614d")
        yield Contract("0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b")

    @pytest.fixture(scope="session")
    def ymechs_safe():
        yield Contract("0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6")

    @pytest.fixture(scope="session")
    def multicall_swapper(interface):
        yield interface.MultiCallOptimizedSwapper(
            # "0xceB202F25B50e8fAF212dE3CA6C53512C37a01D2"
            "0xB2F65F254Ab636C96fb785cc9B4485cbeD39CDAA"
        )

    @pytest.fixture(scope="session")
    def keeper_contract(KeeperWrapper):
        yield KeeperWrapper.at("0x256e6a486075fbAdbB881516e9b6b507fd082B5D")

    @pytest.fixture(scope="session")
    def other_gauge(Contract):
        yield Contract("0xa9A9BC60fc80478059A83f516D5215185eeC2fc0")

    @pytest.fixture(scope="session")
    def ymechs_safe():
        yield Contract("0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6")

    @pytest.fixture(scope="session")
    def test_vault():  # DOLA-FRAXBP
        yield Contract("0xd395DEC4F1733ff09b750D869eEfa7E0D37C3eE6")

    @pytest.fixture(scope="session")
    def test_gauge():  # DOLA-FRAXBP
        yield Contract("0xBE266d68Ce3dDFAb366Bb866F4353B6FC42BA43c")

    @pytest.fixture(scope="session")
    def frax_booster():
        yield Contract("0x569f5B842B5006eC17Be02B8b94510BA8e79FbCa")

    @pytest.fixture(scope="session")
    def steth_gauge():
        yield Contract("0x182B723a58739a9c974cFDB385ceaDb237453c28")

    @pytest.fixture(scope="session")
    def steth_lp():
        yield Contract("0x06325440D014e39736583c165C2963BA99fAf14E")

    ########################################## FACTORY TESTING CONTRACTS ABOVE ##########################################

    @pytest.fixture(scope="session")
    def sushi_router():  # use this to check our allowances
        yield Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")

    # all contracts below should be able to stay static based on the pid
    @pytest.fixture(scope="session")
    def booster():  # this is the deposit contract
        yield Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")

    @pytest.fixture(scope="session")
    def voter():
        yield Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")

    @pytest.fixture(scope="session")
    def convexToken():
        yield Contract("0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B")

    @pytest.fixture(scope="session")
    def crv():
        yield Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")

    @pytest.fixture(scope="session")
    def other_vault_strategy():
        yield Contract("0x8423590CD0343c4E18d35aA780DF50a5751bebae")

    @pytest.fixture(scope="session")
    def curve_registry():
        yield Contract("0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5")

    @pytest.fixture(scope="session")
    def curve_cryptoswap_registry():
        yield Contract("0x4AacF35761d06Aa7142B9326612A42A2b9170E33")

    @pytest.fixture(scope="session")
    def healthCheck():
        yield Contract("0xDDCea799fF1699e98EDF118e0629A974Df7DF012")

    @pytest.fixture(scope="session")
    def farmed():
        # this is the token that we are farming and selling for more of our want.
        yield Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")

    @pytest.fixture(scope="session")
    def token(pid, booster):
        # this should be the address of the ERC-20 used by the strategy/vault
        token_address = booster.poolInfo(pid)[0]
        yield Contract(token_address)

    @pytest.fixture(scope="session")
    def cvxDeposit(booster, pid):
        # this should be the address of the convex deposit token
        cvx_address = booster.poolInfo(pid)[1]
        yield Contract(cvx_address)

    @pytest.fixture(scope="session")
    def rewardsContract(pid, booster):
        rewardsContract = booster.poolInfo(pid)[3]
        yield Contract(rewardsContract)

    # gauge for the curve pool
    @pytest.fixture(scope="session")
    def gauge(pid, booster):
        gauge = booster.poolInfo(pid)[2]
        yield Contract(gauge)

    # curve deposit pool
    @pytest.fixture(scope="session")
    def pool(token, curve_registry, curve_cryptoswap_registry, old_pool):
        if old_pool == ZERO_ADDRESS:
            if curve_registry.get_pool_from_lp_token(token) == ZERO_ADDRESS:
                if (
                    curve_cryptoswap_registry.get_pool_from_lp_token(token)
                    == ZERO_ADDRESS
                ):
                    poolContract = token
                else:
                    poolAddress = curve_cryptoswap_registry.get_pool_from_lp_token(
                        token
                    )
                    poolContract = Contract(poolAddress)
            else:
                poolAddress = curve_registry.get_pool_from_lp_token(token)
                poolContract = Contract(poolAddress)
        else:
            poolContract = Contract(old_pool)
        yield poolContract

    @pytest.fixture(scope="session")
    def gasOracle():
        yield Contract("0x1E7eFAbF282614Aa2543EDaA50517ef5a23c868b")

    # Define any accounts in this section
    # for live testing, governance is the strategist MS; we will update this before we endorse
    # normal gov is ychad, 0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52
    @pytest.fixture(scope="session")
    def gov(accounts):
        yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)

    @pytest.fixture(scope="session")
    def strategist_ms(accounts):
        # like governance, but better
        yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

    # set all of these accounts to SMS as well, just for testing
    @pytest.fixture(scope="session")
    def keeper(accounts):
        yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

    @pytest.fixture(scope="session")
    def rewards(accounts):
        yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

    @pytest.fixture(scope="session")
    def guardian(accounts):
        yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

    @pytest.fixture(scope="session")
    def management(accounts):
        yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

    @pytest.fixture(scope="session")
    def strategist(accounts):
        yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

    @pytest.fixture(scope="session")
    def deployer(accounts):
        yield accounts.at("0xC6387E937Bcef8De3334f80EDC623275d42457ff", force=True)

    @pytest.fixture(scope="session")
    def convex_template(
        StrategyConvexFactoryClonable,
        new_trade_factory,
        test_vault,
        strategist,
        booster,
        convexToken,
        test_pid,
    ):
        # deploy our convex template
        convex_template = StrategyConvexFactoryClonable.at(
            "0x8bbf215c4a8bEf276292f8e276782Dfe9Cf01917"
        )
        print("\nConvex Template deployed:", convex_template)

        yield convex_template

    @pytest.fixture(scope="session")
    def curve_template(
        StrategyCurveBoostedFactoryClonable,
        new_trade_factory,
        test_vault,
        strategist,
        test_gauge,
        new_proxy,
    ):
        # deploy our curve template
        curve_template = StrategyCurveBoostedFactoryClonable.at(
            "0x9B4B3DBCE6A2c7d65bFE3679bA2512fca39bB526"
        )
        print("Curve Template deployed:", curve_template)

        yield curve_template

    @pytest.fixture(scope="session")
    def frax_template(
        StrategyConvexFraxFactoryClonable,
        new_trade_factory,
        test_vault,
        strategist,
        frax_booster,
        test_staking_address,
        test_frax_pid,
    ):
        frax_template = StrategyConvexFraxFactoryClonable.at(
            "0x78883A75c058557Cc74b773c6E96150DB4B01aAf"
        )

        print("Frax Template deployed:", frax_template)
        yield frax_template

    @pytest.fixture(scope="session")
    def curve_global(
        CurveGlobal,
        strategist,
        new_registry,
        gov,
        convex_template,
        curve_template,
        frax_template,
    ):
        # deploy our factory
        curve_global = CurveGlobal.at("0x21b1FC8A52f179757bf555346130bF27c0C2A17A")

        print("Curve factory deployed:", curve_global)
        yield curve_global

    @pytest.fixture(scope="session")
    def new_proxy(StrategyProxy, gov):
        # deploy our new strategy proxy
        strategy_proxy = Contract("0xda18f789a1D9AD33E891253660Fcf1332d236b29")

        print("New Strategy Proxy deployed:", strategy_proxy)
        yield strategy_proxy

    @pytest.fixture(scope="session")
    def new_registry():
        # deploy our new vault registry, point it to our old vault registry and release registry
        new_registry = Contract("0xaF1f5e1c19cB68B30aAD73846eFfDf78a5863319")
        print("New Vault Registry deployed:", new_registry)

        yield new_registry

    @pytest.fixture(scope="session")
    def old_proxy():
        yield Contract("0x4694507Ca1023194eA3Ca4428F99EDEd7Ab2b919")

    @pytest.fixture(scope="session")
    def old_registry():
        yield Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")

    @pytest.fixture(scope="session")
    def vault(pm, gov, rewards, guardian, management, token, chain, vault_address):
        Vault = pm(config["dependencies"][0]).Vault
        vault = Vault.at(vault_address)
        yield vault

    # replace the first value with the name of your strategy
    # since we do lots of on-chain updates here, make the scope function instead of module
    @pytest.fixture(scope="function")
    def strategy(
        StrategyConvexFactoryClonable,
        StrategyCurveBoostedFactoryClonable,
        StrategyConvexFraxFactoryClonable,
        strategist,
        keeper,
        gov,
        accounts,
        token,
        healthCheck,
        chain,
        pid,
        gasOracle,
        strategist_ms,
        gauge,
        which_strategy,
        new_proxy,
        voter,
        new_trade_factory,
        convexToken,
        booster,
        frax_booster,
        frax_pid,
        staking_address,
        vault,
        has_rewards,
        rewards_token,
        deployer,
        curve_global,
        new_registry,
    ):
        # all of the remaining steps left
        # transfer registry ownership
        release_registry = Contract("0x7Cb5ABEb0de8f6f46a27329B9eF54CE10E47F1e2")
        release_registry.transferOwnership(gov, {"from": deployer})
        new_registry.transferOwnership(gov, {"from": deployer})
        print("Registry ownership transferred")
        dinobots = "0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6"

        # set owner of factory to yChad
        curve_global.setOwner(gov, {"from": deployer})
        curve_global.acceptOwner({"from": gov})
        print("Factory ownership transferred")

        # add LDO tokens to strategy proxy
        new_proxy.approveRewardToken(rewards_token, {"from": gov})
        print("LDO approved on strategy proxy")

        # update guardian and gov on all vaults
        for x in range(new_registry.numTokens()):
            underlying = new_registry.tokens(x)
            vault_to_update = Contract(new_registry.latestVault(underlying))
            vault_to_update.acceptGovernance({"from": gov})
            vault_to_update.setGuardian(dinobots, {"from": gov})
        print("Updated gov and guardian for this vaults")

        # migrate our curve strategies
        # set baseFeeOracle, voter, and health check on new strategies
        for x in range(new_registry.numTokens()):
            underlying = new_registry.tokens(x)
            vault_to_update = Contract(new_registry.latestVault(underlying))
            assert vault_to_update.governance() == gov.address
            replacement_curve_strats = [
                "0xaBec96AC9CdC6863446657431DD32F73445E80b1",
                "0xE1c43Cee52dd10543622E429516194F818efc390",
                "0x9BD0D6C7a1f770d513dD9b7dde45e56c8ed81002",
                "0xB73fa254f47cE89Af8B7fC9919C38D62F12bbb5B",
                "0x9D7CD0041ABd91f281E282Db3fba7A9Db9E4cC8b",
                "0x837963994Ff184143e4D448E6Fc685d92Cee639B",
                "0x3b1a64058020954a74550271eA6b0aD2019EF806",
                "0x8D7686Dfca05a555c1E692C6dF79DFFaF188FD45",
                "0x9430A2501e5f2Cd66741375baAbB9576E8FB5f48",
            ]

            for strat in replacement_curve_strats:
                strategy = StrategyCurveBoostedFactoryClonable.at(strat)
                if vault_to_update.address != strategy.vault():
                    continue
                else:
                    old_strategy = vault_to_update.withdrawalQueue(1)
                    vault_to_update.migrateStrategy(old_strategy, strat, {"from": gov})
                    new_curve = StrategyCurveBoostedFactoryClonable.at(strat)
                    assert (
                        new_curve.tradeFactory()
                        == "0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b"
                    )
                    new_curve.setVoter(voter, {"from": gov})
                    new_curve.setBaseFeeOracle(gasOracle, {"from": gov})
                    new_curve.setHealthCheck(healthCheck, {"from": gov})
        print("Strats migrated and updated")

        # update strategy proxy
        replacement_curve_strats = [
            "0xaBec96AC9CdC6863446657431DD32F73445E80b1",
            "0xE1c43Cee52dd10543622E429516194F818efc390",
            "0x9BD0D6C7a1f770d513dD9b7dde45e56c8ed81002",
            "0xB73fa254f47cE89Af8B7fC9919C38D62F12bbb5B",
            "0x9D7CD0041ABd91f281E282Db3fba7A9Db9E4cC8b",
            "0x837963994Ff184143e4D448E6Fc685d92Cee639B",
            "0x3b1a64058020954a74550271eA6b0aD2019EF806",
            "0x8D7686Dfca05a555c1E692C6dF79DFFaF188FD45",
            "0x9430A2501e5f2Cd66741375baAbB9576E8FB5f48",
        ]

        for strat in replacement_curve_strats:
            # replace our strategy on our strategy proxy
            strategy_contract = StrategyCurveBoostedFactoryClonable.at(strat)
            gauge_to_add = strategy_contract.gauge()
            new_proxy.approveStrategy(gauge_to_add, strat, {"from": gov})
        print("Strategies updated on strategy proxy")

        # update trade handler on all strategies except curve
        for x in range(new_registry.numTokens()):
            underlying = new_registry.tokens(x)
            vault_to_update = Contract(new_registry.latestVault(underlying))
            convex_strategy = Contract(vault_to_update.withdrawalQueue(0))
            convex_strategy.updateTradeFactory(new_trade_factory, {"from": gov})
            assert (
                convex_strategy.tradeFactory()
                == "0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b"
            )
            frax_strategy = vault_to_update.withdrawalQueue(2)
            if frax_strategy != ZERO_ADDRESS:
                frax_strategy = Contract(vault_to_update.withdrawalQueue(2))
                frax_strategy.updateTradeFactory(new_trade_factory, {"from": gov})
                assert (
                    frax_strategy.tradeFactory()
                    == "0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b"
                )
        print("Trade Handlers updated")

        # add LDO tokens to new stETH curve strategy
        steth_strat = StrategyCurveBoostedFactoryClonable.at(
            "0xaBec96AC9CdC6863446657431DD32F73445E80b1"
        )
        steth_strat.updateRewards([rewards_token], {"from": gov})
        steth_strat.updateTradeFactory(steth_strat.tradeFactory(), {"from": gov})
        print("LDO added to stETH Curve strategy")

        # only test one strategy at a time, and give it all of our debt
        if which_strategy == 0:  # convex
            print("Testing a live convex strategy")
            strategy = StrategyConvexFactoryClonable.at(vault.withdrawalQueue(0))
            vault.updateStrategyDebtRatio(vault.withdrawalQueue(1), 0, {"from": gov})
            if vault.withdrawalQueue(2) != ZERO_ADDRESS:
                vault.updateStrategyDebtRatio(
                    vault.withdrawalQueue(2), 0, {"from": gov}
                )
            vault.updateStrategyDebtRatio(
                vault.withdrawalQueue(0), 10_000, {"from": gov}
            )
        elif which_strategy == 1:  # curve
            print("Testing a live curve strategy")
            strategy = StrategyCurveBoostedFactoryClonable.at(vault.withdrawalQueue(1))
            vault.updateStrategyDebtRatio(vault.withdrawalQueue(0), 0, {"from": gov})
            if vault.withdrawalQueue(2) != ZERO_ADDRESS:
                vault.updateStrategyDebtRatio(
                    vault.withdrawalQueue(2), 0, {"from": gov}
                )
            vault.updateStrategyDebtRatio(
                vault.withdrawalQueue(1), 10_000, {"from": gov}
            )
        else:  # frax
            print("Testing a live frax strategy")
            strategy = StrategyConvexFraxFactoryClonable.at(vault.withdrawalQueue(2))
            vault.updateStrategyDebtRatio(vault.withdrawalQueue(0), 0, {"from": gov})
            vault.updateStrategyDebtRatio(vault.withdrawalQueue(1), 0, {"from": gov})
            vault.updateStrategyDebtRatio(
                vault.withdrawalQueue(2), 10_000, {"from": gov}
            )

        # turn our oracle into testing mode by setting the provider to 0x00, should default to true
        gasOracle = Contract(strategy.baseFeeOracle())
        oracle_gov = accounts.at(gasOracle.governance(), force=True)
        gasOracle.setBaseFeeProvider(ZERO_ADDRESS, {"from": oracle_gov})
        assert strategy.isBaseFeeAcceptable() == True
        chain.sleep(1)
        chain.mine(1)

        yield strategy
