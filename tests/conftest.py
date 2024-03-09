import pytest
from brownie import web3, config, Contract, ZERO_ADDRESS, chain, interface, accounts
from eth_abi import encode_single
import requests
import os

# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass


# set this for if we want to use tenderly or not; mostly helpful because with brownie.reverts fails in tenderly forks.
# note that for curve factory we should use tenderly with 2/3 factory tests
use_tenderly = False

# tests to run; last 4 should be done with pool that we don't have a vault for yet, and also need tenderly
# brownie test -s
# brownie test tests/factory/test_curve_global.py::test_vault_deployment -s --gas
# brownie test tests/factory/test_curve_global.py::test_permissioned_vault -s --gas
# brownie test tests/strategies/test_simple_harvest.py -s --gas
# brownie test tests/strategies/test_yswaps.py -s --gas


# use this to set what chain we use. 1 for ETH, 250 for fantom, 10 optimism, 42161 arbitrum
chain_used = 100


################################################## TENDERLY DEBUGGING ##################################################

# change autouse to True if we want to use this fork to help debug tests
@pytest.fixture(scope="session", autouse=use_tenderly)
def tenderly_fork(web3, chain):
    # Get env variables
    TENDERLY_ACCESS_KEY = os.environ.get("TENDERLY_ACCESS_KEY")
    TENDERLY_USER = os.environ.get("TENDERLY_USER")
    TENDERLY_PROJECT = os.environ.get("TENDERLY_PROJECT")

    # Construct request
    url = f"https://api.tenderly.co/api/v1/account/{TENDERLY_USER}/project/{TENDERLY_PROJECT}/fork"
    headers = {"X-Access-Key": str(TENDERLY_ACCESS_KEY)}
    data = {
        "network_id": str(chain.id),
    }

    # Post request
    response = requests.post(url, json=data, headers=headers)

    # Parse response
    fork_id = response.json()["simulation_fork"]["id"]

    # Set provider to your new Tenderly fork
    fork_rpc_url = f"https://rpc.tenderly.co/fork/{fork_id}"
    tenderly_provider = web3.HTTPProvider(fork_rpc_url, {"timeout": 600})
    web3.provider = tenderly_provider
    print(
        f"https://dashboard.tenderly.co/{TENDERLY_USER}/{TENDERLY_PROJECT}/fork/{fork_id}"
    )


################################################ UPDATE THINGS BELOW HERE ################################################

#################### FIXTURES BELOW NEED TO BE ADJUSTED FOR THIS REPO ####################

# for curve/balancer, we will pull this automatically, so comment this out here (token below in unique fixtures section)
@pytest.fixture(scope="session")
def token():
    token_address = "0x0CA1C1eC4EBf3CC67a9f545fF90a3795b318cA4a"  # this should be the address of the ERC-20 used by the strategy/vault ()
    yield interface.IERC20(token_address)


# gauge for the curve pool
@pytest.fixture(scope="session")
def gauge():
    yield Contract("0xd91770E868c7471a9585d1819143063A40c54D00")


@pytest.fixture(scope="session")
def whale(accounts, amount, token):
    # Totally in it for the tech
    # Update this with a large holder of your want token (the largest EOA holder of LP)
    # use the FRAX-USDC pool for now
    whale = accounts.at("0x10E4597fF93cbee194F4879f8f1d54a370DB6969", force=True)
    # yPRISMA-f LP (gauge) 0xf1ce237a1E1a88F6e289CD7998A826138AEB30b0, cvxPRISMA gauge: 0x13E58C7b1147385D735a06D14F0456E54C2dEBC8
    # cvxCRV new gauge (already deployed, only use for strategy testing): 0xfB18127c1471131468a1AaD4785c19678e521D86, 47m tokens,
    # stETH: 0x65eaB5eC71ceC12f38829Fbb14C98ce4baD28C46, 1700 tokens, frax-usdc: 0xE57180685E3348589E9521aa53Af0BCD497E884d, DOLA pool, 23.6m tokens,
    # 0x2932a86df44Fe8D2A706d8e9c5d51c24883423F5 frxETH 78k tokens, eCFX 0xeCb456EA5365865EbAb8a2661B0c503410e9B347 (only use for factory deployment testing)
    # 0x8605dc0C339a2e7e85EEA043bD29d42DA2c6D784 eUSD-FRAXBP, 13m, 0x96424E6b5eaafe0c3B36CA82068d574D44BE4e3c crvUSD-FRAX, 88.5k
    # 0x4E21418095d32d15c6e2B96A9910772613A50d50 frxETH-ng 40k (gauge, not perfect for strat testing but good for factory testing)
    # GNOSIS CHAIN 0x10E4597fF93cbee194F4879f8f1d54a370DB6969, EURe ~900k
    if token.balanceOf(whale) < 2 * amount:
        raise ValueError(
            "Our whale needs more funds. Find another whale or reduce your amount variable."
        )
    yield whale


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="session")
def amount(token):
    amount = (
        10_000 * 10 ** token.decimals()
    )  # 500k for cvxCRV, 300 for stETH, 50k for frax-usdc, 5k for frxETH, 5 eCFX, 5_000 eUSD-FRAXBP, 10_000 crvUSD-FRAX, 100 frxETH-ng, 5000 yPRISMA, 100k cvxPRISMA, 10_000 EURe
    yield amount


