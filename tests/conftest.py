import pytest
from brownie import web3, config, Contract, ZERO_ADDRESS, chain, interface, accounts
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
chain_used = 1


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


@pytest.fixture(scope="session")
def which_strategy():
    # vanilla convex: 0
    # curve: 1
    # prisma convex: 2
    # fxn convex: 3
    # Only test 4 (Frax) for pools that actually have frax.
    which_strategy = 2
    yield which_strategy


@pytest.fixture(scope="session")
def token_string():
    id_number = 0
    token_string = "ERROR"
    if id_number == 0:
        token_string = "yPRISMA"
    elif id_number == 1:
        token_string = "cvxPRISMA"
    elif id_number == 2:
        token_string = "cvxCRV New"  # working 7/8/24
    elif id_number == 3:
        token_string = "stETH"
    elif id_number == 4:
        token_string = "FRAX-USDC"
    elif id_number == 5:
        token_string = "frxETH"
    elif id_number == 6:
        token_string = "eCFX"
    elif id_number == 7:
        token_string = "eUSD-FRAXBP"
    elif id_number == 8:
        token_string = "crvUSD-FRAX"
    elif id_number == 9:
        token_string = "frxETH-ng"
    elif id_number == 10:
        token_string = "GHO-fxUSD"  # working 7/8/24
    elif id_number == 11:
        token_string = "CurveLend-WETH"  # working 7/8/24
    yield token_string


####### GENERALLY SHOULDN'T HAVE TO CHANGE ANYTHING BELOW HERE UNLESS UPDATING/ADDING WHALE/PROFIT AMOUNTS OR ADDRESSES


# for curve/balancer, we will pull this automatically via convex_token. set to False to manually set address
@pytest.fixture(scope="session")
def token(token_address_via_convex):
    use_convex_token = True
    if use_convex_token:
        yield token_address_via_convex
    else:
        token_address = ""
        yield interface.IERC20(token_address)


@pytest.fixture(scope="session")
def whale_accounts():
    whale_accounts = {
        "yPRISMA": "0xf1ce237a1E1a88F6e289CD7998A826138AEB30b0",  # gauge
        "cvxPRISMA": "0x13E58C7b1147385D735a06D14F0456E54C2dEBC8",  # gauge
        "cvxCRV New": "0xfB18127c1471131468a1AaD4785c19678e521D86",  # gauge, 55M tokens
        "stETH": "0x65eaB5eC71ceC12f38829Fbb14C98ce4baD28C46",  # 1700 tokens
        "FRAX-USDC": "0xE57180685E3348589E9521aa53Af0BCD497E884d",  # DOLA Pool, 23.6M tokens
        "frxETH": "0x2932a86df44Fe8D2A706d8e9c5d51c24883423F5",  # 78k tokens
        "eCFX": "0xeCb456EA5365865EbAb8a2661B0c503410e9B347",  # only use for factory deployment testing
        "eUSD-FRAXBP": "0x8605dc0C339a2e7e85EEA043bD29d42DA2c6D784",  # 13M
        "crvUSD-FRAX": "0x96424E6b5eaafe0c3B36CA82068d574D44BE4e3c",  # 88.5k
        "frxETH-ng": "0x4E21418095d32d15c6e2B96A9910772613A50d50",  # 40k (gauge, not perfect for strat testing but good for factory testing)
        "GHO-fxUSD": "0xec303960CF0456aC304Af45C0aDDe34921a10Fdf",  # 5M, gauge
        "CurveLend-WETH": "0xF3F6D6d412a77b680ec3a5E35EbB11BbEC319739",  # 7.5B, gauge (1000x)
        "NEW": "",  #
    }
    yield whale_accounts


@pytest.fixture(scope="session")
def whale(accounts, amount, token, whale_accounts, token_string):
    # Totally in it for the tech
    # Update this with a large holder of your want token (the largest EOA holder of LP)
    whale = accounts.at(whale_accounts[token_string], force=True)
    if token.balanceOf(whale) < 2 * amount:
        raise ValueError(
            "Our whale needs more funds. Find another whale or reduce your amount variable."
        )
    yield whale


