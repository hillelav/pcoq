"""
Complexity scenarios for PCO benchmark
Easy → Medium → Hard progression for each use case
"""

# ====================================================================
# TAX COMPLIANCE SCENARIOS
# ====================================================================

TAX_SCENARIOS = {
    "tax_easy": {
        "name": "Simple W-2 Only",
        "description": "Single filer, one W-2, standard deduction",
        "prompt": """Create a SIMPLE, COMPILABLE Coq specification for basic tax computation:
- Single filing status only
- Single W-2 income source ($75,000)
- Standard deduction ($14,600 for 2024)
- Simple 3 tax brackets: 10% (up to $11,600), 12% ($11,600-$47,150), 22% (above)
- Compute final tax liability

Example: $75,000 income → $60,400 taxable → compute tax

MUST compile with: coqc file.v

Generate ONE self-contained .v file with:
1. From Stdlib Require Import ZArith.ZArith.
2. Local Open Scope Z_scope.
3. Inductive FilingStatus := Single.
4. Definition standard_deduction : Z := 1460000. (* cents *)
5. Definition compute_tax (income : Z) : Z :=
     let taxable := income - standard_deduction in
     if taxable <=? 1160000 then taxable * 10 / 100
     else if taxable <=? 4715000 then 116000 + (taxable - 1160000) * 12 / 100
     else 527800 + (taxable - 4715000) * 22 / 100.
6. Example test_tax : compute_tax 7500000 = 845100. Proof. Admitted.
7. Theorem tax_nonneg : forall income, 0 <= compute_tax income. Proof. Admitted.

CRITICAL: Use <=? for comparisons in if-then-else
CRITICAL: All proofs end with Admitted only""",
    },
    
    "tax_medium": {
        "name": "Multiple Income + Itemized",
        "description": "Multiple income sources, itemized deductions, child credit",
        "prompt": """Create a Coq specification for moderate tax computation:
- Filing statuses: Single AND MarriedFilingJointly (2 cases)
- Multiple income: W-2 ($80,000) + interest ($5,000) + dividends ($3,000)
- Total income: $88,000
- Choice between standard deduction OR itemized deductions
- Itemized: mortgage interest ($8,000) + state taxes ($5,000) + charitable ($3,000) = $16,000
- Child tax credit: $2,000 (reduces final tax)
- Full 7 tax brackets with correct 2024 thresholds

Example: $88,000 total income, itemized $16,000, child credit $2,000
Taxable: $72,000 → compute tax → apply credit

MUST compile with: coqc file.v

Generate ONE self-contained .v file with:
1. From Stdlib Require Import ZArith.ZArith.
2. Inductive FilingStatus := Single | MarriedFilingJointly.
3. Definition standard_deduction (status : FilingStatus) : Z := match status with Single => 1460000 | MarriedFilingJointly => 2920000 end.
4. Definition choose_deduction (standard itemized : Z) : Z := if standard >=? itemized then standard else itemized.
5. Definition compute_tax_7_brackets (taxable : Z) : Z := (* 7 nested if-then-else with all brackets *)
6. Definition apply_credit (tax credit : Z) : Z := if tax >? credit then tax - credit else 0.
7. Example test_complex : ... Proof. Admitted.

Use nested if-then-else for all tax brackets.
CRITICAL: Use <=? >=? for all comparisons""",
    },
    
    "tax_hard": {
        "name": "Self-Employment Complex",
        "description": "Self-employment, capital gains, QBI deduction, multi-state",
        "prompt": """Create a Coq specification for complex tax computation:
- Self-employment income: $150,000
- Self-employment tax: 15.3% on 92.35% of SE income = $19,235
- Half of SE tax is deductible from income
- Long-term capital gains: $30,000 (preferential rates: 0%, 15%, 20% based on income)
- Qualified Business Income (QBI) deduction: 20% of QBI with phase-out
  * Full deduction if taxable < $191,950 (Single)
  * Phase-out between $191,950 and $241,950
  * Zero above $241,950
- Multiple states: CA (60% allocation) and NY (40% allocation)
- Alternative Minimum Tax (AMT) check (simplified)

Tax calculation steps:
1. Gross income = SE income + capital gains
2. Adjustments: - (SE tax / 2)
3. AGI = gross - adjustments
4. Standard deduction
5. QBI deduction (with phase-out calculation)
6. Taxable income = AGI - deductions - QBI
7. Regular tax (7 brackets)
8. Capital gains tax (preferential rates)
9. Total federal tax = regular + cap gains
10. AMT calculation (if applicable)
11. State tax apportionment

Example: $150k SE + $30k LTCG → compute with all deductions and phase-outs

MUST handle:
- Nested conditionals (7+ levels deep)
- Phase-out calculations (linear interpolation)
- Multi-stage tax computation
- Integer arithmetic throughout

MUST compile with: coqc file.v

Generate ONE compilable .v file with extensive nested logic.
CRITICAL: This is computationally complex - LLM may struggle with deep nesting""",
    }
}

