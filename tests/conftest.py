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
@pytest.fixture(scope="session")
def pid():
    pid = 100  # 115 DOLA FRAXBP, 100 FRAX-USDC
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
    # must be 0, 1, or 2 for convex, curve, and frax
    which_strategy = 0
    yield which_strategy


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="session")
def amount():
    amount = 500_000e18  #
    yield amount


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="session")
def profit_amount():
    profit_amount = 5_000e18
    yield profit_amount


@pytest.fixture(scope="session")
def profit_whale(accounts, profit_amount, token):
    # Totally in it for the tech
    # Update this with a large holder of your want token (the largest EOA holder of LP)
    # use the FRAX-USDC pool for now
    profit_whale = accounts.at(
        "0x8fdb0bB9365a46B145Db80D0B1C5C5e979C84190", force=True
    )  # 0x8fdb0bB9365a46B145Db80D0B1C5C5e979C84190, BUSD pool, 17m tokens
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
    )  # 0xE57180685E3348589E9521aa53Af0BCD497E884d, DOLA pool, 23.6m tokens
    if token.balanceOf(whale) < 2 * amount:
        raise ValueError(
            "Our whale needs more funds. Find another whale or reduce your amount variable."
        )
    yield whale


# set address if already deployed, use ZERO_ADDRESS if not
@pytest.fixture(scope="session")
def vault_address():
    vault_address = ZERO_ADDRESS
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
    # SNX 0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F, ANGLE 0x31429d1856aD1377A8A0079410B297e1a9e214c2
    yield Contract("0x31429d1856aD1377A8A0079410B297e1a9e214c2")


# sUSD gauge uses blocks instead of seconds to determine rewards, so this needs to be true for that to test if we're earning
@pytest.fixture(scope="session")
def try_blocks():
    try_blocks = False  # True for sUSD
    yield try_blocks


# whether or not we should try a test donation of our rewards token to make sure the strategy handles them correctly
# if you want to bother with whale and amount below, this needs to be true
@pytest.fixture(scope="session")
def test_donation():
    test_donation = True
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
    is_clonable = True
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