@pytest.fixture(scope="session")
def whale_amounts():
    whale_amounts = {
        "yPRISMA": 5_000,
        "cvxPRISMA": 100_000,
        "cvxCRV New": 500_000,
        "stETH": 300,
        "FRAX-USDC": 50_000,
        "frxETH": 5_000,
        "eCFX": 5,
        "eUSD-FRAXBP": 5_000,
        "crvUSD-FRAX": 10_000,
        "frxETH-ng": 100,
        "GHO-fxUSD": 1_000,
        "CurveLend-WETH": 100_000_000,  # $100k of crvUSD
        "NEW": 0,
    }
    yield whale_amounts


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="session")
def amount(token, whale_amounts, token_string):
    amount = whale_amounts[token_string] * 10 ** token.decimals()
    yield amount


@pytest.fixture(scope="session")
def profit_whale_accounts():
    profit_whale_accounts = {
        "yPRISMA": "0x6806D62AAdF2Ee97cd4BCE46BF5fCD89766EF246",
        "cvxPRISMA": "0x154001A2F9f816389b2F6D9E07563cE0359D813D",
        "cvxCRV New": "0x109B3C39d675A2FF16354E116d080B94d238a7c9",  # (only use for strategy testing), new cvxCRV 5100 tokens
        "stETH": "0x82a7E64cdCaEdc0220D0a4eB49fDc2Fe8230087A",  # 500 tokens
        "FRAX-USDC": "0x8fdb0bB9365a46B145Db80D0B1C5C5e979C84190",  # BUSD Pool, 17M tokens
        "frxETH": "0x38a93e70b0D8343657f802C1c3Fdb06aC8F8fe99",  # 28 tokens
        "eCFX": "0xeCb456EA5365865EbAb8a2661B0c503410e9B347",  # only use for factory deployment testing
        "eUSD-FRAXBP": "0xf83deAdE1b0D2AfF07700C548a54700a082388bE",  # 188
        "crvUSD-FRAX": "0x97283C716f72b6F716D6a1bf6Bd7C3FcD840027A",  # 24.5k
        "frxETH-ng": "0x4E21418095d32d15c6e2B96A9910772613A50d50",
        "GHO-fxUSD": "0xfefB84273A4DEdd40D242f4C007190DE21C9E39e",
        "CurveLend-WETH": "0x4Ec3fa22540f841657197440FeE70B5967465AaA",  # 5M, but actually $5k since each is 1000x
        "NEW": "",  #
    }
    yield profit_whale_accounts


@pytest.fixture(scope="session")
def profit_whale(accounts, profit_amount, token, profit_whale_accounts, token_string):
    # ideally not the same whale as the main whale, or else they will lose money
    profit_whale = accounts.at(profit_whale_accounts[token_string], force=True)
    if token.balanceOf(profit_whale) < 5 * profit_amount:
        raise ValueError(
            "Our profit whale needs more funds. Find another whale or reduce your profit_amount variable."
        )
    yield profit_whale


@pytest.fixture(scope="session")
def profit_amounts():
    profit_amounts = {
        "yPRISMA": 25,
        "cvxPRISMA": 100,
        "cvxCRV New": 100,
        "stETH": 2,
        "FRAX-USDC": 1_000,
        "frxETH": 4,
        "eCFX": 1,
        "eUSD-FRAXBP": 25,
        "crvUSD-FRAX": 50,
        "frxETH-ng": 1,
        "GHO-fxUSD": 50,
        "CurveLend-WETH": 500_000,  # $500 of crvUSD
        "NEW": 0,
    }
    yield profit_amounts


