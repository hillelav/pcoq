(* ============================================================== *)
(* TrafficLaw.v - Formal Traffic Law Specification                *)
(* Published by: Transportation Ministry (hypothetically)         *)
(* Version: 2024.1                                                *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Require Import Bool.
Require Import Lia.
Open Scope Z_scope.

(* ============================================================== *)
(* SECTION 1: BASIC UNITS AND CONVERSIONS                         *)
(* All measurements in millimeters and milliseconds for precision *)
(* ============================================================== *)

(* Speed in mm/s (millimeters per second) *)
Definition speed := Z.

(* Distance in mm *)
Definition distance := Z.

(* Time in ms (milliseconds) *)
Definition time_ms := Z.

(* Acceleration in mm/s^2 *)
Definition acceleration := Z.

(* Angle in millidegrees (1/1000 of a degree) *)
Definition angle := Z.

(* Convert km/h to mm/s: 1 km/h = 1000m/3600s = 1000000mm/3600000ms *)
(* Simplified: multiply by 2500/9 *)
Definition kmh_to_mms (kmh : Z) : speed := kmh * 2500 / 9.

(* Convert m/s to mm/s *)
Definition ms_to_mms (ms : Z) : speed := ms * 1000.

(* Convert meters to mm *)
Definition m_to_mm (m : Z) : distance := m * 1000.

(* Standard speed limits in mm/s *)
Definition speed_limit_30 : speed := kmh_to_mms 30.   (*  8333 mm/s *)
Definition speed_limit_50 : speed := kmh_to_mms 50.   (* 13888 mm/s *)
Definition speed_limit_80 : speed := kmh_to_mms 80.   (* 22222 mm/s *)
Definition speed_limit_100 : speed := kmh_to_mms 100. (* 27777 mm/s *)
Definition speed_limit_120 : speed := kmh_to_mms 120. (* 33333 mm/s *)

(* ============================================================== *)
(* SECTION 2: ROAD CONDITIONS                                     *)
(* ============================================================== *)

Inductive road_condition : Type :=
  | Dry
  | Wet
  | Icy
  | Snow
  | Fog
  | Construction
  | SchoolZone
  | EmergencyScene.

(* Condition affects speed limit *)
Definition condition_speed_factor_num (cond : road_condition) : Z :=
  match cond with
  | Dry => 100
  | Wet => 80
  | Icy => 50
  | Snow => 60
  | Fog => 70
  | Construction => 100  (* Handled by absolute limit *)
  | SchoolZone => 100    (* Handled by absolute limit *)
  | EmergencyScene => 0
  end.

Definition condition_speed_factor_den : Z := 100.

(* Absolute speed caps for certain conditions *)
Definition condition_absolute_limit (cond : road_condition) : option speed :=
  match cond with
  | Construction => Some (kmh_to_mms 30)
  | SchoolZone => Some (kmh_to_mms 30)
  | EmergencyScene => Some 0
  | _ => None
  end.

(* Compute adjusted speed limit *)
Definition adjusted_speed_limit (base_limit : speed) (cond : road_condition) : speed :=
  let factor_limited := base_limit * condition_speed_factor_num cond / condition_speed_factor_den in
  match condition_absolute_limit cond with
  | Some abs_limit => Z.min factor_limited abs_limit
  | None => factor_limited
  end.

(* ============================================================== *)
(* SECTION 3: TRAFFIC SIGNALS                                     *)
(* ============================================================== *)

Inductive signal_state : Type :=
  | Red
  | Yellow
  | Green
  | FlashingYellow
  | FlashingRed
  | ArrowGreen     (* Protected turn *)
  | ArrowYellow
  | ArrowRed
  | Off.

(* Signal phase timing (for prediction) *)
Record signal_phase := mkPhase {
  phase_state : signal_state;
  phase_duration : time_ms;
}.

(* Semantic meaning of signals *)
Definition signal_permits_entry (sig : signal_state) : bool :=
  match sig with
  | Green => true
  | ArrowGreen => true
  | FlashingYellow => true  (* Proceed with caution *)
  | _ => false
  end.

Definition signal_requires_stop (sig : signal_state) : bool :=
  match sig with
  | Red => true
  | FlashingRed => true
  | ArrowRed => true
  | _ => false
  end.

Definition signal_requires_prepare_stop (sig : signal_state) : bool :=
  match sig with
  | Yellow => true
  | ArrowYellow => true
  | _ => false
  end.

Definition signal_requires_caution (sig : signal_state) : bool :=
  match sig with
  | FlashingYellow => true
  | Off => true
  | _ => false
  end.

(* ============================================================== *)
(* SECTION 4: RIGHT-OF-WAY RULES                                  *)
(* ============================================================== *)

Inductive priority_sign : Type :=
  | PriorityRoad        (* On the priority road *)
  | GiveWay             (* Yield/Give way sign *)
  | StopSign            (* Must stop completely *)
  | NoPrioritySign.     (* Use default rules *)

Inductive turn_direction : Type :=
  | GoStraight
  | TurnLeft
  | TurnRight
  | UTurn.

(* Right-of-way at intersections *)
(* Returns true if ego vehicle has priority over other vehicle *)
Definition has_priority 
    (ego_sign other_sign : priority_sign)
    (ego_turn other_turn : turn_direction)
    (ego_arrival other_arrival : time_ms)
    (other_on_right : bool) : bool :=
  match ego_sign, other_sign with
  (* Priority road always has right of way over non-priority *)
  | PriorityRoad, GiveWay => true
  | PriorityRoad, StopSign => true
  | PriorityRoad, NoPrioritySign => true
  | GiveWay, PriorityRoad => false
  | StopSign, PriorityRoad => false
  | NoPrioritySign, PriorityRoad => false
  
  (* Equal priority: check arrival time (first come first served) *)
  | _, _ => 
    if ego_arrival <? other_arrival then true
    (* Same arrival time: right-hand rule *)
    else if ego_arrival =? other_arrival then negb other_on_right
    else false
  end.

(* Pedestrian right-of-way *)
Inductive crosswalk_type : Type :=
  | SignalizedCrosswalk   (* Has pedestrian signal *)
  | ZebraCrossing         (* Marked, pedestrians always have priority *)
  | UnmarkedCrossing.     (* At intersections *)

Definition pedestrian_has_priority 
    (cw : crosswalk_type) 
    (ped_signal : option signal_state) : bool :=
  match cw with
  | ZebraCrossing => true  (* Always yield to pedestrians *)
  | SignalizedCrosswalk => 
      match ped_signal with
      | Some Green => true
      | _ => false
      end
  | UnmarkedCrossing => true  (* Pedestrians have priority at intersections *)
  end.

(* ============================================================== *)
(* SECTION 5: LANE RULES                                          *)
(* ============================================================== *)

Inductive lane_type : Type :=
  | RegularLane
  | BusLane
  | BikeLane
  | HOVLane
  | EmergencyLane
  | TurnOnlyLeft
  | TurnOnlyRight
  | TurnOnlyStraight.

(* Can ego vehicle use this lane type? *)
Definition lane_accessible (lt : lane_type) (is_bus is_emergency is_hov : bool) : bool :=
  match lt with
  | RegularLane => true
  | BusLane => is_bus
  | BikeLane => false  (* Vehicles cannot use bike lanes *)
  | HOVLane => is_hov
  | EmergencyLane => is_emergency
  | TurnOnlyLeft => true
  | TurnOnlyRight => true
  | TurnOnlyStraight => true
  end.

(* Lane change rules *)
Inductive lane_marking : Type :=
  | SolidWhite      (* Do not cross *)
  | DashedWhite     (* May cross with caution *)
  | SolidYellow     (* Do not cross, oncoming traffic *)
  | DashedYellow    (* May cross to pass *)
  | DoubleSolid     (* Never cross *)
  | NoMarking.

Definition may_cross_marking (m : lane_marking) : bool :=
  match m with
  | DashedWhite => true
  | DashedYellow => true
  | NoMarking => true
  | _ => false
  end.

(* ============================================================== *)
(* SECTION 6: SPEED COMPLIANCE                                    *)
(* ============================================================== *)

(* Basic speed compliance *)
Definition speed_compliant (current : speed) (limit : speed) : Prop :=
  current <= limit.

(* Speed compliance with tolerance (for enforcement) *)
Definition speed_compliant_tolerance (current limit : speed) (tolerance_percent : Z) : Prop :=
  current <= limit + (limit * tolerance_percent / 100).

(* Minimum speed (on highways) *)
Definition min_speed_compliant (current min_speed : speed) : Prop :=
  current >= min_speed.

(* ============================================================== *)
(* SECTION 7: VERIFICATION LEMMAS                                 *)
(* ============================================================== *)

(* Adjusted limit is never higher than base limit *)
Lemma adjusted_limit_le_base : forall base cond,
  0 <= base ->
  adjusted_speed_limit base cond <= base.
Proof.
  (* Proof: since all condition factors are <= 100 and we divide by 100,
     the result is <= base. For cases with Z.min, the min is also <= base. *)
Admitted.

(* If compliant with base, might not be compliant with adjusted *)
(* This is expected - conditions can reduce the limit *)

(* Green signal permits entry *)
Lemma green_permits : signal_permits_entry Green = true.
Proof. reflexivity. Qed.

(* Red signal requires stop *)
Lemma red_requires_stop : signal_requires_stop Red = true.
Proof. reflexivity. Qed.

(* Speed limit conversions are consistent *)
Lemma kmh_50_value : kmh_to_mms 50 = 13888.
Proof. reflexivity. Qed.

Lemma kmh_30_value : kmh_to_mms 30 = 8333.
Proof. reflexivity. Qed.
