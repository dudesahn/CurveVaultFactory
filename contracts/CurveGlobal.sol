// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;
pragma experimental ABIEncoderV2;

enum VaultType {DEFAULT, AUTOMATED, FIXED_TERM, EXPERIMENTAL}

interface IDetails {
    // get details from curve
    function name() external view returns (string memory);

    function symbol() external view returns (string memory);
}

interface IVoter {
    // get details from our curve voter
    function strategy() external view returns (address);
}

interface IProxy {
    // get details from our curve voter
    function approveStrategy(address gauge, address strategy) external;
}

interface Registry {
    function newVault(
        address _token,
        address _governance,
        address _guardian,
        address _rewards,
        string calldata _name,
        string calldata _symbol,
        uint256 _releaseDelta,
        VaultType _type
    ) external returns (address);

    function isRegistered(address token) external view returns (bool);

    function latestVault(address token) external view returns (address);

    function latestVault(address token, VaultType _type)
        external
        view
        returns (address);

    function endorseVault(
        address _vault,
        uint256 _releaseDelta,
        VaultType _type
    ) external;
}

interface IPoolManager {
    function addPool(address _gauge) external returns (bool);
}

interface ICurveGauge {
    function deposit(uint256) external;

    function balanceOf(address) external view returns (uint256);

    function withdraw(uint256) external;

    function claim_rewards() external;

    function reward_tokens(uint256) external view returns (address); //v2

    function rewarded_token() external view returns (address); //v1

    function lp_token() external view returns (address);
}

interface IGaugeController {
    function get_gauge_weight(address _gauge) external view returns (uint256);

    function vote_user_slopes(address, address)
        external
        view
        returns (
            uint256,
            uint256,
            uint256
        ); //slope,power,end

    function vote_for_gauge_weights(address, uint256) external;

    function add_gauge(
        address,
        int128,
        uint256
    ) external;
}

interface IStrategy {
    function cloneStrategyConvex(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        uint256 _pid,
        address _tradeFactory,
        uint256 _harvestProfitMin,
        uint256 _harvestProfitMax,
        address _booster,
        address _convexToken
    ) external returns (address newStrategy);
    
    function cloneStrategyCurveBoosted(
        address _vault,
        address _strategist,
        address _rewards,
        address _keeper,
        address _proxy,
        address _gauge,
        address _tradeFactory,
        uint256 _harvestProfitMin,
        uint256 _harvestProfitMax
    ) external returns (address newStrategy);

    function updateVoter(address _convexVoter) external;

    function updateLocalKeepCrvs(uint256 _keepCrv, uint256 _keepCvx) external;

    function updateLocalKeepCrv(uint256 _keepCrv) external;

    function setHealthCheck(address) external;
}

interface IBooster {
    function gaugeMap(address) external view returns (bool);

    // deposit into convex, receive a tokenized deposit.  parameter to stake immediately (we always do this).
    function deposit(
        uint256 _pid,
        uint256 _amount,
        bool _stake
    ) external returns (bool);

    // burn a tokenized deposit (Convex deposit tokens) to receive curve lp tokens back
    function withdraw(uint256 _pid, uint256 _amount) external returns (bool);

    function poolLength() external view returns (uint256);

    // give us info about a pool based on its pid
    function poolInfo(uint256)
        external
        view
        returns (
            address,
            address,
            address,
            address,
            address,
            bool
        );
}

interface Vault {
    function setGovernance(address) external;

    function setManagement(address) external;

    function managementFee() external view returns (uint256);

    function setManagementFee(uint256) external;

    function performanceFee() external view returns (uint256);

    function setPerformanceFee(uint256) external;

    function setDepositLimit(uint256) external;

    function addStrategy(
        address,
        uint256,
        uint256,
        uint256,
        uint256
    ) external;
}