@pytest.fixture(scope="session")
def profit_whale(accounts, profit_amount, token):
    # ideally not the same whale as the main whale, or else they will lose money
    profit_whale = accounts.at("0x8E8bc9e262B8d2d1c24d25eeD0d03bF0412Da18b", force=True)
    # 0x109B3C39d675A2FF16354E116d080B94d238a7c9 (only use for strategy testing), new cvxCRV 5100 tokens, stETH: 0x82a7E64cdCaEdc0220D0a4eB49fDc2Fe8230087A, 500 tokens
    # frax-usdc 0x8fdb0bB9365a46B145Db80D0B1C5C5e979C84190, BUSD pool, 17m tokens, 0x38a93e70b0D8343657f802C1c3Fdb06aC8F8fe99 frxETH 28 tokens
    # eCFX 0xeCb456EA5365865EbAb8a2661B0c503410e9B347 (only use for factory deployment testing), 0xf83deAdE1b0D2AfF07700C548a54700a082388bE eUSD-FRAXBP 188
    # 0x97283C716f72b6F716D6a1bf6Bd7C3FcD840027A crvUSD-FRAX, 24.5k, 0x4E21418095d32d15c6e2B96A9910772613A50d50 frxETH-ng
    # 0x6806D62AAdF2Ee97cd4BCE46BF5fCD89766EF246 yPRISMA LP, cvxPRISMA LP 0x5C21F24e5772f52DEfA4BB37f662120c50597b4f
    # GNOSIS CHAIN 0x8E8bc9e262B8d2d1c24d25eeD0d03bF0412Da18b, EURe 500
    if token.balanceOf(profit_whale) < 5 * profit_amount:
        raise ValueError(
            "Our profit whale needs more funds. Find another whale or reduce your profit_amount variable."
        )
    yield profit_whale


@pytest.fixture(scope="session")
def profit_amount(token):
    profit_amount = (
        50 * 10 ** token.decimals()
    )  # 1k for FRAX-USDC, 2 for stETH, 100 for cvxCRV, 4 for frxETH, 1 eCFX, 25 for eUSD, 50 crvUSD-FRAX, 1 frxETH-ng, 25 yPRISMA, 100 cvxPRISMA, EURe 50
    yield profit_amount


@pytest.fixture(scope="session")
def to_sweep(crv):
    # token we can sweep out of strategy (use CRV)
    yield crv


# set address if already deployed, use ZERO_ADDRESS if not
@pytest.fixture(scope="session")
def vault_address():
    vault_address = ZERO_ADDRESS
    yield vault_address


# if our vault is pre-0.4.3, this will affect a few things
@pytest.fixture(scope="session")
def old_vault():
    old_vault = False
    yield old_vault


# this is the name we want to give our strategy
@pytest.fixture(scope="session")
def strategy_name():
    strategy_name = "StrategyConvexfrxETH"
    yield strategy_name


