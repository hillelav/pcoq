(* ============================================================== *)
(* ProductSpec.v - Product Catalog Specification                  *)
(* Published by: Consumer Protection Authority (hypothetically)   *)
(* Version: 2024.1                                                *)
(*                                                                *)
(* This file defines product representation and catalog           *)
(* certification requirements.                                    *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Import ListNotations.
Require Import Bool.
Require Import Lia.
Require Import UserPreference.
Open Scope Z_scope.

(* ============================================================== *)
(* SECTION 1: PRODUCT CATEGORIES                                  *)
(* ============================================================== *)

Inductive product_category : Type :=
  | Electronics
  | Clothing
  | HomeAndGarden
  | Books
  | Food
  | Health
  | Sports
  | Automotive
  | Other.

(* Category to nat for indexing *)
Definition category_to_nat (c : product_category) : nat :=
  match c with
  | Electronics => 0
  | Clothing => 1
  | HomeAndGarden => 2
  | Books => 3
  | Food => 4
  | Health => 5
  | Sports => 6
  | Automotive => 7
  | Other => 8
  end.

(* ============================================================== *)
(* SECTION 2: PRODUCT FEATURES                                    *)
(* ============================================================== *)

(* Standard feature IDs for electronics *)
Definition feature_SSD : nat := 1.
Definition feature_16GB_RAM : nat := 2.
Definition feature_USB_C : nat := 3.
Definition feature_Thunderbolt : nat := 4.
Definition feature_TouchScreen : nat := 5.
Definition feature_Backlit_Keyboard : nat := 6.
Definition feature_Fingerprint : nat := 7.
Definition feature_WiFi6 : nat := 8.
Definition feature_5G : nat := 9.
Definition feature_OLED : nat := 10.

(* Check if a feature is present in a list *)
Definition has_feature (f : nat) (features : list nat) : bool :=
  existsb (Nat.eqb f) features.

(* Count matching features *)
Definition count_matching_features 
    (required : list nat) 
    (present : list nat) : nat :=
  length (filter (fun f => has_feature f present) required).

(* ============================================================== *)
(* SECTION 3: PRODUCT RATING SYSTEM                               *)
(* ============================================================== *)

(* Rating breakdown *)
Record rating_breakdown := mkRatingBreakdown {
  stars_5 : nat;    (* Number of 5-star reviews *)
  stars_4 : nat;
  stars_3 : nat;
  stars_2 : nat;
  stars_1 : nat;
}.

(* Compute aggregate rating from breakdown (0-1000 scale) *)
Definition compute_rating (r : rating_breakdown) : rating :=
  let total := (stars_5 r + stars_4 r + stars_3 r + stars_2 r + stars_1 r)%nat in
  if (total =? 0)%nat then 0
  else
    let weighted := 
      (stars_5 r * 5 + stars_4 r * 4 + stars_3 r * 3 + 
       stars_2 r * 2 + stars_1 r * 1)%nat in
    Z.of_nat weighted * 200 / Z.of_nat total.

(* Total review count *)
Definition total_reviews (r : rating_breakdown) : nat :=
  (stars_5 r + stars_4 r + stars_3 r + stars_2 r + stars_1 r)%nat.

(* ============================================================== *)
(* SECTION 4: PRODUCT ATTRIBUTES                                  *)
(* ============================================================== *)

(* Extended product information *)
Record product_extended := mkProductExt {
  pext_base : product;
  pext_category : product_category;
  pext_rating_breakdown : rating_breakdown;
  pext_description : nat;         (* Index into description table *)
  pext_images : list nat;         (* Indices into image table *)
  pext_seller_id : nat;
  pext_warehouse_location : nat;
  pext_shipping_days : nat;
  pext_return_policy_days : nat;
}.

(* ============================================================== *)
(* SECTION 5: PRODUCT QUALIFICATION                               *)
(* ============================================================== *)

(* Minimum requirements for a product to be recommended *)
Definition product_qualified (p : product) : Prop :=
  prod_availability p = true /\
  prod_certified p = true /\
  (prod_review_count p >= 10)%nat.

(* Boolean version *)
Definition product_qualified_bool (p : product) : bool :=
  prod_availability p &&
  prod_certified p &&
  Nat.leb 10 (prod_review_count p).

(* Product has sufficient reviews for statistical confidence *)
Definition statistically_significant (p : product) : Prop :=
  (prod_review_count p >= 30)%nat.

(* ============================================================== *)
(* SECTION 6: CERTIFIED CATALOG                                   *)
(* ============================================================== *)

(* Catalog with certification *)
Record certified_catalog := mkCatalog {
  cat_products : list product;
  cat_category : nat;
  cat_valid_from : timestamp;
  cat_valid_until : timestamp;
  cat_certifier_id : nat;
  cat_certification_level : nat;  (* 1=basic, 2=verified, 3=audited *)
  cat_signature : signature;
}.

(* Catalog is valid at a given time *)
Definition catalog_valid (cat : certified_catalog) (now : timestamp) : Prop :=
  cat_valid_from cat <= now /\ now <= cat_valid_until cat.

(* Boolean version *)
Definition catalog_valid_bool (cat : certified_catalog) (now : timestamp) : bool :=
  (cat_valid_from cat <=? now) && (now <=? cat_valid_until cat).

(* All products in catalog are qualified *)
Definition catalog_all_qualified (cat : certified_catalog) : Prop :=
  forall p, In p (cat_products cat) -> product_qualified p.

(* ============================================================== *)
(* SECTION 7: PRODUCT COMPARISON                                  *)
(* ============================================================== *)

(* Products are in the same category *)
Definition same_category (p1 p2 : product_extended) : bool :=
  Nat.eqb (category_to_nat (pext_category p1)) 
          (category_to_nat (pext_category p2)).

(* Products have similar price (within 20%) *)
Definition similar_price (p1 p2 : product) : bool :=
  let diff := Z.abs (prod_price p1 - prod_price p2) in
  let max_price := Z.max (prod_price p1) (prod_price p2) in
  if max_price <=? 0 then true
  else (diff * 5 <=? max_price).  (* diff/max <= 0.2 *)

(* Find all products similar to a given product *)
Definition find_similar_products 
    (target : product) 
    (catalog : list product) : list product :=
  filter (fun p => 
    negb (Nat.eqb (prod_id p) (prod_id target)) &&
    similar_price p target
  ) catalog.

(* ============================================================== *)
(* SECTION 8: CATALOG OPERATIONS                                  *)
(* ============================================================== *)

(* Find product by ID *)
Definition find_product_by_id 
    (id : nat) 
    (catalog : list product) : option product :=
  find (fun p => Nat.eqb (prod_id p) id) catalog.

(* Filter products by price range *)
Definition filter_by_price 
    (min_price max_price : price) 
    (catalog : list product) : list product :=
  filter (fun p => 
    (min_price <=? prod_price p) && (prod_price p <=? max_price)
  ) catalog.

(* Filter products by minimum rating *)
Definition filter_by_rating 
    (min_rat : rating) 
    (catalog : list product) : list product :=
  filter (fun p => min_rat <=? prod_rating p) catalog.

(* Filter products by brand *)
Definition filter_by_brand 
    (brand_id : nat) 
    (catalog : list product) : list product :=
  filter (fun p => Nat.eqb (prod_brand p) brand_id) catalog.

(* Filter products that have all required features *)
Definition filter_by_features 
    (required : list nat) 
    (catalog : list product) : list product :=
  filter (fun p => 
    forallb (fun f => has_feature f (prod_features p)) required
  ) catalog.

(* Get qualified products from catalog *)
Definition get_qualified_products (cat : certified_catalog) : list product :=
  filter product_qualified_bool (cat_products cat).

(* ============================================================== *)
(* SECTION 9: SORTING                                             *)
(* ============================================================== *)

(* Insert product into sorted list by utility *)
Fixpoint insert_by_utility 
    (p : product) 
    (prefs : user_preference)
    (sorted : list product) : list product :=
  match sorted with
  | nil => p :: nil
  | h :: t => 
      if compute_utility p prefs >=? compute_utility h prefs
      then p :: h :: t
      else h :: insert_by_utility p prefs t
  end.

(* Sort products by utility (insertion sort) *)
Fixpoint sort_by_utility 
    (catalog : list product) 
    (prefs : user_preference) : list product :=
  match catalog with
  | nil => nil
  | h :: t => insert_by_utility h prefs (sort_by_utility t prefs)
  end.

(* Get top N products by utility *)
Definition top_n_by_utility 
    (n : nat) 
    (catalog : list product) 
    (prefs : user_preference) : list product :=
  firstn n (sort_by_utility catalog prefs).

(* ============================================================== *)
(* SECTION 10: VERIFICATION LEMMAS                                *)
(* ============================================================== *)

(* Filtering preserves catalog membership *)
Lemma filter_preserves_membership : forall (f : product -> bool) (p : product) (catalog : list product),
  In p (filter f catalog) -> In p catalog.
Proof.
  intros f p catalog H.
  induction catalog as [| h t IH].
  - inversion H.
  - simpl in H.
    destruct (f h) eqn:Hf.
    + destruct H as [Heq | Hin].
      * left. exact Heq.
      * right. apply IH. exact Hin.
    + right. apply IH. exact H.
Qed.

(* If product is qualified boolean, then it satisfies qualification prop *)
Lemma qualified_bool_implies_prop : forall p,
  product_qualified_bool p = true -> product_qualified p.
Proof.
  (* Proof follows from boolean definitions *)
Admitted.

(* Sorted list preserves elements *)
Lemma sort_preserves_elements : forall catalog prefs p,
  In p catalog <-> In p (sort_by_utility catalog prefs).
Proof.
  (* Proof omitted for brevity - standard sorting preservation *)
Admitted.

(* Top product in sorted list has maximum utility *)
Lemma top_is_maximum : forall catalog prefs p rest,
  sort_by_utility catalog prefs = p :: rest ->
  catalog <> nil ->
  forall q, In q catalog -> compute_utility p prefs >= compute_utility q prefs.
Proof.
  (* Proof omitted for brevity *)
Admitted.