@pytest.fixture(scope="session")
def profit_amount(token, profit_amounts, token_string):
    profit_amount = profit_amounts[token_string] * 10 ** token.decimals()
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
    StrategyCurveBoostedFactoryClonable,
    StrategyPrismaConvexFactoryClonable,
    StrategyConvexFxnFactoryClonable,
    which_strategy,
):
    if which_strategy == 0:
        contract_name = StrategyConvexFactoryClonable
    elif which_strategy == 1:
        contract_name = StrategyCurveBoostedFactoryClonable
    elif which_strategy == 2:
        contract_name = StrategyPrismaConvexFactoryClonable
    elif which_strategy == 3:
        contract_name = StrategyConvexFxnFactoryClonable
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
    no_profit = False
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

    @pytest.fixture(scope="session")
    def fxn():
        yield Contract("0x365AccFCa291e7D3914637ABf1F7635dB165Bb09")


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
    yprisma,
    prisma_vault,
    fxn_pid,
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
            new_proxy,
            gauge,
        )
        voter.setStrategy(new_proxy.address, {"from": gov})
        print("New Strategy Proxy setup")
    elif which_strategy == 2:  # prisma convex
        strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            prisma_vault,
            prisma_convex_factory.getDeterministicAddress(
                pid
            ),  # This looks up the prisma receiver for the pool
        )
    elif which_strategy == 3:  # FXN Convex
        strategy = gov.deploy(
            contract_name,
            vault,
            trade_factory,
            fxn_pid,
        )
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

    if which_strategy == 0:  # convex
        # convex implemented a change where you might need to wait until next epoch to earmark to prevent over-harvesting
        # chain.sleep(86400 * 7)
        # booster.earmarkRewards(pid, {"from": gov})
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

        # approve reward token on our strategy proxy if needed
        if has_rewards:
            # first, add our rewards token to our strategy, then use that for our strategy proxy
            strategy.updateRewards([rewards_token], {"from": gov})
            new_proxy.approveRewardToken(strategy.rewardsTokens(0), {"from": gov})

        # approve our new strategy on the proxy (if we want to test an existing want, then add more logic here)
        new_proxy.approveStrategy(strategy.gauge(), strategy, {"from": gov})
        assert new_proxy.strategies(gauge.address) == strategy.address
        assert voter.strategy() == new_proxy.address
    elif which_strategy == 2:  # Prisma Convex
        vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 0, {"from": gov})
        print("New Vault, Prisma Convex Strategy")

        # this is the same for new or existing vaults
        strategy.setHarvestTriggerParams(90000e6, 150000e6, {"from": gov})

        # set up our claim params; default to always claim
        strategy.setClaimParams(False, True, {"from": gov})
    elif which_strategy == 3:  # FXN Convex
        vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 0, {"from": gov})
        print("New Vault, Convex FXN Strategy")
        chain.sleep(1)
        chain.mine()
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


@pytest.fixture(scope="session")
def pid_list():
    pid_list = {
        "yPRISMA": 260,
        "cvxPRISMA": 258,
        "cvxCRV New": 157,
        "stETH": 25,
        "FRAX-USDC": 100,
        "frxETH": 128,  # do for frax
        "eCFX": 160,
        "eUSD-FRAXBP": 156,
        "crvUSD-FRAX": 187,
        "frxETH-ng": 219,
        "GHO-fxUSD": 316,  # we don't really need this for FXN strategies, but set to use for token lookup
        "CurveLend-WETH": 365,
        "NEW": 0,
    }
    yield pid_list


# put our test pool's convex pid here
# if you change this, make sure to update addresses/values below too
@pytest.fixture(scope="session")
def pid(pid_list, token_string):
    pid = pid_list[token_string]
    yield pid


@pytest.fixture(scope="session")
def prisma_receiver(pid, gauge, prisma_convex_factory, which_strategy):
    address = ZERO_ADDRESS
    if which_strategy == 2:
        address = prisma_convex_factory.getDeterministicAddress(pid)
        yield Contract(address)
    else:
        yield address