# this is the name of our strategy in the .sol file
@pytest.fixture(scope="session")
def contract_name(
    StrategyConvexFactoryClonable,
    StrategyConvexFraxFactoryClonable,
    StrategyCurveNoBoostClonable,
    StrategyPrismaConvexFactoryClonable,
    # StrategyPrismaCurveFactoryClonable,
    which_strategy,
):
    if which_strategy == 0:
        contract_name = StrategyConvexFactoryClonable
    elif which_strategy == 1:
        contract_name = StrategyCurveNoBoostClonable
    elif which_strategy == 2:
        contract_name = StrategyPrismaConvexFactoryClonable
    # elif which_strategy == 3:
    #     contract_name = StrategyPrismaCurveFactoryClonable
    else:
        contract_name = StrategyConvexFraxFactoryClonable
    yield contract_name


# if our strategy is using ySwaps, then we need to donate profit to it from our profit whale
@pytest.fixture(scope="session")
def use_yswaps():
    use_yswaps = True
    yield use_yswaps


# whether or not a strategy is clonable. if true, don't forget to update what our cloning function is called in test_cloning.py
@pytest.fixture(scope="session")
def is_clonable():
    is_clonable = True
    yield is_clonable


# use this to test our strategy in case there are no profits
@pytest.fixture(scope="session")
def no_profit():
    no_profit = True
    yield no_profit


# use this when we might lose a few wei on conversions between want and another deposit token (like router strategies)
# generally this will always be true if no_profit is true, even for curve/convex since we can lose a wei converting
@pytest.fixture(scope="session")
def is_slippery(no_profit):
    is_slippery = False  # set this to true or false as needed
    if no_profit:
        is_slippery = True
    yield is_slippery


# use this to set the standard amount of time we sleep between harvests.
# generally 1 day, but can be less if dealing with smaller windows (oracles) or longer if we need to trigger weekly earnings.
@pytest.fixture(scope="session")
def sleep_time():
    hour = 3600

    # change this one right here
    hours_to_sleep = 12

    sleep_time = hour * hours_to_sleep
    yield sleep_time


#################### FIXTURES ABOVE NEED TO BE ADJUSTED FOR THIS REPO ####################

#################### FIXTURES BELOW SHOULDN'T NEED TO BE ADJUSTED FOR THIS REPO ####################


@pytest.fixture(scope="session")
def tests_using_tenderly():
    yes_or_no = use_tenderly
    yield yes_or_no


# by default, pytest uses decimals, but in solidity we use uints, so 10 actually equals 10 wei (1e-17 for most assets, or 1e-6 for USDC/USDT)
@pytest.fixture(scope="session")
def RELATIVE_APPROX(token):
    approx = 10
    print("Approx:", approx, "wei")
    yield approx


# use this to set various fixtures that differ by chain
if chain_used == 1:  # mainnet

    @pytest.fixture(scope="session")
    def gov():
        yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)

    @pytest.fixture(scope="session")
    def health_check():
        yield interface.IHealthCheck("0xddcea799ff1699e98edf118e0629a974df7df012")

    @pytest.fixture(scope="session")
    def base_fee_oracle():
        yield interface.IBaseFeeOracle("0xfeCA6895DcF50d6350ad0b5A8232CF657C316dA7")

    # set all of the following to SMS, just simpler
    @pytest.fixture(scope="session")
    def management():
        yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

    @pytest.fixture(scope="session")
    def rewards(management):
        yield management

    @pytest.fixture(scope="session")
    def guardian(management):
        yield management

    @pytest.fixture(scope="session")
    def strategist(management):
        yield management

    @pytest.fixture(scope="session")
    def keeper(management):
        yield management

    @pytest.fixture(scope="session")
    def trade_factory():
        yield Contract("0xcADBA199F3AC26F67f660C89d43eB1820b7f7a3b")

    @pytest.fixture(scope="session")
    def keeper_wrapper():
        yield Contract("0x0D26E894C2371AB6D20d99A65E991775e3b5CAd7")

    @pytest.fixture(scope="session")
    def prisma_vault():
        yield Contract("0x06bDF212C290473dCACea9793890C5024c7Eb02c")

    @pytest.fixture(scope="session")
    def prisma_curve_factory():
        yield Contract("0x2664a7B123e7E6b5CC5cf6a76Cf65e409BD1569F")

    @pytest.fixture(scope="session")
    def prisma_convex_factory():
        yield Contract("0x3dA992F4694d1a1624c32CAFb5E57fE75B4Bc867")

    @pytest.fixture(scope="session")
    def yprisma():
        yield Contract("0xe3668873D944E4A949DA05fc8bDE419eFF543882")
