import pytest
from brownie import config, Contract, ZERO_ADDRESS, chain, interface, accounts
from eth_abi import encode_single
import requests
import os

# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    pass


# set this for if we want to use tenderly or not; mostly helpful because with brownie.reverts fails in tenderly forks.
# note that for curve factory we should use tenderly with 2/3 factory tests, and update our earned function as below unless
# we want to do each test individually with tenderly
use_tenderly = False

# because of the staticcall we now use, need to use tenderly when testing the strategy, unless we remove this function
# actually, easier just to comment out the _updateRewards() call in the constructor and then everything is cool
# to test the getEarnedTokens() fxn, we call in in test_simple_harvest

#
#     /// @notice Use this helper function to handle v1 and v2 Convex Frax stakingToken wrappers
#     /// @dev We use staticcall here, as on newer userVaults, earned is a write function.
#     /// @return tokenAddresses Array of our reward token addresses.
#     /// @return tokenAmounts Amounts of our corresponding reward tokens.
#     function getEarnedTokens()
#         public
#         view
#         returns (address[] memory tokenAddresses, uint256[] memory tokenAmounts)
#     {
# //         bytes memory data = abi.encodeWithSignature("earned()");
# //         (bool success, bytes memory returnBytes) = address(userVault)
# //             .staticcall(data);
# //         if (success) {
# //             (tokenAddresses, tokenAmounts) = abi.decode(
# //                 returnBytes,
# //                 (address[], uint256[])
# //             );
#         bool success = false;
#         if (success) {
#             (tokenAddresses, tokenAmounts) = userVault.earned();
#         } else {
#             tokenAmounts = stakingAddress.earned(address(userVault));
#             tokenAddresses = stakingAddress.getAllRewardTokens();
#         }
#     }

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

#################### FIXTURES BELOW NEED TO BE ADJUSTED FOR THIS REPO ####################

# for curve/balancer, we will pull this automatically, so comment this out here (token below in unique fixtures section)
# @pytest.fixture(scope="session")
# def token():
#     token_address = "0x6DEA81C8171D0bA574754EF6F8b412F2Ed88c54D"  # this should be the address of the ERC-20 used by the strategy/vault ()
#     yield interface.IERC20(token_address)


@pytest.fixture(scope="session")
def whale(accounts, amount, token):
    # Totally in it for the tech
    # Update this with a large holder of your want token (the largest EOA holder of LP)
    # use the FRAX-USDC pool for now
    whale = accounts.at(
        "0xE57180685E3348589E9521aa53Af0BCD497E884d", force=True
    )  # cvxCRV new gauge (already deployed, only use for strategy testing): 0xfB18127c1471131468a1AaD4785c19678e521D86, 47m tokens,
    # stETH: 0x65eaB5eC71ceC12f38829Fbb14C98ce4baD28C46, 1700 tokens, frax-usdc: 0xE57180685E3348589E9521aa53Af0BCD497E884d, DOLA pool, 23.6m tokens,
    # 0x2932a86df44Fe8D2A706d8e9c5d51c24883423F5 frxETH 78k tokens, eCFX 0xeCb456EA5365865EbAb8a2661B0c503410e9B347 (only use for factory deployment testing)
    # 0x8605dc0C339a2e7e85EEA043bD29d42DA2c6D784 eUSD-FRAXBP, 13m, 0xF4D36Cbf5fb6b3003e1f97E58E4a9122ee28B5F0 crvUSD-FRAX, 88.5k
    if token.balanceOf(whale) < 2 * amount:
        raise ValueError(
            "Our whale needs more funds. Find another whale or reduce your amount variable."
        )
    yield whale


# this is the amount of funds we have our whale deposit. adjust this as needed based on their wallet balance
@pytest.fixture(scope="session")
def amount(token):
    amount = (
        50_000 * 10 ** token.decimals()
    )  # 500k for cvxCRV, 300 for stETH, 50k for frax-usdc, 5k for frxETH, 5 eCFX, 5k eUSD-FRAXBP, 10k crvUSD-FRAX
    yield amount