@pytest.fixture(scope="session")
def frax_pid_list():
    frax_pid_list = {
        "yPRISMA": 1_000,  # 1_000 is null
        "cvxPRISMA": 1_000,
        "cvxCRV New": 1_000,
        "stETH": 1_000,
        "FRAX-USDC": 9,
        "frxETH": 36,
        "eCFX": 1_000,
        "eUSD-FRAXBP": 44,
        "crvUSD-FRAX": 49,
        "frxETH-ng": 63,
        "GHO-fxUSD": 1_000,
        "CurveLend-WETH": 1_000,
        "NEW": 0,
    }
    yield frax_pid_list


# put our pool's frax pid here
@pytest.fixture(scope="session")
def frax_pid(frax_pid_list, token_string):
    frax_pid = frax_pid_list[token_string]
    yield frax_pid


@pytest.fixture(scope="session")
def fxn_pid_list():
    fxn_pid_list = {
        "yPRISMA": 1_000,  # 1_000 is null
        "cvxPRISMA": 1_000,
        "cvxCRV New": 1_000,
        "stETH": 1_000,
        "FRAX-USDC": 1_000,
        "frxETH": 1_000,
        "eCFX": 1_000,
        "eUSD-FRAXBP": 1_000,
        "crvUSD-FRAX": 1_000,
        "frxETH-ng": 1_000,
        "GHO-fxUSD": 14,
        "CurveLend-WETH": 1_000,
        "NEW": 0,
    }
    yield fxn_pid_list


# put our pool's fxn pid here
@pytest.fixture(scope="session")
def fxn_pid(fxn_pid_list, token_string):
    fxn_pid = fxn_pid_list[token_string]
    yield fxn_pid


@pytest.fixture(scope="session")
def staking_address_list():
    staking_address_list = {
        "yPRISMA": "NULL",
        "cvxPRISMA": "NULL",
        "cvxCRV New": "NULL",
        "stETH": "NULL",
        "FRAX-USDC": "0x963f487796d54d2f27bA6F3Fbe91154cA103b199",
        "frxETH": "0xa537d64881b84faffb9Ae43c951EEbF368b71cdA",
        "eCFX": "NULL",
        "eUSD-FRAXBP": "0x4c9AD8c53d0a001E7fF08a3E5E26dE6795bEA5ac",
        "crvUSD-FRAX": "0x67CC47cF82785728DD5E3AE9900873a074328658",
        "frxETH-ng": "0xB4fdD7444E1d86b2035c97124C46b1528802DA35",
        "GHO-fxUSD": "NULL",
        "CurveLend-WETH": "NULL",
        "NEW": "NULL",
    }
    yield staking_address_list


# our pool's staking address
@pytest.fixture(scope="session")
def staking_address(token_string, staking_address_list):
    staking_address = staking_address_list[token_string]
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


# all contracts below should be able to stay static based on the pid
@pytest.fixture(scope="session")
def booster():  # this is the deposit contract
    yield Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")


@pytest.fixture(scope="session")
def frax_booster():
    yield Contract("0x2B8b301B90Eb8801f1eEFe73285Eec117D2fFC95")


@pytest.fixture(scope="session")
def voter():
    yield Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")


@pytest.fixture(scope="session")
def crv():
    yield Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")


@pytest.fixture(scope="session")
def crv_whale():
    yield accounts.at("0xF977814e90dA44bFA03b6295A0616a897441aceC", force=True)


@pytest.fixture(scope="session")
def fxn_whale():
    yield accounts.at("0x26B2ec4E02ebe2F54583af25b647b1D619e67BbF", force=True)


@pytest.fixture(scope="session")
def convex_token():
    yield Contract("0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B")


@pytest.fixture(scope="session")
def fxs():
    yield Contract("0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0")


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
def other_gauge(Contract):
    yield Contract("0xa9A9BC60fc80478059A83f516D5215185eeC2fc0")


@pytest.fixture(scope="session")
def template_vault():  # DOLA-FRAXBP
    yield Contract("0xd395DEC4F1733ff09b750D869eEfa7E0D37C3eE6")


@pytest.fixture(scope="session")
def template_gauge():  # DOLA-FRAXBP
    yield Contract("0xBE266d68Ce3dDFAb366Bb866F4353B6FC42BA43c")