elif chain_used == 100:  # GNO

    @pytest.fixture(scope="session")
    def gov():
        yield accounts.at("0x22eAe41c7Da367b9a15e942EB6227DF849Bb498C", force=True)

    @pytest.fixture(scope="session")
    def health_check():
        yield interface.IHealthCheck("0x9C59c9bde73Af993c2313590C90305F372F4e8db")

    @pytest.fixture(scope="session")
    def base_fee_oracle():
        yield interface.IBaseFeeOracle("0xb10072d2B48fD9C8a1114F4b7f9E5E3f61509127")

    # set all of the following to SMS, just simpler
    @pytest.fixture(scope="session")
    def management():
        yield accounts.at("0xFB4464a18d18f3FF439680BBbCE659dB2806A187", force=True)

    @pytest.fixture(scope="session")
    def rewards(management):
        yield management

    @pytest.fixture(scope="session")
    def guardian(management):
        yield management

    @pytest.fixture(scope="session")
    def strategist(management):
        yield management

    @pytest.fixture(scope="session")
    def keeper(management):
        yield management

    @pytest.fixture(scope="session")
    def trade_factory():
        yield Contract("0x67a5802068f9E1ee03821Be0cD7f46D04f4dF33A")

    @pytest.fixture(scope="session")
    def keeper_wrapper():
        yield Contract("0xA45CB3222815e96a023341B2f340A78A7C69FCE9")


@pytest.fixture(scope="module")
def vault(pm, gov, rewards, guardian, management, token, vault_address):
    if vault_address == ZERO_ADDRESS:
        Vault = pm(config["dependencies"][0]).Vault
        vault = guardian.deploy(Vault)
        vault.initialize(token, gov, rewards, "", "", guardian)
        vault.setDepositLimit(2**256 - 1, {"from": gov})
        vault.setManagement(management, {"from": gov})
    else:
        vault = interface.IVaultFactory045(vault_address)
    yield vault


#################### FIXTURES ABOVE SHOULDN'T NEED TO BE ADJUSTED FOR THIS REPO ####################

#################### FIXTURES BELOW LIKELY NEED TO BE ADJUSTED FOR THIS REPO ####################


@pytest.fixture(scope="session")
def target(which_strategy):
    # whatever we want it to be—this is passed into our harvest function as a target
    yield which_strategy


# this should be a strategy from a different vault to check during migration
@pytest.fixture(scope="session")
def other_strategy():
    yield Contract("0x3bCa26c3D49Af712ac74Af82De27665A610999E2")


