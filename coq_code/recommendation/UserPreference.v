(* ============================================================== *)
(* UserPreference.v - User Preference and Utility Specification   *)
(* Published by: Consumer Protection Authority (hypothetically)   *)
(* Version: 2024.1                                                *)
(*                                                                *)
(* This file defines how user preferences are represented and     *)
(* how utility scores are computed for products.                  *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Require Import Bool.
Require Import Lia.
Open Scope Z_scope.

(* ============================================================== *)
(* SECTION 1: BASIC UNITS                                         *)
(* All values scaled to avoid floating point arithmetic           *)
(* ============================================================== *)

(* Weight in parts per thousand (0-1000 = 0%-100%) *)
Definition weight := Z.

(* Utility score scaled to milliunits *)
Definition utility_score := Z.

(* Price in cents *)
Definition price := Z.

(* Rating scaled 0-1000 (where 1000 = 5 stars) *)
Definition rating := Z.

(* Timestamp in milliseconds since epoch *)
Definition timestamp := Z.

(* Cryptographic signature placeholder *)
Parameter signature : Type.
Parameter signature_valid : signature -> bool.
Parameter valid_sig : signature.
Axiom valid_sig_is_valid : signature_valid valid_sig = true.

(* ============================================================== *)
(* SECTION 2: PREFERENCE WEIGHTS                                  *)
(* ============================================================== *)

(* User preference weights for different product attributes *)
Record preference_weights := mkWeights {
  w_price : weight;           (* Weight for price optimization *)
  w_quality : weight;         (* Weight for quality/rating *)
  w_features : weight;        (* Weight for feature match *)
  w_brand : weight;           (* Weight for brand preference *)
  w_sustainability : weight;  (* Weight for eco-friendliness *)
}.

(* Default weights: balanced preferences *)
Definition default_weights : preference_weights := mkWeights
  200    (* 20% price *)
  300    (* 30% quality *)
  200    (* 20% features *)
  150    (* 15% brand *)
  150.   (* 15% sustainability *)

(* Weights are valid if non-negative and sum to 1000 *)
Definition weights_valid (w : preference_weights) : Prop :=
  0 <= w_price w /\
  0 <= w_quality w /\
  0 <= w_features w /\
  0 <= w_brand w /\
  0 <= w_sustainability w /\
  w_price w + w_quality w + w_features w + 
    w_brand w + w_sustainability w = 1000.

(* Boolean check for weight validity *)
Definition weights_valid_bool (w : preference_weights) : bool :=
  (0 <=? w_price w) &&
  (0 <=? w_quality w) &&
  (0 <=? w_features w) &&
  (0 <=? w_brand w) &&
  (0 <=? w_sustainability w) &&
  (w_price w + w_quality w + w_features w + 
   w_brand w + w_sustainability w =? 1000).

(* ============================================================== *)
(* SECTION 3: USER CONSTRAINTS                                    *)
(* ============================================================== *)

(* Hard constraints that must be satisfied *)
Record user_constraints := mkConstraints {
  max_budget : price;              (* Maximum acceptable price *)
  min_rating : rating;             (* Minimum acceptable rating *)
  required_features : list nat;    (* Features that must be present *)
  preferred_brands : list nat;     (* Preferred brand IDs *)
  excluded_brands : list nat;      (* Brands to exclude *)
  min_reviews : nat;               (* Minimum review count *)
}.

(* Default constraints: very permissive *)
Definition no_constraints : user_constraints := mkConstraints
  10000000   (* $100,000 budget *)
  0          (* No minimum rating *)
  nil        (* No required features *)
  nil        (* No preferred brands *)
  nil        (* No excluded brands *)
  0.         (* No minimum reviews *)

(* Constraints are valid *)
Definition constraints_valid (c : user_constraints) : Prop :=
  max_budget c > 0 /\
  0 <= min_rating c /\
  min_rating c <= 1000.

(* ============================================================== *)
(* SECTION 4: COMPLETE USER PREFERENCE                            *)
(* ============================================================== *)

(* Signed user preference declaration *)
Record user_preference := mkUserPref {
  pref_user_id : nat;
  pref_weights : preference_weights;
  pref_constraints : user_constraints;
  pref_timestamp : timestamp;
  pref_signature : signature;
}.

(* User preference is valid *)
Definition preference_valid (p : user_preference) : Prop :=
  signature_valid (pref_signature p) = true /\
  weights_valid (pref_weights p) /\
  constraints_valid (pref_constraints p).

(* ============================================================== *)
(* SECTION 5: UTILITY COMPONENT FUNCTIONS                         *)
(* ============================================================== *)

(* Price utility: higher for lower prices relative to budget *)
(* Returns 0-1000 scale *)
Definition price_utility (p : price) (budget : price) : Z :=
  if budget <=? 0 then 0
  else if p >=? budget then 0
  else if p <? 0 then 0
  else (budget - p) * 1000 / budget.

(* Lemma: price utility is bounded *)
Lemma price_utility_bounded : forall p budget,
  0 <= price_utility p budget /\ price_utility p budget <= 1000.
Proof.
  intros p budget.
  unfold price_utility.
  destruct (budget <=? 0) eqn:Hb1.
  - split; lia.
  - destruct (p >=? budget) eqn:Hb2.
    + split; lia.
    + destruct (p <? 0) eqn:Hb3.
      * split; lia.
      * split.
        -- apply Z.div_pos; lia.
        -- apply Z.div_le_upper_bound; lia.
Qed.

(* Quality utility: direct use of rating *)
Definition quality_utility (r : rating) : Z :=
  if r <? 0 then 0
  else if r >? 1000 then 1000
  else r.

(* Feature match: percentage of required features present *)
Definition feature_match_utility 
    (required : list nat) 
    (present : list nat) : Z :=
  let matches := length (filter (fun f => existsb (Nat.eqb f) present) required) in
  let total := length required in
  if (total =? 0)%nat then 1000  (* No requirements = perfect match *)
  else (Z.of_nat matches) * 1000 / (Z.of_nat total).

(* Brand utility *)
Definition brand_utility 
    (brand_id : nat) 
    (preferred : list nat) 
    (excluded : list nat) : Z :=
  if existsb (Nat.eqb brand_id) excluded then 0
  else if existsb (Nat.eqb brand_id) preferred then 1000
  else 500.  (* Neutral for unknown brands *)

(* Sustainability utility: direct use of eco-score *)
Definition sustainability_utility (eco_score : Z) : Z :=
  if eco_score <? 0 then 0
  else if eco_score >? 1000 then 1000
  else eco_score.

(* ============================================================== *)
(* SECTION 6: PRODUCT REPRESENTATION (forward declaration)        *)
(* ============================================================== *)

(* Product type - fully defined in ProductSpec.v *)
Record product := mkProduct {
  prod_id : nat;
  prod_name : nat;
  prod_brand : nat;
  prod_price : price;
  prod_rating : rating;
  prod_review_count : nat;
  prod_features : list nat;
  prod_sustainability : Z;
  prod_availability : bool;
  prod_certified : bool;
}.

(* ============================================================== *)
(* SECTION 7: MAIN UTILITY FUNCTION                               *)
(* ============================================================== *)

(* Check if product meets hard constraints *)
Definition meets_constraints (prod : product) (c : user_constraints) : bool :=
  (prod_price prod <=? max_budget c) &&
  (prod_rating prod >=? min_rating c) &&
  negb (existsb (Nat.eqb (prod_brand prod)) (excluded_brands c)) &&
  (Nat.leb (min_reviews c) (prod_review_count prod)) &&
  (prod_availability prod).

(* THE MAIN UTILITY FUNCTION *)
(* Computes weighted utility score for a product given user preferences *)
Definition compute_utility 
    (prod : product) 
    (prefs : user_preference) : utility_score :=
  let w := pref_weights prefs in
  let c := pref_constraints prefs in
  
  (* If hard constraints not met, utility is 0 *)
  if negb (meets_constraints prod c) then 0
  else
    (* Compute individual utility components *)
    let u_price := price_utility (prod_price prod) (max_budget c) in
    let u_quality := quality_utility (prod_rating prod) in
    let u_features := feature_match_utility 
                        (required_features c) (prod_features prod) in
    let u_brand := brand_utility (prod_brand prod) 
                                 (preferred_brands c) (excluded_brands c) in
    let u_sustain := sustainability_utility (prod_sustainability prod) in
    
    (* Weighted sum, normalized by dividing by 1000 *)
    (w_price w * u_price +
     w_quality w * u_quality +
     w_features w * u_features +
     w_brand w * u_brand +
     w_sustainability w * u_sustain) / 1000.

(* ============================================================== *)
(* SECTION 8: UTILITY COMPARISON                                  *)
(* ============================================================== *)

(* Compare utility of two products *)
Definition utility_greater_eq 
    (p1 p2 : product) 
    (prefs : user_preference) : Prop :=
  compute_utility p1 prefs >= compute_utility p2 prefs.

(* Boolean comparison *)
Definition utility_greater_eq_bool 
    (p1 p2 : product) 
    (prefs : user_preference) : bool :=
  compute_utility p1 prefs >=? compute_utility p2 prefs.

(* Product is utility-maximizing over a list *)
Definition is_utility_maximum 
    (p : product) 
    (catalog : list product) 
    (prefs : user_preference) : bool :=
  forallb (fun other => utility_greater_eq_bool p other prefs) catalog.

(* ============================================================== *)
(* SECTION 9: VERIFICATION LEMMAS                                 *)
(* ============================================================== *)

(* Utility is non-negative *)
Lemma utility_nonneg : forall prod prefs,
  0 <= compute_utility prod prefs.
Proof.
  intros prod prefs.
  unfold compute_utility.
  destruct (negb (meets_constraints prod (pref_constraints prefs))).
  - lia.
  - apply Z.div_pos.
    + (* Sum of non-negative terms is non-negative *)
      (* Each weight is non-negative, each utility is bounded 0-1000 *)
      admit. (* Requires detailed arithmetic proof *)
    + lia.
Admitted.

(* If weights sum to 1000 and all utilities are at most 1000,
   total utility is at most 1000 *)
Lemma utility_bounded : forall prod prefs,
  weights_valid (pref_weights prefs) ->
  compute_utility prod prefs <= 1000.
Proof.
  intros prod prefs Hvalid.
  unfold compute_utility.
  destruct (negb (meets_constraints prod (pref_constraints prefs))).
  - lia.
  - (* Maximum case: all utility components are 1000 *)
    (* Then sum = 1000 * 1000 = 1000000, divided by 1000 = 1000 *)
    admit.
Admitted.

(* Reflexivity of utility comparison *)
Lemma utility_refl : forall p prefs,
  utility_greater_eq p p prefs.
Proof.
  intros p prefs.
  unfold utility_greater_eq.
  lia.
Qed.

(* Default weights are valid *)
Lemma default_weights_valid : weights_valid default_weights.
Proof.
  unfold weights_valid, default_weights. simpl.
  repeat split; lia.
Qed.
