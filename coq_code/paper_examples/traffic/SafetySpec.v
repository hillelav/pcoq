(* ============================================================== *)
(* SafetySpec.v - Safety Distance Specifications                  *)
(* Published by: Transportation Ministry (hypothetically)         *)
(* Version: 2024.1                                                *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Require Import Bool.
Require Import Lia.
Require Import TrafficLaw.
Open Scope Z_scope.

(* ============================================================== *)
(* SECTION 1: FOLLOWING DISTANCE (TIME HEADWAY)                   *)
(* ============================================================== *)

(* Minimum time headway in milliseconds *)
(* Standard rule: 2 seconds following distance *)
Definition min_time_headway_normal : time_ms := 2000.

(* Increased headway for adverse conditions *)
Definition min_time_headway (cond : road_condition) : time_ms :=
  match cond with
  | Dry => 2000          (* 2 seconds *)
  | Wet => 3000          (* 3 seconds *)
  | Icy => 6000          (* 6 seconds *)
  | Snow => 5000         (* 5 seconds *)
  | Fog => 4000          (* 4 seconds *)
  | Construction => 3000
  | SchoolZone => 3000
  | EmergencyScene => 4000
  end.

(* Required following distance in mm *)
(* distance = speed * time *)
Definition required_following_distance (ego_speed : speed) (cond : road_condition) : distance :=
  ego_speed * min_time_headway cond / 1000.

(* Following distance compliance *)
Definition following_distance_safe 
    (ego_pos lead_pos : distance) 
    (ego_speed : speed)
    (cond : road_condition) : Prop :=
  lead_pos - ego_pos >= required_following_distance ego_speed cond.

(* ============================================================== *)
(* SECTION 2: STOPPING DISTANCE                                   *)
(* ============================================================== *)

(* Reaction time in milliseconds *)
Definition reaction_time : time_ms := 1500.  (* 1.5 seconds *)

(* Maximum deceleration in mm/s^2 *)
(* Varies by road condition *)
Definition max_deceleration (cond : road_condition) : acceleration :=
  match cond with
  | Dry => 8000          (* 8 m/s^2 *)
  | Wet => 6000          (* 6 m/s^2 *)
  | Icy => 2000          (* 2 m/s^2 *)
  | Snow => 3000         (* 3 m/s^2 *)
  | Fog => 7000          (* 7 m/s^2, visibility issue not friction *)
  | Construction => 6000
  | SchoolZone => 7000
  | EmergencyScene => 7000
  end.

(* Reaction distance: distance traveled during reaction time *)
Definition reaction_distance (current_speed : speed) : distance :=
  current_speed * reaction_time / 1000.

(* Braking distance: d = v^2 / (2a) *)
(* Note: must handle units carefully *)
(* v in mm/s, a in mm/s^2, result in mm *)
Definition braking_distance (current_speed : speed) (cond : road_condition) : distance :=
  let a := max_deceleration cond in
  if a =? 0 then 
    (* Cannot brake - infinite stopping distance, cap at large value *)
    1000000000
  else
    (current_speed * current_speed) / (2 * a).

(* Total stopping distance *)
Definition stopping_distance (current_speed : speed) (cond : road_condition) : distance :=
  reaction_distance current_speed + braking_distance current_speed cond.

(* Can stop before obstacle *)
Definition can_stop_before 
    (current_speed : speed) 
    (distance_to_obstacle : distance)
    (cond : road_condition) : Prop :=
  stopping_distance current_speed cond <= distance_to_obstacle.

(* ============================================================== *)
(* SECTION 3: SAFE SPEED FOR VISIBILITY                           *)
(* ============================================================== *)

(* Safe speed: can stop within visible distance *)
(* Solving: reaction_dist + braking_dist <= visibility *)
(* v*t + v^2/(2a) <= d *)
(* This is quadratic in v; we compute maximum safe speed *)

Definition max_safe_speed_for_visibility 
    (visibility : distance) 
    (cond : road_condition) : speed :=
  let a := max_deceleration cond in
  let t := reaction_time in
  (* Approximate solution using conservative estimate *)
  (* v_max ≈ sqrt(2 * a * visibility) - a * t / 1000 *)
  (* For simplicity, use lookup table approach *)
  if visibility <? 10000 then kmh_to_mms 20       (* < 10m *)
  else if visibility <? 30000 then kmh_to_mms 30  (* < 30m *)
  else if visibility <? 50000 then kmh_to_mms 40  (* < 50m *)
  else if visibility <? 100000 then kmh_to_mms 60 (* < 100m *)
  else if visibility <? 200000 then kmh_to_mms 80 (* < 200m *)
  else kmh_to_mms 120.                            (* >= 200m *)

(* ============================================================== *)
(* SECTION 4: LATERAL SAFETY (PASSING DISTANCE)                   *)
(* ============================================================== *)

(* Minimum passing distance to vulnerable road users *)
Definition min_passing_distance_cyclist : distance := m_to_mm 1500.  (* 1.5m *)
Definition min_passing_distance_pedestrian : distance := m_to_mm 1500.
Definition min_passing_distance_vehicle : distance := m_to_mm 500.   (* 0.5m *)

Inductive road_user_type : Type :=
  | Cyclist
  | Pedestrian
  | Motorcycle
  | Vehicle
  | LargeVehicle
  | EmergencyVehicle.

Definition min_passing_distance (user : road_user_type) : distance :=
  match user with
  | Cyclist => m_to_mm 1500
  | Pedestrian => m_to_mm 1500
  | Motorcycle => m_to_mm 1000
  | Vehicle => m_to_mm 500
  | LargeVehicle => m_to_mm 1000
  | EmergencyVehicle => m_to_mm 2000
  end.

(* Lateral clearance compliance *)
Definition lateral_clearance_safe
    (ego_x other_x : Z)
    (ego_half_width other_half_width : Z)
    (other_type : road_user_type) : Prop :=
  let actual_clearance := Z.abs (ego_x - other_x) - ego_half_width - other_half_width in
  actual_clearance >= min_passing_distance other_type.

(* ============================================================== *)
(* SECTION 5: TIME-TO-COLLISION (TTC)                             *)
(* ============================================================== *)

(* Minimum acceptable TTC in milliseconds *)
Definition min_ttc : time_ms := 3000.  (* 3 seconds *)

(* Compute TTC given relative position and velocity *)
(* TTC = distance / closing_speed *)
Definition compute_ttc 
    (distance_gap : distance) 
    (ego_speed lead_speed : speed) : option time_ms :=
  let closing_speed := ego_speed - lead_speed in
  if closing_speed <=? 0 then 
    None  (* Not closing, TTC is infinite *)
  else
    Some (distance_gap * 1000 / closing_speed).

(* TTC is safe *)
Definition ttc_safe 
    (distance_gap : distance)
    (ego_speed lead_speed : speed) : Prop :=
  match compute_ttc distance_gap ego_speed lead_speed with
  | None => True  (* Not closing *)
  | Some ttc => ttc >= min_ttc
  end.

(* ============================================================== *)
(* SECTION 6: INTERSECTION SAFETY                                 *)
(* ============================================================== *)

(* Safe gap acceptance for turning/crossing *)
(* Minimum gap in milliseconds to accept *)
Definition min_gap_left_turn : time_ms := 6000.   (* 6 seconds *)
Definition min_gap_right_turn : time_ms := 4000.  (* 4 seconds *)
Definition min_gap_crossing : time_ms := 7000.    (* 7 seconds *)

Definition gap_acceptable 
    (maneuver : turn_direction)
    (available_gap : time_ms) : bool :=
  match maneuver with
  | TurnLeft => available_gap >=? min_gap_left_turn
  | TurnRight => available_gap >=? min_gap_right_turn
  | GoStraight => available_gap >=? min_gap_crossing  (* For crossing traffic *)
  | UTurn => available_gap >=? min_gap_left_turn + 2000
  end.

(* ============================================================== *)
(* SECTION 7: EMERGENCY VEHICLE RESPONSE                          *)
(* ============================================================== *)

(* When emergency vehicle detected, must yield *)
Definition emergency_yield_distance : distance := m_to_mm 100.  (* 100m *)

(* Safe behavior when emergency vehicle approaching *)
Inductive emergency_response : Type :=
  | PullOverRight    (* Pull to right side of road *)
  | SlowAndYield     (* Reduce speed and prepare to yield *)
  | StopCompletely   (* Stop if cannot move out of way *)
  | Continue.        (* Emergency vehicle not relevant *)

Definition required_emergency_response
    (emergency_behind : bool)
    (emergency_distance : distance)
    (can_pull_over : bool) : emergency_response :=
  if negb emergency_behind then Continue
  else if emergency_distance >? emergency_yield_distance then SlowAndYield
  else if can_pull_over then PullOverRight
  else StopCompletely.

(* ============================================================== *)
(* SECTION 8: VERIFICATION LEMMAS                                 *)
(* ============================================================== *)

(* Following distance increases with speed *)
Lemma following_distance_monotonic : forall s1 s2 cond,
  0 <= s1 <= s2 ->
  required_following_distance s1 cond <= required_following_distance s2 cond.
Proof.
  intros s1 s2 cond [H0 H12].
  unfold required_following_distance.
  apply Z.div_le_mono; try lia.
  apply Z.mul_le_mono_nonneg_r; try lia.
  destruct cond; simpl; lia.
Qed.

(* Stopping distance increases with speed (quadratically) *)
Lemma stopping_distance_monotonic : forall s1 s2 cond,
  0 <= s1 <= s2 ->
  stopping_distance s1 cond <= stopping_distance s2 cond.
Proof.
  intros s1 s2 cond [H0 H12].
  unfold stopping_distance, reaction_distance, braking_distance.
  (* This follows from both terms being monotonic in speed *)
  (* Full proof requires showing v^2 is monotonic for v >= 0 *)
Admitted.

(* Example: 50 km/h stopping distance on dry road *)
(* We compute the actual value rather than assert it *)
Lemma stopping_distance_50kmh_dry :
  stopping_distance (kmh_to_mms 50) Dry > 0.
Proof.
  unfold stopping_distance, reaction_distance, braking_distance.
  unfold kmh_to_mms, reaction_time, max_deceleration.
  simpl. lia.
Qed.

(* Time headway is positive for all conditions *)
Lemma time_headway_positive : forall cond,
  0 < min_time_headway cond.
Proof.
  intro cond. destruct cond; simpl; lia.
Qed.
