"""
Synthetic auto claims for development and testing. Entirely fabricated.

  windshield - all criteria met        -> approved
  frame      - missing report, cost too high vs ACV -> pended / likely denial
  tow        - no pre-approval needed  -> short-circuit
  adas       - recalibration after covered glass replacement -> approved
"""
from datetime import date
from models.acord import (
    ClaimFile, PolicyHolder, Vehicle, AutoPolicy, Coverage, Loss, RepairRequest,
)
from data.coverage_guidelines import CARRIER

_FULL = [
    Coverage(type="liability"),
    Coverage(type="collision", deductible=500),
    Coverage(type="comprehensive", deductible=250),
    Coverage(type="towing"),
]

CASE_WINDSHIELD = ClaimFile(
    claim_number="CLM-1001",
    policyholder=PolicyHolder(id="PH-501", first_name="Maria", last_name="Lopez"),
    vehicle=Vehicle(vin="2HKRS4H70NH400001", year=2022, make="Honda", model="CR-V",
                    adas_equipped=True, actual_cash_value=27500),
    policy=AutoPolicy(policy_number="LMA-778812", carrier_name=CARRIER, coverages=_FULL),
    loss=Loss(loss_date=date(2026, 10, 12), cause="glass",
              description="Rock strike on I-90"),
    repair_request=RepairRequest(service_code="AUTO-GLS-RPL",
                                 service_name="Windshield replacement",
                                 estimated_cost=1180, reason="Crack across driver view"),
    note_text=(
        "Insured reports a rock strike on I-90 on 10/12/2026. Inspection found a 14-inch "
        "crack running across the driver's critical viewing area; too long for resin chip "
        "repair. Four photos of the damage attached to the file. Comprehensive coverage "
        "with $250 deductible confirmed active."
    ),
)

CASE_FRAME = ClaimFile(
    claim_number="CLM-1002",
    policyholder=PolicyHolder(id="PH-502", first_name="Daniel", last_name="Brooks"),
    vehicle=Vehicle(vin="1FADP3F20FL000002", year=2015, make="Ford", model="Focus",
                    adas_equipped=False, actual_cash_value=7800),
    policy=AutoPolicy(policy_number="LMA-662041", carrier_name=CARRIER, coverages=_FULL),
    loss=Loss(loss_date=date(2026, 10, 3), cause="collision",
              description="Front-end collision at low speed"),
    repair_request=RepairRequest(service_code="AUTO-STR-FRM",
                                 service_name="Structural / frame repair",
                                 estimated_cost=6900, reason="Bent front frame rail"),
    note_text=(
        "Front-end collision on 10/3/2026. Visual inspection shows the left front frame "
        "rail appears bent. Shop estimate is $6,900. Frame measurement not yet performed. "
        "Collision coverage active."
    ),
)

CASE_TOW = ClaimFile(
    claim_number="CLM-1003",
    policyholder=PolicyHolder(id="PH-503", first_name="Priya", last_name="Shah"),
    vehicle=Vehicle(vin="5YJ3E1EA0KF000003", year=2019, make="Tesla", model="Model 3"),
    policy=AutoPolicy(policy_number="LMA-559320", carrier_name=CARRIER, coverages=_FULL),
    loss=Loss(loss_date=date(2026, 10, 20), cause="collision",
              description="Vehicle not drivable after collision"),
    repair_request=RepairRequest(service_code="AUTO-TOW-STD",
                                 service_name="Standard tow to repair facility",
                                 estimated_cost=145),
    note_text="Vehicle not drivable after collision; towed 8 miles to network shop.",
)

CASE_ADAS = ClaimFile(
    claim_number="CLM-1004",
    policyholder=PolicyHolder(id="PH-504", first_name="Kevin", last_name="Nguyen"),
    vehicle=Vehicle(vin="2T3P1RFV5PW000004", year=2023, make="Toyota", model="RAV4",
                    adas_equipped=True, actual_cash_value=31200),
    policy=AutoPolicy(policy_number="LMA-440187", carrier_name=CARRIER, coverages=_FULL),
    loss=Loss(loss_date=date(2026, 10, 15), cause="glass",
              description="Windshield replaced under covered glass claim"),
    repair_request=RepairRequest(service_code="AUTO-ADAS-CAL",
                                 service_name="ADAS camera/sensor recalibration",
                                 estimated_cost=395),
    note_text=(
        "2023 RAV4 with Toyota Safety Sense lane-departure camera mounted on the windshield. "
        "Windshield was replaced under an approved comprehensive glass claim. Shop will "
        "perform static camera calibration per Toyota OEM procedure and attach pre- and "
        "post-repair scan reports."
    ),
)

ALL_CASES = {
    "windshield": CASE_WINDSHIELD,
    "frame": CASE_FRAME,
    "tow": CASE_TOW,
    "adas": CASE_ADAS,
}