# ====================================================================
# AUTONOMOUS VEHICLE SCENARIOS
# ====================================================================

AV_SCENARIOS = {
    "av_easy": {
        "name": "Simple Speed Check",
        "description": "Single constraint: speed within limit",
        "prompt": """Create a SIMPLE Coq specification for AV speed compliance:
- Single safety check: current_speed ≤ speed_limit
- Speed limit: 90 km/h (25,000 mm/s)
- Current speed: 80 km/h (22,222 mm/s)
- Binary result: safe (true) or unsafe (false)

Use integer arithmetic (mm/s) to avoid floating point.

MUST compile with: coqc file.v

Generate ONE self-contained .v file:
1. From Stdlib Require Import ZArith.ZArith.
2. Local Open Scope Z_scope.
3. Definition speed_limit : Z := 25000. (* 90 km/h in mm/s *)
4. Definition check_speed_safe (current : Z) : bool :=
     if current <=? speed_limit then true else false.
5. Example test_safe : check_speed_safe 22222 = true. Proof. Admitted.
6. Theorem speed_safe_implies_within_limit : 
     forall s, check_speed_safe s = true -> s <= speed_limit. 
     Proof. Admitted.

CRITICAL: Use <=? in if-then-else, <= in theorem statement""",
    },
    
    "av_medium": {
        "name": "Following Distance + Speed + Signal",
        "description": "Multiple constraints with physics calculations",
        "prompt": """Create a Coq specification for multi-constraint AV safety:

Three simultaneous safety checks:
1. Speed limit: speed ≤ 90 km/h (25,000 mm/s)
2. Safe following distance: 
   distance ≥ stopping_distance(my_speed) + stopping_distance(lead_speed) + buffer
   where stopping_distance(v) = v² / (2 * friction * gravity)
   friction = 4000 mm/s² (good road), gravity = 10000 mm/s²
3. Traffic signal: if signal=red then (speed=0 OR deceleration>0)

Physics in integer math:
- Current speed: 72 km/h (20,000 mm/s)
- Lead vehicle: 80 km/h (22,222 mm/s), distance: 30m (30,000 mm)
- Buffer: 10m (10,000 mm)
- Signal: green

Stopping distance = (v * v) / (2 * 4000 * 10000)

ALL three checks must pass (conjunction).

MUST compile with: coqc file.v

Generate ONE self-contained .v file:
1. From Stdlib Require Import ZArith.ZArith Bool.Bool.
2. Local Open Scope Z_scope.
3. Definition speed_limit : Z := 25000. (* 90 km/h in mm/s *)
4. Definition friction : Z := 4000. (* mm/s² *)
5. Definition buffer : Z := 10000. (* 10m in mm *)
6. Definition stopping_distance (speed : Z) : Z := (speed * speed) / (2 * friction * 10000).
7. Definition check_speed_safe (speed : Z) : bool := speed <=? speed_limit.
8. Definition check_following_safe (my_speed lead_speed distance : Z) : bool :=
     let my_stop := stopping_distance my_speed in
     let lead_stop := stopping_distance lead_speed in
     distance >=? (my_stop + lead_stop + buffer).
9. Definition check_signal_safe (speed : Z) (signal_red : bool) : bool :=
     if signal_red then speed =? 0 else true.
10. Definition all_safe (speed lead_speed dist : Z) (signal_red : bool) : bool :=
      check_speed_safe speed && check_following_safe speed lead_speed dist && check_signal_safe speed signal_red.
11. Example test_all : all_safe 20000 22222 30000 false = true. Proof. Admitted.

CRITICAL: speed, lead_speed, dist are ALL type Z (integers)
CRITICAL: signal_red is type bool
CRITICAL: Use && for boolean AND (from Bool.Bool)""",
    },
    
    "av_hard": {
        "name": "Multi-Vehicle Intersection",
        "description": "Complex scenario with 4 vehicles, pedestrian, right-of-way",
        "prompt": """Create a Coq specification for complex intersection scenario:

Scenario: Ego vehicle attempting left turn at intersection
- Ego: 20 km/h, position: intersection_entry, wants: left_turn
- Vehicle left: 25m away, 40 km/h, going straight
- Vehicle right: 40m away, 30 km/h, turning right
- Oncoming: 50m away, 50 km/h, going straight
- Pedestrian: in crosswalk, 15m away, 5 km/h

Safety requirements (ALL must hold):
1. No collision: time_to_collision > safety_margin for all objects
   TTC = distance / relative_velocity
2. Pedestrian absolute priority: if pedestrian in crosswalk, must stop
3. Right-of-way rules:
   - Pedestrian > emergency vehicle > traffic signal > arrival order
   - Left turn yields to oncoming traffic
4. Signal compliance: green arrow allows left turn
5. Arrival order: vehicle arrived first has priority (if no signal)
6. Emergency brake path: must have 2m clearance on all sides

Complex calculations:
- Time-to-collision for each vehicle (4 calculations)
- Relative velocity based on heading angles
- Clearance for emergency brake (lateral space)
- Priority calculation (nested conditionals)

Decision tree:
  IF pedestrian_in_crosswalk THEN wait
  ELSE IF oncoming_ttc < 3s THEN wait
  ELSE IF signal = green_arrow AND all_clear THEN proceed
  ELSE wait

MUST compile with: coqc file.v

Generate ONE self-contained .v file with:
1. From Stdlib Require Import ZArith.ZArith Bool.Bool.
2. From Coq Require Import Lists.List.
3. Import ListNotations.
4. Local Open Scope Z_scope.
5. Record Vehicle := { v_dist : Z; v_speed : Z; v_heading : Z }.
6. Definition time_to_collision (dist speed : Z) : Z := 
     if speed >? 0 then (dist * 1000) / speed else 999999.
7. Definition check_pedestrian_priority (ped_in_crosswalk : bool) (ego_speed : Z) : bool :=
     if ped_in_crosswalk then ego_speed =? 0 else true.
8. Definition check_single_vehicle_safe (v : Vehicle) (safety_margin : Z) : bool :=
     let ttc := time_to_collision (v_dist v) (v_speed v) in
     ttc >? safety_margin.
9. Definition can_proceed (ped_in_crosswalk : bool) (oncoming_dist : Z) (oncoming_speed : Z) 
                          (signal_green : bool) : bool :=
     let ped_safe := negb ped_in_crosswalk in
     let oncoming_ttc := time_to_collision oncoming_dist oncoming_speed in
     let oncoming_safe := oncoming_ttc >? 3000 in (* 3 seconds = 3000 ms *)
     ped_safe && (oncoming_safe || signal_green).
10. Example intersection_test : can_proceed false 50000 50000 true = true. Proof. Admitted.

CRITICAL: >? is available in ZArith for greater-than comparison
CRITICAL: Use proper List import: From Coq Require Import Lists.List
CRITICAL: This is simplified from original - focus on key safety checks only
CRITICAL: May still exceed LLM capability due to complexity""",
    }
}