@pytest.fixture(scope="session")
def legacy_gauge():  # something with no factory vault but a legacy one, EURS-USDC
    yield Contract("0x65CA7Dc5CB661fC58De57B1E1aF404649a27AD35")


# curve deposit pool
@pytest.fixture(scope="session")
def pool(token, curve_registry, curve_cryptoswap_registry, old_pool):
    if old_pool == ZERO_ADDRESS:
        if curve_registry.get_pool_from_lp_token(token) == ZERO_ADDRESS:
            if curve_cryptoswap_registry.get_pool_from_lp_token(token) == ZERO_ADDRESS:
                poolContract = token
            else:
                poolAddress = curve_cryptoswap_registry.get_pool_from_lp_token(token)
                poolContract = Contract(poolAddress)
        else:
            poolAddress = curve_registry.get_pool_from_lp_token(token)
            poolContract = Contract(poolAddress)
    else:
        poolContract = Contract(old_pool)
    yield poolContract


@pytest.fixture(scope="session")
def token_address_via_convex(pid, booster):
    # this should be the address of the ERC-20 used by the strategy/vault
    token_address = booster.poolInfo(pid)[0]
    yield Contract(token_address)


@pytest.fixture(scope="session")
def cvx_deposit(booster, pid):
    # this should be the address of the convex deposit token
    cvx_address = booster.poolInfo(pid)[1]
    yield Contract(cvx_address)


@pytest.fixture(scope="session")
def rewards_contract(pid, booster):
    rewards_contract = booster.poolInfo(pid)[3]
    yield Contract(rewards_contract)


# gauge for the curve pool
@pytest.fixture(scope="session")
def gauge(pid, booster):
    gauge = booster.poolInfo(pid)[2]
    yield interface.ICurveGaugeV6(gauge)


@pytest.fixture(scope="function")
def convex_template(
    StrategyConvexFactoryClonable,
    trade_factory,
    template_vault,
    gov,
    booster,
    convex_token,
    template_pid,
):
    # deploy our convex template
    convex_template = gov.deploy(
        StrategyConvexFactoryClonable,
        template_vault,
        trade_factory,
        template_pid,
        10_000 * 1e6,
        25_000 * 1e6,
        booster,
        convex_token,
    )
    print("\nConvex Template deployed:", convex_template)

    yield convex_template


@pytest.fixture(scope="function")
def curve_template(
    StrategyCurveBoostedFactoryClonable,
    trade_factory,
    template_vault,
    strategist,
    template_gauge,
    new_proxy,
    gov,
):
    # deploy our curve template
    curve_template = gov.deploy(
        StrategyCurveBoostedFactoryClonable,
        template_vault,
        trade_factory,
        new_proxy,
        template_gauge,
    )
    print("Curve Template deployed:", curve_template)

    yield curve_template


@pytest.fixture(scope="function")
def frax_template(
    StrategyConvexFraxFactoryClonable,
    trade_factory,
    template_vault,
    strategist,
    frax_booster,
    template_staking_address,
    template_frax_pid,
    gov,
):
    frax_template = gov.deploy(
        StrategyConvexFraxFactoryClonable,
        template_vault,
        trade_factory,
        template_frax_pid,
        template_staking_address,
        10_000 * 1e6,
        25_000 * 1e6,
        frax_booster,
    )

    print("Frax Template deployed:", frax_template)
    yield frax_template


@pytest.fixture(scope="session")
def curve_global(CurveGlobal):
    # deploy our factory
    curve_global = CurveGlobal.at("0x21b1FC8A52f179757bf555346130bF27c0C2A17A")
    print("Curve factory already deployed:", curve_global)
    yield curve_global


@pytest.fixture(scope="session")
def new_proxy():
    yield Contract("0x78eDcb307AC1d1F8F5Fd070B377A6e69C8dcFC34")


@pytest.fixture(scope="session")
def new_registry():
    yield Contract("0xaF1f5e1c19cB68B30aAD73846eFfDf78a5863319")
