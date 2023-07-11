# README

## CurveGlobal.sol

https://github.com/flashfish0x/StrategyConvexTemplate/blob/e992dc01c5f31d6b5a7392b6ed731f1b8d594168/contracts/CurveGlobal.sol

This is our factory for creating yVaults for Curve pool tokens, with one strategy to farm via Convex.
There are lots of setters that we can use to make changes to future vaults/strategies created by the factory.
The createNewVaultsAndStrategies function allows any user to create a yVault for a Curve LP token by entering a gauge (provided one doesn't already exist).
The gauge is used to identify the lpToken and the Convex pid.
Then we create the new automated vault and the Convex strategy.
Finally we add the strategy to the vault.

## StrategyConvexFactoryClonable.sol

https://github.com/flashfish0x/StrategyConvexTemplate/blob/e992dc01c5f31d6b5a7392b6ed731f1b8d594168/contracts/StrategyConvexFactoryClonable.sol

This is our Convex strategy that is created by CurveGlobal and automatically added to each vault it creates.
It's a simple auto-compounder for Convex.
It deposits Curve pool tokens into Convex and then periodically claims CRV and CVX rewards, swaps them for the vault's Curve pool tokens, and deposits those back into Convex to earn more rewards.

## KeeperWrapper.sol

https://github.com/flashfish0x/StrategyConvexTemplate/blob/e992dc01c5f31d6b5a7392b6ed731f1b8d594168/contracts/KeeperWrapper.sol

If set as the keeper of the strategy, this contract will make keeper functions (like harvest) public.