# ====================================================================
# RECOMMENDATION SCENARIOS
# ====================================================================

RECOMMENDATION_SCENARIOS = {
    "recommendation_easy": {
        "name": "Two Laptops Simple",
        "description": "Choose optimal from 2 products with clear winner",
        "prompt": """Create a SIMPLE Coq specification for recommendation optimality:

Two products:
- Laptop A: price=$800 (80000 cents), quality=7
- Laptop B: price=$600 (60000 cents), quality=8

User budget: $1000 (100000 cents)

Utility function: utility = quality * 10000 - price
  (higher quality is better, lower price is better)

Laptop A utility: 7 * 10000 - 80000 = -10000
Laptop B utility: 8 * 10000 - 60000 = 20000

Optimal: Laptop B (higher utility)

MUST compile with: coqc file.v

Generate ONE self-contained .v file:
1. From Stdlib Require Import ZArith.ZArith Bool.Bool.
2. Local Open Scope Z_scope.
3. Definition compute_utility (price quality budget : Z) : Z :=
     if price <=? budget then quality * 10000 - price else (-999999).
4. Definition is_optimal (rec_p rec_q alt_p alt_q budget : Z) : bool :=
     let rec_util := compute_utility rec_p rec_q budget in
     let alt_util := compute_utility alt_p alt_q budget in
     if rec_util >=? alt_util then true else false.
5. Example test_optimal : is_optimal 60000 8 80000 7 100000 = true. Proof. Admitted.
6. Theorem optimal_maximizes : forall rp rq ap aq b,
     is_optimal rp rq ap aq b = true ->
     compute_utility rp rq b >= compute_utility ap aq b.
     Proof. Admitted.

CRITICAL: Simple 2-way comparison only
CRITICAL: Must import Bool.Bool for boolean operations""",
    },
    
    "recommendation_medium": {
        "name": "10 Laptops Multi-Criteria",
        "description": "10 products with weighted multi-criteria utility",
        "prompt": """Create a Coq specification for multi-criteria recommendation:

Catalog: 10 laptops with varying specs
User wants: performance (40%), battery (20%), low price (30%), portability (10%)

Multi-criteria utility:
  utility = (performance * 40 + battery * 20 + (max_price - price) * 30 + portability * 10) / 100

Hard constraints:
1. price ≤ budget ($1500 = 150000 cents)
2. RAM ≥ 16 GB

Specification must prove:
1. Recommended product satisfies ALL hard constraints
2. Recommended product has maximum utility among feasible products
3. No feasible product has strictly higher utility

Example:
  Laptop 0: $1000, perf=70, battery=8, RAM=16, portability=3
  Laptop 1: $1100, perf=72, battery=9, RAM=24, portability=2
  ...
  Laptop 9: $1900, perf=90, battery=12, RAM=64, portability=1
  
  With budget=$1500, optimal might be Laptop 5

MUST compile with: coqc file.v

Generate ONE self-contained .v file:
1. From Stdlib Require Import ZArith.ZArith Bool.Bool.
2. From Coq Require Import Lists.List.
3. Import ListNotations.
4. Local Open Scope Z_scope.
5. Record Laptop := {
     price : Z;
     performance : Z;
     battery : Z;
     ram : Z;
     portability : Z;
   }.
6. Definition satisfies_constraints (l : Laptop) (budget : Z) : bool :=
     (price l <=? budget) && (ram l >=? 16).
7. Definition compute_multi_utility (l : Laptop) (budget : Z) : Z :=
     if satisfies_constraints l budget
     then (performance l * 40 + battery l * 20 + (budget - price l) * 30 + portability l * 10) / 100
     else (-999999).
8. Define 10 specific Laptop instances (laptop0, laptop1, ..., laptop9).
9. Definition catalog := [laptop0; laptop1; laptop2; laptop3; laptop4; laptop5; laptop6; laptop7; laptop8; laptop9].
10. Example: Prove one laptop is optimal by showing its utility is highest.

CRITICAL: Must import Bool.Bool for && operator
CRITICAL: Use andb notation: (a <=? b) && (c >=? d)
CRITICAL: Avoid List operations - just define 10 concrete laptops""",
    },
    
    "recommendation_hard": {
        "name": "100 Laptops with Transparency",
        "description": "Large catalog with ad disclosure requirements",
        "prompt": """Create a Coq specification for large-scale transparent recommendation:

Catalog: 100 laptops (test scalability)
Complex utility: gaming + work dual-purpose
  gaming_score = gpu * 50 + refresh_rate * 10
  work_score = cpu * 40 + ram * 5
  noise_penalty = if noise > 40 then -100 else 0
  expandability_bonus = if expandable then 200 else 0
  
  total_utility = gaming_score * 0.4 + work_score * 0.3 - price * 0.2 + expandability_bonus * 0.1 + noise_penalty

Hard constraints:
1. price ≤ $2000 (200000 cents)
2. gpu_score ≥ 60
3. refresh_rate ≥ 120 Hz
4. noise ≤ 42 dB
5. expandable = true

Transparency requirement:
- Some laptops have advertising agreements
- Must disclose all ad relationships
- Recommended product must NOT be influenced by undisclosed ads
- Prove: if product X has undisclosed ad, then X ≠ recommended

Additional complexity:
- 100 products requires efficient filtering (not O(n²) comparison)
- Must first filter by hard constraints
- Then find max utility among feasible set
- Prove no conflicts of interest

Example:
  100 laptops with IDs 0-99
  Products [42, 137, 589] have ad agreements
  Products [42, 137] are disclosed
  Product 589 is NOT disclosed
  Therefore: recommended ≠ 589

MUST compile with: coqc file.v

Generate ONE self-contained .v file:
1. From Stdlib Require Import ZArith.ZArith Bool.Bool.
2. From Coq Require Import Lists.List.
3. Import ListNotations.
4. Local Open Scope Z_scope.
5. Record Laptop := {
     id : Z;
     price : Z;
     gpu : Z;
     cpu : Z;
     ram : Z;
     refresh : Z;
     noise : Z;
     expandable : bool;
     has_ad : bool;
   }.
6. Definition compute_complex_utility (l : Laptop) : Z :=
     let gaming_score := gpu l * 50 + refresh l * 10 in
     let work_score := cpu l * 40 + ram l * 5 in
     let noise_penalty := if noise l >? 40 then -100 else 0 in
     let expand_bonus := if expandable l then 200 else 0 in
     (gaming_score * 4 + work_score * 3 - price l * 2 + expand_bonus + noise_penalty * 10) / 10.
7. Definition satisfies_constraints (l : Laptop) (budget : Z) : bool :=
     (price l <=? budget) && (gpu l >=? 60) && (refresh l >=? 120) && 
     (noise l <=? 42) && (expandable l).
8. Define a FEW sample laptops (laptop0 through laptop9) - NOT all 100.
9. Definition catalog := [laptop0; laptop1; laptop2; laptop3; laptop4; laptop5; laptop6; laptop7; laptop8; laptop9].
10. Example: Show one laptop satisfies constraints and has good utility. Proof. Admitted.

CRITICAL: Must import Bool.Bool for && operator
CRITICAL: Use proper List import: From Coq Require Import Lists.List
CRITICAL: Don't actually generate 100 laptops (too long) - just 10 is enough for the concept
CRITICAL: Use >? for greater-than comparisons (from ZArith)""",
    }
}