@pytest.fixture(scope="session")
def profit_whale(accounts, profit_amount, token):
    # ideally not the same whale as the main whale, or else they will lose money
    profit_whale = accounts.at(
        "0x8fdb0bB9365a46B145Db80D0B1C5C5e979C84190", force=True
    )  # 0x109B3C39d675A2FF16354E116d080B94d238a7c9 (only use for strategy testing), new cvxCRV 5100 tokens, stETH: 0x82a7E64cdCaEdc0220D0a4eB49fDc2Fe8230087A, 500 tokens
    # frax-usdc 0x8fdb0bB9365a46B145Db80D0B1C5C5e979C84190, BUSD pool, 17m tokens, 0x38a93e70b0D8343657f802C1c3Fdb06aC8F8fe99 frxETH 28 tokens
    # eCFX 0xeCb456EA5365865EbAb8a2661B0c503410e9B347 (only use for factory deployment testing), 0xf83deAdE1b0D2AfF07700C548a54700a082388bE eUSD-FRAXBP 188
    # 0x97283C716f72b6F716D6a1bf6Bd7C3FcD840027A crvUSD-FRAX, 24.5k
    if token.balanceOf(profit_whale) < 5 * profit_amount:
        raise ValueError(
            "Our profit whale needs more funds. Find another whale or reduce your profit_amount variable."
        )
    yield profit_whale


@pytest.fixture(scope="session")
def profit_amount(token):
    profit_amount = (
        1_000 * 10 ** token.decimals()
    )  # 1k for FRAX-USDC, 2 for stETH, 100 for cvxCRV, 4 for frxETH, 1 eCFX, 25 for eUSD, 50 crvUSD-FRAX
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
    which_strategy,
):
    if which_strategy == 0:
        contract_name = StrategyConvexFactoryClonable
    elif which_strategy == 1:
        contract_name = StrategyCurveBoostedFactoryClonable
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

        # approve reward token on our strategy proxy if needed
        if has_rewards:
            # first, add our rewards token to our strategy, then use that for our strategy proxy
            strategy.updateRewards([rewards_token], {"from": gov})
            new_proxy.approveRewardToken(strategy.rewardsTokens(0), {"from": gov})

        # approve our new strategy on the proxy
        new_proxy.approveStrategy(strategy.gauge(), strategy, {"from": gov})
        assert new_proxy.strategies(gauge.address) == strategy.address
        assert voter.strategy() == new_proxy.address
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
    pid = 100  # 25 stETH, 157 cvxCRV new, 128 frxETH-ETH (do for frax), eCFX 160, eUSD-FRAXBP 156, crvUSD-FRAX 187, FRAX-USDC 100
    yield pid


# put our pool's frax pid here
@pytest.fixture(scope="session")
def frax_pid():
    frax_pid = (
        9  # 27 DOLA-FRAXBP, 9 FRAX-USDC, 36 frxETH-ETH, 44 eUSD-FRAXBP, crvUSD-FRAX 49
    )
    yield frax_pid


# put our pool's staking address here
@pytest.fixture(scope="session")
def staking_address():
    staking_address = "0x963f487796d54d2f27bA6F3Fbe91154cA103b199"
    #  0xa537d64881b84faffb9Ae43c951EEbF368b71cdA frxETH, 0x963f487796d54d2f27bA6F3Fbe91154cA103b199 FRAX-USDC,
    # 0xE7211E87D60177575846936F2123b5FA6f0ce8Ab DOLA-FRAXBP, 0x4c9AD8c53d0a001E7fF08a3E5E26dE6795bEA5ac eUSD-FRAXBP
    # 0x67CC47cF82785728DD5E3AE9900873a074328658 crvUSD-FRAX
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


# put our pool's convex pid here
@pytest.fixture(scope="session")
def which_strategy():
    # must be 0, 1, or 2 for convex, curve, and frax. Only test 2 (Frax) for pools that actually have frax.
    which_strategy = 2
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
def token(pid, booster):
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
    yield Contract(gauge)


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
    yield Contract("0xda18f789a1D9AD33E891253660Fcf1332d236b29")


@pytest.fixture(scope="session")
def new_registry():
    yield Contract("0xaF1f5e1c19cB68B30aAD73846eFfDf78a5863319")