# replace the first value with the name of your strategy
# since we do lots of on-chain updates here, make the scope function instead of module
@pytest.fixture(scope="module")
def strategy(
    strategist,
    keeper,
    vault,
    gov,
    management,
    health_check,
    contract_name,
    strategy_name,
    base_fee_oracle,
    vault_address,
    trade_factory,
    which_strategy,
    pid,
    gauge,
    new_proxy,
    voter,
    convex_token,
    booster,
    has_rewards,
    rewards_token,
    frax_booster,
    frax_pid,
    staking_address,
    prisma_convex_factory,
    prisma_curve_factory,
    yprisma,
    prisma_vault,
):
    if which_strategy == 0:  # convex
        strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            pid,
            10_000 * 1e6,
            25_000 * 1e6,
            booster,
            convex_token,
        )
    elif which_strategy == 1:  # curve
        strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            # new_proxy, COMMENT OUT FOR GNOSIS CHAIN
            gauge,
        )
        #voter.setStrategy(new_proxy.address, {"from": gov})
        #print("New Strategy Proxy setup")
    elif which_strategy == 2:  # prisma convex
        strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            10_000 * 1e6,
            25_000 * 1e6,
            prisma_vault,
            prisma_convex_factory.getDeterministicAddress(
                pid
            ),  # This looks up the prisma receiver for the pool
        )
    # elif which_strategy == 3:   # prisma curve
    #     strategy = gov.deploy(
    #         contract_name,
    #         vault,
    #         trade_factory,
    #         10_000 * 1e6,
    #         25_000 * 1e6,
    #         prisma_vault,
    #         prisma_curve_factory.getDeterministicAddress(gauge.address), # This looks up the prisma receiver for the pool
    #     )
    else:  # frax
        strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            frax_pid,
            staking_address,
            10_000 * 1e6,
            25_000 * 1e6,
            frax_booster,
        )

    strategy.setKeeper(keeper, {"from": gov})

    # set our management fee to zero so it doesn't mess with our profit checking
    vault.setManagementFee(0, {"from": gov})
    vault.setPerformanceFee(0, {"from": gov})

    # we will be migrating on our live vault instead of adding it directly
    if which_strategy == 0:  # convex
        # earmark rewards if we are using a convex strategy
        booster.earmarkRewards(pid, {"from": gov})
        chain.sleep(1)
        chain.mine(1)

        vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 0, {"from": gov})
        print("New Vault, Convex Strategy")
        chain.sleep(1)
        chain.mine(1)

        # this is the same for new or existing vaults
        strategy.setHarvestTriggerParams(
            90000e6, 150000e6, strategy.checkEarmark(), {"from": gov}
        )
    elif which_strategy == 1:  # Curve
        vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 0, {"from": gov})
        print("New Vault, Curve Strategy")
        chain.sleep(1)
        chain.mine(1)
        
        # add rewards direct for gnosis chain
        strategy.updateRewards([rewards_token], {"from": gov})
        
        # approve reward token on our strategy proxy if needed
#         if has_rewards:
#             # first, add our rewards token to our strategy, then use that for our strategy proxy
#             strategy.updateRewards([rewards_token], {"from": gov})
#             new_proxy.approveRewardToken(strategy.rewardsTokens(0), {"from": gov})
# 
#         # approve our new strategy on the proxy
#         new_proxy.approveStrategy(strategy.gauge(), strategy, {"from": gov})
#         assert new_proxy.strategies(gauge.address) == strategy.address
#         assert voter.strategy() == new_proxy.address
    elif which_strategy == 2:  # Prisma Convex
        vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 0, {"from": gov})
        print("New Vault, Prisma Convex Strategy")

        # this is the same for new or existing vaults
        strategy.setHarvestTriggerParams(90000e6, 150000e6, {"from": gov})
    elif which_strategy == 3:  # Prisma Curve
        vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 0, {"from": gov})
        print("New Vault, Prisma Curve Strategy")
        chain.sleep(1)
        # chain.mine(1)
    else:  # frax
        vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 0, {"from": gov})
        print("New Vault, Frax Strategy")
        chain.sleep(1)
        chain.mine(1)

        # this is the same for new or existing vaults
        strategy.setHarvestTriggerParams(90000e6, 150000e6, {"from": gov})

        # for testing, let's deposit anything above 1e18
        strategy.setDepositParams(1e18, 5_000_000e18, False, {"from": gov})

    # turn our oracle into testing mode by setting the provider to 0x00, then forcing true
    strategy.setBaseFeeOracle(base_fee_oracle, {"from": management})
    base_fee_oracle.setBaseFeeProvider(ZERO_ADDRESS, {"from": management})
    base_fee_oracle.setManualBaseFeeBool(True, {"from": management})
    assert strategy.isBaseFeeAcceptable() == True

    yield strategy


#################### FIXTURES ABOVE LIKELY NEED TO BE ADJUSTED FOR THIS REPO ####################

####################         PUT UNIQUE FIXTURES FOR THIS REPO BELOW         ####################

# put our test pool's convex pid here
# if you change this, make sure to update addresses/values below too
@pytest.fixture(scope="session")
def pid():
    pid = 258  # 25 stETH, 157 cvxCRV new, 128 frxETH-ETH (do for frax), eCFX 160, eUSD-FRAXBP 156, crvUSD-FRAX 187, FRAX-USDC 100, frxETH-ng 219
    # 258 cvxPRISMA LP, 260 yPRISMA LP
    yield pid