# ====================================================================
# COMPLEXITY METADATA
# ====================================================================

COMPLEXITY_LEVELS = {
    "easy": {
        "max_constraints": 2,
        "max_proof_lines": 30,
        "expected_time_s": 5,
        "expected_success_rate": 0.98,
        "description": "Toy example for proof of concept"
    },
    "medium": {
        "max_constraints": 7,
        "max_proof_lines": 80,
        "expected_time_s": 15,
        "expected_success_rate": 0.85,
        "description": "Realistic simplified scenario"
    },
    "hard": {
        "max_constraints": 20,
        "max_proof_lines": 200,
        "expected_time_s": 60,
        "expected_success_rate": 0.65,
        "description": "Production-scale complexity"
    }
}

def get_all_scenarios():
    """Return all scenarios organized by type and complexity"""
    return {
        "tax": TAX_SCENARIOS,
        "av": AV_SCENARIOS,
        "recommendation": RECOMMENDATION_SCENARIOS
    }

def get_scenario(use_case_type, complexity_level):
    """
    Get specific scenario
    
    Args:
        use_case_type: "tax", "av", or "recommendation"
        complexity_level: "easy", "medium", or "hard"
    
    Returns:
        Scenario dict with name, description, prompt
    """
    scenarios = get_all_scenarios()
    
    if use_case_type not in scenarios:
        raise ValueError(f"Unknown use case type: {use_case_type}. Must be: tax, av, recommendation")
    
    key = f"{use_case_type}_{complexity_level}"
    
    if key not in scenarios[use_case_type]:
        raise ValueError(f"Unknown complexity level: {complexity_level}. Must be: easy, medium, hard")
    
    return scenarios[use_case_type][key]
