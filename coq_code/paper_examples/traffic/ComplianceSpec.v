(* ============================================================== *)
(* ComplianceSpec.v - Main Compliance Specification               *)
(* Published by: Transportation Ministry (hypothetically)         *)
(* Version: 2024.1                                                *)
(*                                                                *)
(* This file defines THE COMPLIANCE PREDICATE that vehicle AIs    *)
(* must prove their actions satisfy.                              *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Require Import Bool.
Require Import Lia.
Require Import TrafficLaw.
Require Import SafetySpec.
Open Scope Z_scope.

(* ============================================================== *)
(* SECTION 1: POSITION AND GEOMETRY                               *)
(* ============================================================== *)

(* 2D position in local coordinates (mm) *)
Record position := mkPos {
  pos_x : Z;  (* Lateral: negative=left, positive=right of lane center *)
  pos_y : Z;  (* Longitudinal: along direction of travel *)
}.

Definition origin : position := mkPos 0 0.

(* Distance between two positions *)
Definition pos_distance (p1 p2 : position) : distance :=
  let dx := pos_x p1 - pos_x p2 in
  let dy := pos_y p1 - pos_y p2 in
  (* Approximate Euclidean distance using max + min/2 *)
  let ax := Z.abs dx in
  let ay := Z.abs dy in
  Z.max ax ay + Z.min ax ay / 2.

(* Longitudinal distance (along road) *)
Definition longitudinal_distance (ego lead : position) : distance :=
  pos_y lead - pos_y ego.

(* ============================================================== *)
(* SECTION 2: VEHICLE STATE                                       *)
(* ============================================================== *)

Record vehicle_state := mkVehState {
  veh_position : position;
  veh_speed : speed;
  veh_acceleration : acceleration;
  veh_heading : angle;           (* millidegrees, 0 = north *)
  veh_width : distance;          (* vehicle width in mm *)
  veh_length : distance;         (* vehicle length in mm *)
  veh_type : road_user_type;
}.

(* Project vehicle state forward in time *)
Definition project_state (s : vehicle_state) (dt : time_ms) : vehicle_state :=
  let new_speed := veh_speed s + veh_acceleration s * dt / 1000 in
  let avg_speed := (veh_speed s + new_speed) / 2 in
  let new_y := pos_y (veh_position s) + avg_speed * dt / 1000 in
  mkVehState
    (mkPos (pos_x (veh_position s)) new_y)
    new_speed
    (veh_acceleration s)
    (veh_heading s)
    (veh_width s)
    (veh_length s)
    (veh_type s).

(* ============================================================== *)
(* SECTION 3: LANE REPRESENTATION                                 *)
(* ============================================================== *)

Record lane := mkLane {
  lane_id : nat;
  lane_left_edge : Z;            (* x coordinate of left boundary *)
  lane_right_edge : Z;           (* x coordinate of right boundary *)
  lane_center : Z;               (* x coordinate of center line *)
  lane_speed_limit : speed;
  lane_type : lane_type;
  lane_direction : bool;         (* true = same direction as ego *)
  lane_left_marking : lane_marking;
  lane_right_marking : lane_marking;
}.

Definition lane_width (l : lane) : distance :=
  lane_right_edge l - lane_left_edge l.

(* Check if position is within lane boundaries *)
Definition in_lane (p : position) (veh_width : distance) (l : lane) : Prop :=
  let half_width := veh_width / 2 in
  pos_x p - half_width >= lane_left_edge l /\
  pos_x p + half_width <= lane_right_edge l.

Definition in_lane_bool (p : position) (veh_width : distance) (l : lane) : bool :=
  let half_width := veh_width / 2 in
  (pos_x p - half_width >=? lane_left_edge l) &&
  (pos_x p + half_width <=? lane_right_edge l).

(* ============================================================== *)
(* SECTION 4: DETECTED OBJECTS                                    *)
(* ============================================================== *)

Inductive object_class : Type :=
  | ObjVehicle
  | ObjPedestrian
  | ObjCyclist
  | ObjMotorcycle
  | ObjStatic         (* Static obstacle *)
  | ObjUnknown.

Record detected_object := mkDetObj {
  obj_id : nat;
  obj_class : object_class;
  obj_position : position;
  obj_position_uncertainty : distance;  (* Radius of uncertainty *)
  obj_velocity : speed;                 (* Along road direction *)
  obj_velocity_uncertainty : speed;
  obj_width : distance;
  obj_length : distance;
  obj_timestamp : time_ms;
}.

(* Conservative (closest) position estimate *)
Definition obj_closest_y (obj : detected_object) : Z :=
  pos_y (obj_position obj) - obj_position_uncertainty obj - obj_length obj / 2.

(* Conservative (farthest) position estimate *)
Definition obj_farthest_y (obj : detected_object) : Z :=
  pos_y (obj_position obj) + obj_position_uncertainty obj + obj_length obj / 2.

(* Conservative (fastest) speed estimate *)
Definition obj_max_speed (obj : detected_object) : speed :=
  obj_velocity obj + obj_velocity_uncertainty obj.

(* ============================================================== *)
(* SECTION 5: SIGNAL AND MAP DATA                                 *)
(* ============================================================== *)

(* Cryptographic signature placeholder *)
Parameter signature : Type.
Parameter signature_valid : signature -> bool.
Parameter valid_sig : signature.
Axiom valid_sig_is_valid : signature_valid valid_sig = true.

Record signal_message := mkSignalMsg {
  sig_intersection_id : nat;
  sig_approach_id : nat;
  sig_state : signal_state;
  sig_time_to_change : option time_ms;
  sig_timestamp : time_ms;
  sig_signature : signature;
}.

Record map_segment := mkMapSeg {
  seg_id : nat;
  seg_lanes : list lane;
  seg_speed_limit : speed;
  seg_valid_from : time_ms;
  seg_valid_until : time_ms;
  seg_signature : signature;
}.

(* ============================================================== *)
(* SECTION 6: ENVIRONMENT SNAPSHOT                                *)
(* ============================================================== *)

Record environment := mkEnv {
  env_map : map_segment;
  env_signals : list signal_message;
  env_objects : list detected_object;
  env_condition : road_condition;
  env_visibility : distance;
  env_timestamp : time_ms;
}.

(* Find current lane from map *)
Definition find_current_lane (m : map_segment) (p : position) : option lane :=
  let matching := filter (fun l => in_lane_bool p 0 l) (seg_lanes m) in
  hd_error matching.

(* Get speed limit for current location *)
Definition current_speed_limit (env : environment) (p : position) : speed :=
  match find_current_lane (env_map env) p with
  | Some l => adjusted_speed_limit (lane_speed_limit l) (env_condition env)
  | None => adjusted_speed_limit (seg_speed_limit (env_map env)) (env_condition env)
  end.

(* Get relevant signal for current position *)
Definition get_signal (env : environment) (intersection_id : nat) : option signal_message :=
  find (fun s => Nat.eqb (sig_intersection_id s) intersection_id) (env_signals env).

(* Find objects ahead in current lane *)
Definition objects_ahead (env : environment) (ego : vehicle_state) : list detected_object :=
  filter (fun obj => 
    (pos_y (obj_position obj) >? pos_y (veh_position ego)) &&
    (Z.abs (pos_x (obj_position obj) - pos_x (veh_position ego)) <? 2000)
  ) (env_objects env).

(* Distance to nearest object ahead *)
Definition distance_to_nearest_ahead (env : environment) (ego : vehicle_state) : option distance :=
  let ahead := objects_ahead env ego in
  match ahead with
  | nil => None
  | objs => 
      let distances := map (fun o => obj_closest_y o - pos_y (veh_position ego) - veh_length ego / 2) objs in
      Some (fold_right Z.min (hd 1000000000 distances) distances)
  end.

(* ============================================================== *)
(* SECTION 7: DRIVING ACTION                                      *)
(* ============================================================== *)

Record driving_action := mkAction {
  act_acceleration : acceleration;   (* Commanded acceleration *)
  act_steering : angle;              (* Steering angle change *)
  act_timestamp : time_ms;
}.

(* No action (maintain current state) *)
Definition no_action : driving_action := mkAction 0 0 0.

(* Project speed after action *)
Definition projected_speed (current : speed) (action : driving_action) (dt : time_ms) : speed :=
  Z.max 0 (current + act_acceleration action * dt / 1000).

(* ============================================================== *)
(* SECTION 8: THE COMPLIANCE PREDICATE                            *)
(* ============================================================== *)

(* Individual compliance components *)

Definition speed_limit_compliant 
    (state : vehicle_state) 
    (env : environment)
    (action : driving_action) : Prop :=
  let current := veh_speed state in
  let proj := projected_speed current action 100 in (* 100ms lookahead *)
  let limit := current_speed_limit env (veh_position state) in
  proj <= limit.

Definition following_distance_compliant
    (state : vehicle_state)
    (env : environment) : Prop :=
  forall obj,
    In obj (env_objects env) ->
    obj_class obj = ObjVehicle ->
    pos_y (obj_position obj) > pos_y (veh_position state) ->
    following_distance_safe
      (pos_y (veh_position state))
      (obj_closest_y obj)
      (veh_speed state)
      (env_condition env).

Definition lane_position_compliant
    (state : vehicle_state)
    (env : environment) : Prop :=
  match find_current_lane (env_map env) (veh_position state) with
  | Some l => in_lane (veh_position state) (veh_width state) l
  | None => False  (* Must be in a valid lane *)
  end.

Definition signal_compliant
    (state : vehicle_state)
    (env : environment) : Prop :=
  forall sig,
    In sig (env_signals env) ->
    sig_timestamp sig + 500 >= env_timestamp env ->  (* Signal is fresh *)
    (* If approaching intersection with red signal, must be stopped or stopping *)
    (signal_requires_stop (sig_state sig) = true ->
     veh_speed state = 0 \/ veh_acceleration state < 0).

Definition stopping_capability_compliant
    (state : vehicle_state)
    (env : environment) : Prop :=
  match distance_to_nearest_ahead env state with
  | None => True  (* No obstacle ahead *)
  | Some d => can_stop_before (veh_speed state) d (env_condition env)
  end.

Definition visibility_speed_compliant
    (state : vehicle_state)
    (env : environment) : Prop :=
  veh_speed state <= max_safe_speed_for_visibility (env_visibility env) (env_condition env).

(* ============================================================== *)
(* THE MAIN COMPLIANCE PREDICATE                                  *)
(* This is what vehicle AI must prove for every action            *)
(* ============================================================== *)

Definition action_compliant
    (state : vehicle_state)
    (env : environment)
    (action : driving_action) : Prop :=
  (* 1. Speed limit compliance *)
  speed_limit_compliant state env action /\
  (* 2. Following distance compliance *)
  following_distance_compliant state env /\
  (* 3. Lane position compliance *)
  lane_position_compliant state env /\
  (* 4. Traffic signal compliance *)
  signal_compliant state env /\
  (* 5. Can stop before obstacles *)
  stopping_capability_compliant state env /\
  (* 6. Speed appropriate for visibility *)
  visibility_speed_compliant state env.

(* ============================================================== *)
(* SECTION 9: DECIDABLE COMPLIANCE (for runtime checking)         *)
(* ============================================================== *)

(* Simplified boolean check for runtime *)
Definition action_compliant_quick
    (state : vehicle_state)
    (env : environment)
    (action : driving_action) : bool :=
  let proj_speed := projected_speed (veh_speed state) action 100 in
  let limit := current_speed_limit env (veh_position state) in
  (proj_speed <=? limit) &&
  (veh_speed state <=? max_safe_speed_for_visibility (env_visibility env) (env_condition env)) &&
  match distance_to_nearest_ahead env state with
  | None => true
  | Some d => stopping_distance (veh_speed state) (env_condition env) <=? d
  end.

(* ============================================================== *)
(* SECTION 10: COMPLIANCE RECORD FOR LOGGING                      *)
(* ============================================================== *)

Record compliance_record := mkCompRec {
  rec_timestamp : time_ms;
  rec_state : vehicle_state;
  rec_env : environment;
  rec_action : driving_action;
  rec_compliant : bool;
  rec_signature : signature;
}.

(* Verify a logged compliance record *)
Definition verify_record (rec : compliance_record) : bool :=
  signature_valid (rec_signature rec) &&
  action_compliant_quick (rec_state rec) (rec_env rec) (rec_action rec).