@pytest.fixture(scope="session")
def prisma_receiver(
    pid, gauge, prisma_convex_factory, prisma_curve_factory, which_strategy
):
    address = ZERO_ADDRESS
    if which_strategy == 2:
        address = prisma_convex_factory.getDeterministicAddress(pid)
    elif which_strategy == 3:
        address = prisma_curve_factory.getDeterministicAddress(gauge)
    yield Contract(address)


# put our pool's frax pid here
@pytest.fixture(scope="session")
def frax_pid():
    frax_pid = 44  # 27 DOLA-FRAXBP, 9 FRAX-USDC, 36 frxETH-ETH, 44 eUSD-FRAXBP, crvUSD-FRAX 49, frxETH-ng 63
    yield frax_pid


# put our pool's staking address here
@pytest.fixture(scope="session")
def staking_address():
    staking_address = "0x4c9AD8c53d0a001E7fF08a3E5E26dE6795bEA5ac"
    #  0xa537d64881b84faffb9Ae43c951EEbF368b71cdA frxETH, 0x963f487796d54d2f27bA6F3Fbe91154cA103b199 FRAX-USDC,
    # 0xE7211E87D60177575846936F2123b5FA6f0ce8Ab DOLA-FRAXBP, 0x4c9AD8c53d0a001E7fF08a3E5E26dE6795bEA5ac eUSD-FRAXBP
    # 0x67CC47cF82785728DD5E3AE9900873a074328658 crvUSD-FRAX, 0xB4fdD7444E1d86b2035c97124C46b1528802DA35 frxETH-ng
    yield staking_address


# this is only used for deploying our template—should be for an existing vault
@pytest.fixture(scope="session")
def template_pid():
    template_pid = 115  # 115 DOLA FRAXBP, 100 FRAX-USDC
    yield template_pid


# this is only used for deploying our template—should be for an existing vault
@pytest.fixture(scope="session")
def template_frax_pid():
    template_frax_pid = 27  # 27 DOLA-FRAXBP, 9 FRAX-USDC
    yield template_frax_pid


# this is only used for deploying our template—should be for an existing vault
@pytest.fixture(scope="session")
def template_staking_address():
    template_staking_address = "0xE7211E87D60177575846936F2123b5FA6f0ce8Ab"  # 0x963f487796d54d2f27bA6F3Fbe91154cA103b199 FRAX-USDC, 0xE7211E87D60177575846936F2123b5FA6f0ce8Ab DOLA-FRAXBP
    yield template_staking_address


@pytest.fixture(scope="session")
def which_strategy():
    # must be 0 or 1 for vanilla convex and curve
    # prisma convex: 2
    # prisma curve: 3
    # Only test 4 (Frax) for pools that actually have frax.
    which_strategy = 1
    yield which_strategy


# curve deposit pool for old pools, set to ZERO_ADDRESS otherwise
@pytest.fixture(scope="session")
def old_pool():
    old_pool = ZERO_ADDRESS
    yield old_pool


# if our curve gauge deposits aren't tokenized (older pools), we can't as easily do some tests and we skip them
@pytest.fixture(scope="session")
def gauge_is_not_tokenized():
    gauge_is_not_tokenized = False
    yield gauge_is_not_tokenized


# this is the address of our rewards token
@pytest.fixture(scope="session")
def rewards_token():  # OGN 0x8207c1FfC5B6804F6024322CcF34F29c3541Ae26, SPELL 0x090185f2135308BaD17527004364eBcC2D37e5F6
    # SNX 0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F, ANGLE 0x31429d1856aD1377A8A0079410B297e1a9e214c2, LDO 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32
    # GNOSIS CHAIN wstETH 0x6C76971f98945AE98dD7d4DFcA8711ebea946eA6
    yield Contract("0x6C76971f98945AE98dD7d4DFcA8711ebea946eA6")


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
    # LDO whale: 0x28C6c06298d514Db089934071355E5743bf21d60, 7.6m LDO
    yield accounts.at("0x28C6c06298d514Db089934071355E5743bf21d60", force=True)


@pytest.fixture(scope="session")
def rewards_amount():
    rewards_amount = 50_000e18
    # SNX 50_000e18
    # SPELL 1_000_000e18
    # ANGLE 10_000_000e18
    # LDO 50_000e18
    yield rewards_amount


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


########## ADDRESSES TO UPDATE FOR BALANCER VS CURVE ##########
