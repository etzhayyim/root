// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies — see /CHARTER-RIDER.md
pragma solidity 0.8.27;

import "forge-std/Script.sol";
import {Constitution} from "../src/Constitution.sol";
import {ConstitutionKeys as K} from "../src/ConstitutionKeys.sol";
import {AdherentRegistry} from "../src/AdherentRegistry.sol";
import {ChartersComplianceRegistry, IAdherentRegistry as CCRRegIA} from "../src/ChartersComplianceRegistry.sol";
import {TitheRouter, IERC20, IConstitution as TRConst, IChartersComplianceRegistry as TRCharters} from "../src/TitheRouter.sol";
import {LandRegistry, IAdherentRegistry as LandIA, IChartersComplianceRegistry as LandCharters} from "../src/LandRegistry.sol";
import {PublicFundGovernance, IAdherentRegistry as PFIA, IChartersComplianceRegistry as PFCharters} from "../src/PublicFundGovernance.sol";
import {ForceAuthorization, IAdherentRegistry as FAIA, IChartersComplianceRegistry as FACharters} from "../src/ForceAuthorization.sol";

/**
 * @title DeployReligiousCorp
 * @notice S2 of ADR-2605192415 §10 roadmap — deploy the religious-corp
 *         constitutional wave contracts (ADRs 2605192100..2605192415) to
 *         a target chain (local Anvil / Base Sepolia / Base mainnet).
 *
 * @dev Deploy order (resolves circular dependencies):
 *       1. Constitution (with religious-corp wave 38 constants + 16 mutables)
 *       2. AdherentRegistry (initial officers list)
 *       3. ChartersComplianceRegistry (bootstrap council 5)
 *       4. TitheRouter (depends on Constitution + Charters + publicFundSafe)
 *       5. LandRegistry (depends on AdherentRegistry + Charters)
 *
 * Usage:
 *   forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
 *     --sig "run(address,address[],address[],address)" \
 *     <USDC_ADDRESS> "[<officer1>,<officer2>,...]" "[<council1>,...<council5>]" <PUBLIC_FUND_SAFE> \
 *     --rpc-url <rpc> --broadcast
 *
 * For local Anvil smoke test:
 *   forge script script/DeployReligiousCorp.s.sol:DeployReligiousCorp \
 *     --sig "runLocal()" \
 *     --rpc-url http://localhost:8545 --broadcast \
 *     --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
 */
