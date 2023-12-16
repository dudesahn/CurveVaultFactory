# README

## Tests

To run the test suite with detailed printouts

```
brownie test -s
```

Note that due to limitations of Brownie/Ganache-CLI, certain aspects of these contracts may cause reverts unless using a different RPC such as
tenderly. For instance, Curve Global testing of deployments will fail because of the try-catch [here](https://github.com/dudesahn/CurveVaultFactory/blob/c370aa2b31fefc6f5b4a10f573b4500e4c834158/contracts/CurveGlobal.sol#L760).

## Core Contracts

### [CurveGlobal.sol](https://github.com/dudesahn/CurveVaultFactory/blob/main/contracts/CurveGlobal.sol)

This is our factory for creating yVaults for Curve pool tokens, with up to three strategies. One deposits directly to Convex,
another deposits directly to the Curve gauge via Yearn's Voter (using Yearn's veCRV boost), and strategies with FXS rewards
from Frax (typically those paired with FRAXBP or other Frax tokens) utilize a third strategy to deposit to Frax Convex and farm
their FXS boost.

The `createNewVaultsAndStrategies` function allows any user to create a yVault for a Curve LP token by entering a gauge
(provided one doesn't already exist). The gauge is used to identify the LP Token and the Convex PID. If a PID doesn't already exist,
a new Convex pool is deployed. Then we create the new automated vault along with the corresponding strategies. If a vault has a Convex
Frax pool available, it is auto-detected and the Frax strategy is added. As Frax pools are continually added, it's possible that a vault
has a Frax strategy become an option after it has already been deployed. In this case, the strategy must be manually deployed and added
to the vault by governance.

### [StrategyConvexFactoryClonable.sol](https://github.com/dudesahn/CurveVaultFactory/blob/main/contracts/StrategyConvexFactoryClonable.sol)

Our Convex strategy is a simple auto-compounder for Convex. It deposits Curve pool tokens into Convex and then periodically claims
CRV and CVX rewards, swaps them for the vault's Curve pool tokens, and deposits those back into Convex to earn more rewards.

### [StrategyCurveBoostedFactoryClonable.sol](https://github.com/dudesahn/CurveVaultFactory/blob/main/contracts/StrategyCurveBoostedFactoryClonable.sol)

Our Curve strategy deposits LP tokens to Yearn's [Voter](https://etherscan.io/address/0xf147b8125d2ef93fb6965db97d6746952a133934) via a
strategy proxy. All Curve strategy LP tokens are held by the voter, and are staked in the Curve gauge. CRV token emissions are boosted by
Yearn's veCRV holdings. Typically, this strategy is more favorable than Convex, unless Yearn holds large (>20%) of the total LP tokens in our voter.

### [StrategyConvexFraxFactoryClonable.sol](https://github.com/dudesahn/CurveVaultFactory/blob/main/contracts/StrategyConvexFraxFactoryClonable.sol)

Our Convex Frax strategy is very similar to the Convex strategy, except LP tokens receive the benefit of not only Convex's veCRV position,
but also their veFXS position for those pools that have FXS emissions. Frax LP deposits utilize a helper `userVault` contract that tracks deposits,
as Frax deposits also can be locked for increased time periods for higher APR (minimum of 7 days). The strategy can manage multiple deposits at once
(called `keks` by Frax), and can also be configured to redeposit to the same keks over and over, meaning that past the initial 7-day period there
is effectively no lock.

### [StrategyPrismaConvexFactoryClonable.sol](https://github.com/dudesahn/CurveVaultFactory/blob/main/contracts/StrategyPrismaConvexFactoryClonable.sol)

Our Prisma Convex strategy is very similar to the Convex strategy, except we receive extra yield through Prisma's _receiver_ contract, which is
their name for a gauge. vePRISMA voters are able to approve proposed receivers to receive vePRISMA emissions. For this strategy, we deposit the
Curve LP to the Prisma Convex receiver, which just deposits to Convex via a Prisma contract and then receives extra vePRISMA (as yPRISMA) on top.
Note that for most of these pools, PRISMA emissions are the primary form of yield, so for these vaults we will send the majority of `debtRatio` (if
not 100%) to this strategy.

### [KeeperWrapper.sol](https://github.com/dudesahn/CurveVaultFactory/blob/main/contracts/KeeperWrapper.sol)

If set as the keeper of the strategy, this contract will make harvest public. Factory harvests do not swap atomically,
but instead do so asynchronously, using TradeFactory and SeaSolver, Yearn's in-house CoWSwap solver.