# this is whether our strategy is convex or not
@pytest.fixture(scope="session")
def is_convex():
    is_convex = True
    yield is_convex


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
    hours_to_sleep = 6

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
    def new_registry(interface):
        yield interface.IRegistry("0x78f73705105A63e06B932611643E0b210fAE93E9")

    @pytest.fixture(scope="session")
    def weth(interface):
        yield interface.ERC20("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")

    @pytest.fixture(scope="session")
    def uniswap_router(Contract):
        yield Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

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
        yield Contract("0xd6a8ae62f4d593DAf72E2D7c9f7bDB89AB069F06")

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

    @pytest.fixture(scope="module")
    def convex_template(
        CurveGlobal,
        StrategyConvexFactoryClonable,
        StrategyCurveBoostedFactoryClonable,
        StrategyConvexFraxFactoryClonable,
        new_trade_factory,
        test_vault,
        strategist,
        new_registry,
        gov,
        booster,
        convexToken,
        test_gauge,
        accounts,
        test_pid,
        frax_booster,
        which_strategy,
    ):
        # deploy our convex template
        convex_template = strategist.deploy(
            StrategyConvexFactoryClonable,
            test_vault,
            new_trade_factory,
            test_pid,
            10_000 * 1e6,
            25_000 * 1e6,
            booster,
            convexToken,
        )
        print("\nConvex Template:", convex_template)

        yield convex_template

    @pytest.fixture(scope="module")
    def curve_template(
        CurveGlobal,
        StrategyConvexFactoryClonable,
        StrategyCurveBoostedFactoryClonable,
        StrategyConvexFraxFactoryClonable,
        new_trade_factory,
        test_vault,
        strategist,
        new_registry,
        gov,
        booster,
        convexToken,
        test_gauge,
        new_proxy,
        accounts,
        pid,
        frax_booster,
        which_strategy,
    ):
        # deploy our curve template
        curve_template = strategist.deploy(
            StrategyCurveBoostedFactoryClonable,
            test_vault,
            new_trade_factory,
            new_proxy,
            test_gauge,
            10_000 * 1e6,
            25_000 * 1e6,
        )
        print("Curve Template:", curve_template)

        yield curve_template

    @pytest.fixture(scope="module")
    def frax_template(
        CurveGlobal,
        StrategyConvexFactoryClonable,
        StrategyCurveBoostedFactoryClonable,
        StrategyConvexFraxFactoryClonable,
        new_trade_factory,
        test_vault,
        strategist,
        new_registry,
        gov,
        booster,
        convexToken,
        test_gauge,
        accounts,
        test_pid,
        frax_booster,
        which_strategy,
        test_staking_address,
        test_frax_pid,
    ):
        frax_template = strategist.deploy(
            StrategyConvexFraxFactoryClonable,
            test_vault,
            new_trade_factory,
            test_frax_pid,
            test_staking_address,
            10_000 * 1e6,
            25_000 * 1e6,
            frax_booster,
        )

        print("Frax Template:", frax_template)

        cloned_strategy = frax_template.cloneStrategyConvexFrax(
            test_vault,
            test_vault.management(),
            test_vault.rewards(),
            frax_template.keeper(),
            new_trade_factory,
            27,  # this is using values for DOLX-FRAXBP since it's on that vault
            "0xE7211E87D60177575846936F2123b5FA6f0ce8Ab",  # this is using values for DOLX-FRAXBP since it's on that vault
            10_000 * 1e6,
            25_000 * 1e6,
            frax_booster,
        )
        print("Successfully cloned", cloned_strategy.return_value)
        clone_contract = StrategyConvexFraxFactoryClonable.at(
            cloned_strategy.return_value
        )
        print("Cloned strategy:", clone_contract.name())

        yield frax_template

    @pytest.fixture(scope="module")
    def curve_global(
        CurveGlobal,
        strategist,
        new_registry,
        gov,
        accounts,
        convex_template,
        curve_template,
        frax_template,
    ):
        # before we deploy our first vault, we need to update to the latest release (0.4.5)
        release_registry = Contract(new_registry.releaseRegistry())
        template_vault_045 = "0xBb1988ab99d4839Af8b6c94853B890307770E48B"
        release_registry_owner = accounts.at(release_registry.owner(), force=True)
        release_registry.newRelease(
            template_vault_045, {"from": release_registry_owner}
        )

        # then, deploy our factory
        factory = strategist.deploy(
            CurveGlobal,
            new_registry,
            convex_template,
            curve_template,
            frax_template,
            gov,
        )

        # once our factory is deployed, setup the factory from gov
        registry_owner = accounts.at(new_registry.owner(), force=True)
        new_registry.setApprovedVaultsOwner(factory, True, {"from": registry_owner})
        new_registry.setRole(factory, False, True, {"from": registry_owner})

        yield factory

    @pytest.fixture(scope="module")
    def new_proxy(StrategyProxy, gov):
        # deploy our new strategy proxy
        strategy_proxy = gov.deploy(StrategyProxy)
        yield strategy_proxy

    @pytest.fixture(scope="session")
    def old_proxy():
        yield Contract("0xA420A63BbEFfbda3B147d0585F1852C358e2C152")

    @pytest.fixture(scope="module")
    def vault(pm, gov, rewards, guardian, management, token, chain, vault_address):
        Vault = pm(config["dependencies"][0]).Vault
        vault = guardian.deploy(Vault)
        vault.initialize(token, gov, rewards, "", "", guardian)
        vault.setDepositLimit(2**256 - 1, {"from": gov})
        vault.setManagement(management, {"from": gov})
        chain.sleep(1)
        chain.mine(1)
        yield vault

    # replace the first value with the name of your strategy
    @pytest.fixture(scope="module")
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
        Contract,
        pid,
        gasOracle,
        strategist_ms,
        gauge,
        which_strategy,
        old_proxy,
        voter,
        new_trade_factory,
        convexToken,
        booster,
        frax_booster,
        frax_pid,
        staking_address,
        vault,
    ):

        if which_strategy == 0:  # convex
            strategy = strategist.deploy(
                StrategyConvexFactoryClonable,
                vault,
                new_trade_factory,
                pid,
                10_000 * 1e6,
                25_000 * 1e6,
                booster,
                convexToken,
            )
        elif which_strategy == 1:  # curve
            strategy = strategist.deploy(
                StrategyCurveBoostedFactoryClonable,
                vault,
                new_trade_factory,
                old_proxy,
                gauge,
                10_000 * 1e6,
                25_000 * 1e6,
            )
        else:  # frax
            strategy = strategist.deploy(
                StrategyConvexFraxFactoryClonable,
                vault,
                new_trade_factory,
                frax_pid,
                staking_address,
                10_000 * 1e6,
                25_000 * 1e6,
                frax_booster,
            )

        strategy.setKeeper(keeper, {"from": gov})

        # set our management fee to zero so it doesn't mess with our profit checking
        vault.setManagementFee(0, {"from": gov})

        # we will be migrating on our live vault instead of adding it directly
        if which_strategy == 0:
            # earmark rewards if we are using a convex strategy
            booster.earmarkRewards(pid, {"from": gov})
            chain.sleep(1)
            chain.mine(1)

            vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 1_000, {"from": gov})
            print("New Vault, Convex Strategy")
            chain.sleep(1)
            chain.mine(1)

            # this is the same for new or existing vaults
            strategy.setHarvestTriggerParams(90000e6, 150000e6, False, {"from": gov})
        elif which_strategy == 1:
            vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 1_000, {"from": gov})
            print("New Vault, Curve Strategy")
            chain.sleep(1)
            chain.mine(1)

            # approve our new strategy on the proxy
            old_proxy.approveStrategy(strategy.gauge(), strategy, {"from": gov})

        # turn our oracle into testing mode by setting the provider to 0x00, should default to true
        strategy.setBaseFeeOracle(gasOracle, {"from": strategist_ms})
        gasOracle = Contract(strategy.baseFeeOracle())
        oracle_gov = accounts.at(gasOracle.governance(), force=True)
        gasOracle.setBaseFeeProvider(ZERO_ADDRESS, {"from": oracle_gov})
        strategy.setHealthCheck(healthCheck, {"from": gov})
        assert strategy.isBaseFeeAcceptable() == True

        # set up custom params and setters
        strategy.setMaxReportDelay(86400 * 21, {"from": gov})

        yield strategy

    @pytest.fixture(scope="module")
    def factory_vault(
        StrategyConvexFactoryClonable,
        StrategyCurveBoostedFactoryClonable,
        StrategyConvexFraxFactoryClonable,
        strategist,
        keeper,
        ymechs_safe,
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
        gasOracle,
        new_registry,
        strategist_ms,
        gauge,
        which_strategy,
        proxy,
        voter,
    ):

        print("Factory address: ", curve_global)
        print("Gauge: ", gauge)

        # update the strategy on our voter
        voter.setStrategy(proxy.address, {"from": gov})

        # set our factory address on the strategy proxy
        proxy.setFactory(curve_global.address, {"from": gov})

        # check if our current gauge has a strategy for it, but mostly just do this to update our proxy
        print(
            "Here is our strategy for the gauge (likely 0x000):",
            proxy.strategies(gauge),
        )

        # make sure we can create this vault permissionlessly
        assert curve_global.canCreateVaultPermissionlessly(gauge)

        tx = curve_global.createNewVaultsAndStrategies(gauge, {"from": strategist})
        vault_address = tx.events["NewAutomatedVault"]["vault"]
        vault = Contract(vault_address)
        print("Vault name:", vault.name())

        print("Vault endorsed:", vault_address)
        info = tx.events["NewAutomatedVault"]

        print("Here's our new vault created event:", info, "\n")

        if which_strategy == 0:  # convex
            strat = tx.events["NewAutomatedVault"]["convexStrategy"]
            strategy = StrategyConvexFactoryClonable.at(strat)
        elif which_strategy == 1:  # curve
            strat = tx.events["NewAutomatedVault"]["curveStrategy"]
            strategy = StrategyCurveBoostedFactoryClonable.at(strat)
        else:  # frax
            strat = tx.events["NewAutomatedVault"]["convexFraxStrategy"]
            strategy = StrategyConvexFraxFactoryClonable.at(strat)

        # daddy needs to accept gov on all new vaults
        vault.acceptGovernance({"from": gov})
        assert vault.governance() == gov.address

        # set all debtRatios to zero, then set to 10k for our strategy we want to test
        vault.updateStrategyDebtRatio(vault.withdrawalQueue(0), 0, {"from": gov})
        if vault.withdrawalQueue(1) != ZERO_ADDRESS:
            vault.updateStrategyDebtRatio(vault.withdrawalQueue(1), 0, {"from": gov})
        if vault.withdrawalQueue(2) != ZERO_ADDRESS:
            vault.updateStrategyDebtRatio(vault.withdrawalQueue(2), 0, {"from": gov})
        vault.updateStrategyDebtRatio(strategy, 10_000, {"from": gov})

        # turn our oracle into testing mode by setting the provider to 0x00, should default to true
        strategy.setBaseFeeOracle(gasOracle, {"from": strategist_ms})
        gasOracle = Contract(strategy.baseFeeOracle())
        oracle_gov = accounts.at(gasOracle.governance(), force=True)
        gasOracle.setBaseFeeProvider(ZERO_ADDRESS, {"from": oracle_gov})
        strategy.setHealthCheck(healthCheck, {"from": gov})
        assert strategy.isBaseFeeAcceptable() == True