contract CurveGlobal {
    event NewAutomatedVault(
        uint256 indexed category,
        address indexed lpToken,
        address gauge,
        address indexed vault,
        address convexStrategy,
        address curveStrategy
    );

    ///////////////////////////////////
    //
    //  Storage variables and setters
    //
    ////////////////////////////////////

    address[] public deployedVaults;

    function allDeployedVaults() external view returns (address[] memory) {
        return deployedVaults;
    }

    function numVaults() external view returns (uint256) {
        return deployedVaults.length;
    }

    address public constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    uint256 public constant CATEGORY = 0; // 0 for curve

    // always owned by ychad
    address public owner;
    address internal pendingOwner = 0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52;

    function setOwner(address newOwner) external {
        if(msg.sender != owner) {
            revert();
        }
        pendingOwner = newOwner;
    }

    function acceptOwner() external {
        if(msg.sender != pendingOwner) {
            revert();
        }
        owner = pendingOwner;
    }

    address public convexPoolManager =
        0xD1f9b3de42420A295C33c07aa5C9e04eDC6a4447;

    function setConvexPoolManager(address _convexPoolManager) external {
        if(msg.sender != owner) {
            revert();
        }
        convexPoolManager = _convexPoolManager;
    }

    Registry public registry; // = Registry(address(0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804));

    function setRegistry(address _registry) external {
        if(msg.sender != owner) {
            revert();
        }
        registry = Registry(_registry);
    }

    IBooster public booster =
        IBooster(0xF403C135812408BFbE8713b5A23a04b3D48AAE31);

    function setBooster(address _booster) external {
        if(msg.sender != owner) {
            revert();
        }
        booster = IBooster(_booster);
    }

    address public governance = 0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52;

    function setGovernance(address _governance) external {
        if(msg.sender != owner) {
            revert();
        }
        governance = _governance;
    }

    address public management = 0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7;

    function setManagement(address _management) external {
        if(msg.sender != owner) {
            revert();
        }
        management = _management;
    }

    address public guardian = 0x846e211e8ba920B353FB717631C015cf04061Cc9;

    function setGuardian(address _guardian) external {
        if(msg.sender != owner) {
            revert();
        }
        guardian = _guardian;
    }

    address public treasury = 0x93A62dA5a14C80f265DAbC077fCEE437B1a0Efde;

    function setTreasury(address _treasury) external {
        if(msg.sender != owner) {
            revert();
        }
        treasury = _treasury;
    }

    address public keeper = 0x256e6a486075fbAdbB881516e9b6b507fd082B5D;

    function setKeeper(address _keeper) external {
        if(!(msg.sender == owner || msg.sender == management)) {
            revert();
        }
        keeper = _keeper;
    }

    address public healthCheck = 0xDDCea799fF1699e98EDF118e0629A974Df7DF012;

    function setHealthcheck(address _health) external {
        if(!(msg.sender == owner || msg.sender == management)) {
            revert();
        }
        healthCheck = _health;
    }

    address public tradeFactory = 0xd6a8ae62f4d593DAf72E2D7c9f7bDB89AB069F06;

    function setTradeFactory(address _tradeFactory) external {
        if(msg.sender != owner) {
            revert();
        }
        tradeFactory = _tradeFactory;
    }

    address public baseFeeOracle;

    function setBaseFeeOracle(address _baseFeeOracle) external {
        if(msg.sender != owner) {
            revert();
        }
        baseFeeOracle = _baseFeeOracle;
    }

    uint256 public depositLimit = 10_000_000_000_000 * 1e18; // some large number

    function setDepositLimit(uint256 _depositLimit) external {
        if(!(msg.sender == owner || msg.sender == management)) {
            revert();
        }
        depositLimit = _depositLimit;
    }

    address public convexStratImplementation;

    function setConvexStratImplementation(address _convexStratImplementation)
        external
    {
        if(msg.sender != owner) {
            revert();
        }
        convexStratImplementation = _convexStratImplementation;
    }

    address public curveStratImplementation;

    function setCurveStratImplementation(address _curveStratImplementation)
        external
    {
        if(msg.sender != owner) {
            revert();
        }
        curveStratImplementation = _curveStratImplementation;
    }

    uint256 public keepCRV; // the percentage of CRV we re-lock for boost (in basis points). Default is 0%.
    address public constant voterCRV = 0xF147b8125d2ef93FB6965Db97D6746952a133934; // Yearn's veCRV voter, will never change

    // Set the amount of CRV to be locked in Yearn's veCRV voter from each harvest.
    function setKeepCRV(uint256 _keepCRV) external {
        if(msg.sender != owner) {
            revert();
        }
        if(_keepCRV > 10_000) {
            revert();
        }
        keepCRV = _keepCRV;
    }

    uint256 public keepCVX; // the percentage of CVX we re-lock for boost (in basis points). Default is 0%.
    address public voterCVX;

    // Set the amount of CVX to be locked in Yearn's veCVX voter from each harvest.
    function setKeepCVX(uint256 _keepCVX, address _voterCVX) external {
        if(msg.sender != owner) {
            revert();
        }
        if(_keepCVX > 10_000) {
            revert();
        }
        if (_keepCVX > 0) {
            if(_voterCVX == address(0)) {
            revert();
            }
        }

        keepCVX = _keepCVX;
        voterCVX = _voterCVX;
    }

    uint256 public harvestProfitMinInUsdt = 10_000 * 1e6; // what profit do we need to harvest

    function setHarvestProfitMinInUsdt(uint256 _harvestProfitMinInUsdt)
        external
    {
        if(!(msg.sender == owner || msg.sender == management)) {
            revert();
        }
        harvestProfitMinInUsdt = _harvestProfitMinInUsdt;
    }

    uint256 public harvestProfitMaxInUsdt = 25_000 * 1e6; // what profit do we need to harvest

    function setHarvestProfitMaxInUsdt(uint256 _harvestProfitMaxInUsdt)
        external
    {
        if(!(msg.sender == owner || msg.sender == management)) {
            revert();
        }
        harvestProfitMaxInUsdt = _harvestProfitMaxInUsdt;
    }

    uint256 public performanceFee = 1_000;

    function setPerformanceFee(uint256 _performanceFee) external {
        if(msg.sender != owner) {
            revert();
        }
        if(_performanceFee > 5_000) {
            revert();
        }
        performanceFee = _performanceFee;
    }

    uint256 public managementFee = 0;

    function setManagementFee(uint256 _managementFee) external {
        if(msg.sender != owner) {
            revert();
        }
        if(_managementFee > 1_000) {
            revert();
        }
        managementFee = _managementFee;
    }
    

    ///////////////////////////////////
    //
    // Functions
    //
    ////////////////////////////////////

    constructor(
        address _registry,
        address _convexStratImplementation,
        address _curveStratImplementation,
        address _owner
    ) {
        registry = Registry(_registry);
        convexStratImplementation = _convexStratImplementation;
        curveStratImplementation = _curveStratImplementation;
        owner = _owner;
    }

    /// @notice Public function to check whether, for a given gauge address, its possible to permissionlessly create a vault for corressponding LP token
    /// @param _gauge The gauge address to find the latest vault for
    /// @return bool if true, vault can be created permissionlessly
    function canCreateVaultPermissionlessly(address _gauge) public view returns (bool) {
        return latestDefaultOrAutomatedVaultFromGauge(_gauge) == address(0);
    }

    /// @dev Returns only the latest vault address for any DEFAULT/AUTOMATED type vaults
    /// @dev If no vault of either DEFAULT or AUTOMATED types exists for this gauge, 0x0 is returned from registry.
    function latestDefaultOrAutomatedVaultFromGauge(address _gauge)
        internal
        view
        returns (address)
    {
        address lptoken = ICurveGauge(_gauge).lp_token();
        Registry _registry = registry;
        if (!_registry.isRegistered(lptoken)) {
            return address(0);
        }

        address latest = _registry.latestVault(lptoken);
        if (latest == address(0)) {
            return _registry.latestVault(lptoken, VaultType.AUTOMATED);
        }

        return latest;
    }

    function getPid(address _gauge) public view returns (uint256 pid) {

        IBooster _booster = booster;
        if (!_booster.gaugeMap(_gauge)) {
            return type(uint256).max;
        }

        for (uint256 i = _booster.poolLength(); i > 0; --i) {
            //we start at the end and work back for most recent
            (, , address gauge, , , ) = _booster.poolInfo(i - 1);

            if (_gauge == gauge) {
                return i - 1;
            }
        }
    }

    function getProxy() public view returns (address) {
        address proxy = IVoter(voterCRV).strategy();
        return proxy;
    }

    // only permissioned users can set custom name and symbol or deploy if there is already one endorsed
    function createNewVaultsAndStrategies(
        address _gauge,
        bool _allowDuplicate,
        string memory _name,
        string memory _symbol
    ) external returns (address vault, address convexStrategy, address curveStrategy) {
        if(!(msg.sender == owner || msg.sender == management)) {
            revert();
        }

        return _createNewVaultsAndStrategies(_gauge, _allowDuplicate, _name, _symbol);
    }

    function createNewVaultsAndStrategies(address _gauge)
        external
        returns (address vault, address convexStrategy, address curveStrategy)
    {
        return _createNewVaultsAndStrategies(_gauge, false, "", "");
    }

    function _createNewVaultsAndStrategies(
        address _gauge,
        bool _allowDuplicate,
        string memory _name,
        string memory _symbol
    ) internal returns (address vault, address convexStrategy, address curveStrategy) {
        if (!_allowDuplicate) {
            require(
                canCreateVaultPermissionlessly(_gauge),
                "Vault already exists"
            );
        }
        address lptoken = ICurveGauge(_gauge).lp_token();

        // get convex pid. if no pid create one
        uint256 pid = getPid(_gauge);
        if (pid == type(uint256).max) {
            //when we add the new pool it will be added to the end of the pools in convexDeposit.
            pid = booster.poolLength();
            //add pool
            require(
                IPoolManager(convexPoolManager).addPool(_gauge),
                "Unable to add pool to Convex"
            );
        }
                
        if (_allowDuplicate) { 
            // allow trusted users to input the name and symbol—hopefully they behave!
            vault = _createCustomVault(lptoken, _name, _symbol);
        } else {
            // anyone can create a vault, but it will have an auto-generated name and symbol
            vault = _createStandardVault(lptoken);
        }
        
        // setup our fees, deposit limit, gov, etc
        _setupVaultParams(vault);
        
        // setup our strategies as needed
        (convexStrategy, curveStrategy)= _setupStrategies(vault, _gauge, pid);

        emit NewAutomatedVault(CATEGORY, lptoken, _gauge, vault, convexStrategy, curveStrategy);
    }
    
    function _createCustomVault(address lptoken, string memory _name, string memory _symbol) internal returns (address vault) {
        vault = registry.newVault(
            lptoken,
            address(this),
            guardian,
            treasury,
            _name,
            _symbol,
            0,
            VaultType.AUTOMATED
        );
    }
    
    function _createStandardVault(address lptoken) internal returns (address vault) {
        vault = registry.newVault(
            lptoken,
            address(this),
            guardian,
            treasury,
            string(
                abi.encodePacked(
                    "Curve ",
                    IDetails(address(lptoken)).symbol(),
                    " Auto-Compounding yVault"
                )
            ),
            string(
                abi.encodePacked("yvCurve-", IDetails(address(lptoken)).symbol())
            ),
            0,
            VaultType.AUTOMATED
        );
    }
    
    function _setupVaultParams(address _vault) internal {
        deployedVaults.push(_vault);
        
        Vault v = Vault(_vault);
        v.setManagement(management);
        
        //set governance to ychad who needs to accept before it is finalised. until then governance is this factory
        v.setGovernance(governance);
        v.setDepositLimit(depositLimit);
        
        if (v.managementFee() != managementFee) {
            v.setManagementFee(managementFee);
        }
        if (v.performanceFee() != performanceFee) {
            v.setPerformanceFee(performanceFee);
        }
    }
    
    function _setupStrategies(address _vault, address _gauge, uint256 _pid) internal returns (address convexStrategy, address curveStrategy){
        // first we create the convex strat
        convexStrategy = IStrategy(convexStratImplementation).cloneStrategyConvex(
            _vault,
            management,
            treasury,
            keeper,
            _pid,
            tradeFactory,
            harvestProfitMinInUsdt,
            harvestProfitMaxInUsdt,
            address(booster),
            CVX
        );
        IStrategy(convexStrategy).setHealthCheck(healthCheck);
        
        if (keepCRV > 0 || keepCVX > 0) {
            IStrategy(convexStrategy).updateVoter(voterCVX);
            IStrategy(convexStrategy).updateLocalKeepCrvs(keepCRV, keepCVX);
        }
        
        // only attach a curve strategy if this is the first vault for this LP
        if (canCreateVaultPermissionlessly(_gauge)) {
            // pull our strategyProxy from our voter
            IProxy proxy = IProxy(getProxy());
            
            // create the curve voter strategy
            curveStrategy = IStrategy(curveStratImplementation).cloneStrategyCurveBoosted(
                _vault,
                management,
                treasury,
                keeper,
                address(proxy),
                _gauge,
                tradeFactory,
                harvestProfitMinInUsdt,
                harvestProfitMaxInUsdt
            );
            IStrategy(curveStrategy).setHealthCheck(healthCheck);
            
            if (keepCRV > 0) {
                IStrategy(curveStrategy).updateLocalKeepCrv(keepCRV);
            }
            
            Vault(_vault).addStrategy(
                convexStrategy,
                5_000,
                0,
                type(uint256).max,
                0
            );
            
            Vault(_vault).addStrategy(
                curveStrategy,
                5_000,
                0,
                type(uint256).max,
                0
            );
            
            // approve our new voter strategy on the proxy
            proxy.approveStrategy(_gauge, curveStrategy);
        } else {
            Vault(_vault).addStrategy(
                convexStrategy,
                10_000,
                0,
                type(uint256).max,
                0
            );
        }
    }
}