contract DeployReligiousCorp is Script {
    struct ReligiousCorpDeployment {
        address constitution;
        address adherentRegistry;
        address chartersComplianceRegistry;
        address titheRouter;
        address landRegistry;
        address publicFundGovernance;
        address forceAuthorization;
        address publicFundSafe;
    }

    // ─── Constants vocabulary (must match Deploy.s.sol _constants/_mutables) ──
    function _constants() internal pure returns (bytes32[] memory keys, bytes32[] memory vals) {
        keys = new bytes32[](39);
        vals = new bytes32[](39);
        keys[0] = K.ONE_SBT_ONE_VOTE;            vals[0] = bytes32(uint256(1));
        keys[1] = K.NO_TRANSFERABLE_SHARE;       vals[1] = bytes32(uint256(1));
        keys[2] = K.LICENSE;                      vals[2] = bytes32("Apache-2.0");
        keys[3] = K.PHENOTYPE_MIN_BPS;            vals[3] = bytes32(uint256(5_000));
        keys[4] = K.PHENOTYPE_MAX_BPS;            vals[4] = bytes32(uint256(20_000));
        keys[5] = K.KAPPA_FLOOR_BPS;              vals[5] = bytes32(uint256(100));
        keys[6] = K.KAPPA_CEILING_BPS;            vals[6] = bytes32(uint256(500));
        keys[7] = K.QUORUM_FLOOR_BPS;             vals[7] = bytes32(uint256(2_000));
        keys[8]  = K.MISSION_LABOR_LIBERATION;            vals[8]  = bytes32(uint256(1));
        keys[9]  = K.MISSION_ROBOTICS_UNIVERSAL;          vals[9]  = bytes32(uint256(1));
        keys[10] = K.MISSION_IP_FREE_RELEASE;             vals[10] = bytes32(uint256(1));
        keys[11] = K.MISSION_DISINTERMEDIATION;           vals[11] = bytes32(uint256(1));
        keys[12] = K.MISSION_SPECIALIST_ANTI_GATEKEEPING; vals[12] = bytes32(uint256(1));
        keys[13] = K.MISSION_ANTI_INDIVIDUALISM;          vals[13] = bytes32(uint256(1));
        keys[14] = K.MISSION_MULTI_GENERATIONAL_PRIORITY; vals[14] = bytes32(uint256(1));
        keys[15] = K.MISSION_MULTI_GENERATIONAL_HORIZON_YEARS; vals[15] = bytes32(uint256(50));
        keys[16] = K.MISSION_WELLBECOMING_PRIORITY;       vals[16] = bytes32(uint256(1));
        keys[17] = K.MISSION_LAND_AS_RELIGIOUS_TRUST;     vals[17] = bytes32(uint256(1));
        keys[18] = K.MISSION_PARALLEL_GOVERNANCE_TO_STATE; vals[18] = bytes32(uint256(1));
        keys[19] = K.MISSION_TRANSPARENT_FORCE_ONLY;      vals[19] = bytes32(uint256(1));
        keys[20] = K.MISSION_PROPRIETARY_FORCE_DESIGN_PROHIBITED; vals[20] = bytes32(uint256(1));
        keys[21] = K.MISSION_FORCE_REQUIRES_SBT_VOTE;     vals[21] = bytes32(uint256(1));
        keys[22] = K.MISSION_NO_STATE_MILITARY_ALLIANCE;  vals[22] = bytes32(uint256(1));
        keys[23] = K.MISSION_EROS_PERMITTED;     vals[23] = bytes32(uint256(1));
        keys[24] = K.MISSION_GORE_PROHIBITED;    vals[24] = bytes32(uint256(1));
        keys[25] = K.MISSION_LINEAGE_JAPANESE_PROTESTANT; vals[25] = bytes32(uint256(1));
        keys[26] = K.MISSION_ESCHATOLOGICAL;               vals[26] = bytes32(uint256(0));
        keys[27] = K.MISSION_REVELATION_IN_CANON;          vals[27] = bytes32(uint256(0));
        keys[28] = K.MISSION_CONTINUOUS_BECOMING;          vals[28] = bytes32(uint256(1));
        keys[29] = K.GOVERNANCE_FUTURE_GENERATIONS_THIRD_PARTY_BENEFICIARY; vals[29] = bytes32(uint256(1));
        keys[30] = K.ECONOMIC_NON_PROFIT_ONLY;            vals[30] = bytes32(uint256(1));
        keys[31] = K.ECONOMIC_DONATION_ONLY;              vals[31] = bytes32(uint256(1));
        keys[32] = K.ECONOMIC_NO_ADVERTISING;             vals[32] = bytes32(uint256(1));
        keys[33] = K.ECONOMIC_TITHE_TO_PUBLIC_FUND_BPS;   vals[33] = bytes32(uint256(1_000));
        keys[34] = K.LICENSE_BASE;                          vals[34] = bytes32("Apache-2.0");
        keys[35] = K.LICENSE_CHARTER_RIDER_REQUIRED;      vals[35] = bytes32(uint256(1));
        keys[36] = K.LICENSE_CHARTER_RIDER_VERSION;       vals[36] = bytes32("v2.0");
        keys[37] = K.ENFORCEMENT_THREE_TIER;               vals[37] = bytes32(uint256(1));
        // kawase-yui FX band (ADR-2605282200 G4): ±0.5% Chainlink mid-market.
        keys[38] = K.KAWASE_MAX_BAND_BPS;                   vals[38] = bytes32(uint256(50));
    }

    function _mutables(address publicFundSafe) internal pure returns (bytes32[] memory keys, bytes32[] memory vals) {
        keys = new bytes32[](17);
        vals = new bytes32[](17);
        keys[0] = K.KISHA_BASE_RATE;       vals[0] = bytes32(uint256(1_000_000));
        keys[1] = K.KAPPA_BPS;              vals[1] = bytes32(uint256(300));
        keys[2] = K.TIER_LIQUID_BPS;        vals[2] = bytes32(uint256(1_000));
        keys[3] = K.TIER_RESERVE_BPS;       vals[3] = bytes32(uint256(6_000));
        keys[4] = K.TIER_CORPUS_BPS;        vals[4] = bytes32(uint256(3_000));
        keys[5] = K.QUORUM_BPS;             vals[5] = bytes32(uint256(3_300));
        keys[6] = K.ACTIVE_WINDOW_SECS;     vals[6] = bytes32(uint256(30 days));
        keys[7] = K.TIMELOCK_SECS;          vals[7] = bytes32(uint256(72 hours));
        keys[8] = K.PHENOTYPE_NON_COMPLIANT_MULTIPLIER; vals[8] = bytes32(uint256(0));
        // public_fund.safe_address wired in constructor (Phase 1).
        keys[9]  = K.PUBLIC_FUND_SAFE_ADDRESS;            vals[9]  = bytes32(uint256(uint160(publicFundSafe)));
        keys[10] = K.CHARTERS_COMPLIANCE_REGISTRY_ADDRESS; vals[10] = bytes32(0);
        keys[11] = K.TITHE_ROUTER_ADDRESS;                 vals[11] = bytes32(0);
        keys[12] = K.LAND_REGISTRY_ADDRESS;                vals[12] = bytes32(0);
        keys[13] = K.FORCE_AUTHORIZATION_ADDRESS;          vals[13] = bytes32(0);
        keys[14] = K.PUBLIC_FUND_GOVERNANCE_ADDRESS;       vals[14] = bytes32(0);
        // kawase-yui per-member monthly cap (ADR-2605282200 G9): R1 default $1,000.
        keys[15] = K.KAWASE_PER_MONTH_CAP_USD_MINOR;        vals[15] = bytes32(uint256(1_000_000_000));
        keys[16] = bytes32(0); vals[16] = bytes32(0);
    }

    function run(
        address usdc,
        address[] memory initialOfficers,
        address[] memory bootstrapCouncil,
        address publicFundSafe
    ) public returns (ReligiousCorpDeployment memory out) {
        require(bootstrapCouncil.length == 5, "council=5");
        require(initialOfficers.length >= 1, "officers>=1");
        require(publicFundSafe != address(0), "publicFundSafe=0");

        vm.startBroadcast();

        // 1. Constitution with religious-corp wave constants
        (bytes32[] memory cK, bytes32[] memory cV) = _constants();
        (bytes32[] memory mK, bytes32[] memory mV) = _mutables(publicFundSafe);
        Constitution constitution = new Constitution(cK, cV, mK, mV);

        // 2. AdherentRegistry
        AdherentRegistry adherent = new AdherentRegistry(initialOfficers);

        // 3. ChartersComplianceRegistry
        ChartersComplianceRegistry charters = new ChartersComplianceRegistry(
            CCRRegIA(address(adherent)),
            bootstrapCouncil
        );

        // 4. TitheRouter
        TitheRouter tithe = new TitheRouter(
            IERC20(usdc),
            TRConst(address(constitution)),
            TRCharters(address(charters)),
            publicFundSafe
        );

        // 5. LandRegistry
        LandRegistry land = new LandRegistry(
            LandIA(address(adherent)),
            LandCharters(address(charters))
        );

        // 6. PublicFundGovernance
        PublicFundGovernance publicFundGov = new PublicFundGovernance(
            PFIA(address(adherent)),
            PFCharters(address(charters)),
            publicFundSafe
        );

        // 7. ForceAuthorization
        ForceAuthorization forceAuth = new ForceAuthorization(
            FAIA(address(adherent)),
            FACharters(address(charters))
        );

        vm.stopBroadcast();

        out = ReligiousCorpDeployment({
            constitution: address(constitution),
            adherentRegistry: address(adherent),
            chartersComplianceRegistry: address(charters),
            titheRouter: address(tithe),
            landRegistry: address(land),
            publicFundGovernance: address(publicFundGov),
            forceAuthorization: address(forceAuth),
            publicFundSafe: publicFundSafe
        });

        _log(out);
    }

    /// @notice Local Anvil smoke test entrypoint — uses deterministic test addresses.
    function runLocal() public returns (ReligiousCorpDeployment memory) {
        // Anvil deterministic accounts 0-9
        address[] memory officers = new address[](1);
        officers[0] = 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266;  // Account 0

        address[] memory council = new address[](5);
        council[0] = 0x70997970C51812dc3A010C7d01b50e0d17dc79C8;  // Account 1
        council[1] = 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC;  // Account 2
        council[2] = 0x90F79bf6EB2c4f870365E785982E1f101E93b906;  // Account 3
        council[3] = 0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65;  // Account 4
        council[4] = 0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc;  // Account 5

        address publicFundSafe = 0x976EA74026E726554dB657fA54763abd0C3a0aa9;  // Account 6 (treated as a Safe stand-in)

        // Mock USDC for local smoke (real Base would use 0x833589...).
        // The address below is the canonical "0x...beef" stand-in — TitheRouter only
        // calls transferFrom() which Anvil treats as a no-op until a real ERC-20
        // is deployed; for the deploy smoke we only care that the deploy succeeds.
        address mockUsdc = address(0xbeef);
        return run(mockUsdc, officers, council, publicFundSafe);
    }

    function _log(ReligiousCorpDeployment memory o) internal pure {
        console.log("=== etzhayyim Religious-Corp Wave Deployment ===");
        console.log("Constitution                 ", o.constitution);
        console.log("AdherentRegistry             ", o.adherentRegistry);
        console.log("ChartersComplianceRegistry   ", o.chartersComplianceRegistry);
        console.log("TitheRouter                  ", o.titheRouter);
        console.log("LandRegistry                 ", o.landRegistry);
        console.log("PublicFundGovernance         ", o.publicFundGovernance);
        console.log("ForceAuthorization           ", o.forceAuthorization);
        console.log("PublicFundSafe               ", o.publicFundSafe);
    }
}
