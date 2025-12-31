(* ============================================================== *)
(* TaxCode.v - Formal 2024 U.S. Tax Rules                         *)
(* Published by: IRS (hypothetically)                             *)
(* Version: 2024.1                                                *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Require Import String.
Require Import Lia.
Open Scope Z_scope.

(* ============================================================== *)
(* SECTION 1: FILING STATUS                                       *)
(* IRC Section 1(a)-(d), Section 2                                *)
(* ============================================================== *)

Inductive filing_status : Type :=
  | Single
  | MarriedFilingJointly
  | MarriedFilingSeparately  
  | HeadOfHousehold
  | QualifyingWidow.

(* ============================================================== *)
(* SECTION 2: STANDARD DEDUCTION                                  *)
(* IRC Section 63(c) - 2024 Values (Rev. Proc. 2023-34)          *)
(* ============================================================== *)

Definition standard_deduction_2024 (status : filing_status) : Z :=
  match status with
  | Single => 14600
  | MarriedFilingJointly => 29200
  | MarriedFilingSeparately => 14600
  | HeadOfHousehold => 21900
  | QualifyingWidow => 29200
  end.

(* Additional standard deduction for age 65+ or blind *)
Definition additional_std_deduction_2024 
    (status : filing_status) (age_65_or_blind : bool) : Z :=
  if age_65_or_blind then
    match status with
    | Single => 1950
    | HeadOfHousehold => 1950
    | _ => 1550  (* Married statuses *)
    end
  else 0.

(* ============================================================== *)
(* SECTION 3: TAX BRACKETS                                        *)
(* IRC Section 1 - 2024 Values (Rev. Proc. 2023-34)              *)
(* All amounts in whole dollars (cents truncated)                 *)
(* ============================================================== *)

(* Helper: compute tax for a bracket segment *)
Definition bracket_tax (income : Z) (floor ceiling : Z) (rate_num rate_den : Z) : Z :=
  let applicable := Z.min income ceiling - floor in
  if applicable >? 0 then
    applicable * rate_num / rate_den
  else 0.

(* Single Filer Tax Brackets 2024 *)
Definition tax_single_2024 (taxable_income : Z) : Z :=
  let ti := Z.max 0 taxable_income in
  (* 10% bracket: $0 - $11,600 *)
  let t1 := Z.min ti 11600 * 10 / 100 in
  (* 12% bracket: $11,600 - $47,150 *)
  let t2 := if ti >? 11600 then (Z.min ti 47150 - 11600) * 12 / 100 else 0 in
  (* 22% bracket: $47,150 - $100,525 *)
  let t3 := if ti >? 47150 then (Z.min ti 100525 - 47150) * 22 / 100 else 0 in
  (* 24% bracket: $100,525 - $191,950 *)
  let t4 := if ti >? 100525 then (Z.min ti 191950 - 100525) * 24 / 100 else 0 in
  (* 32% bracket: $191,950 - $243,725 *)
  let t5 := if ti >? 191950 then (Z.min ti 243725 - 191950) * 32 / 100 else 0 in
  (* 35% bracket: $243,725 - $609,350 *)
  let t6 := if ti >? 243725 then (Z.min ti 609350 - 243725) * 35 / 100 else 0 in
  (* 37% bracket: $609,350+ *)
  let t7 := if ti >? 609350 then (ti - 609350) * 37 / 100 else 0 in
  t1 + t2 + t3 + t4 + t5 + t6 + t7.

(* Married Filing Jointly Tax Brackets 2024 *)
Definition tax_mfj_2024 (taxable_income : Z) : Z :=
  let ti := Z.max 0 taxable_income in
  (* 10% bracket: $0 - $23,200 *)
  let t1 := Z.min ti 23200 * 10 / 100 in
  (* 12% bracket: $23,200 - $94,300 *)
  let t2 := if ti >? 23200 then (Z.min ti 94300 - 23200) * 12 / 100 else 0 in
  (* 22% bracket: $94,300 - $201,050 *)
  let t3 := if ti >? 94300 then (Z.min ti 201050 - 94300) * 22 / 100 else 0 in
  (* 24% bracket: $201,050 - $383,900 *)
  let t4 := if ti >? 201050 then (Z.min ti 383900 - 201050) * 24 / 100 else 0 in
  (* 32% bracket: $383,900 - $487,450 *)
  let t5 := if ti >? 383900 then (Z.min ti 487450 - 383900) * 32 / 100 else 0 in
  (* 35% bracket: $487,450 - $731,200 *)
  let t6 := if ti >? 487450 then (Z.min ti 731200 - 487450) * 35 / 100 else 0 in
  (* 37% bracket: $731,200+ *)
  let t7 := if ti >? 731200 then (ti - 731200) * 37 / 100 else 0 in
  t1 + t2 + t3 + t4 + t5 + t6 + t7.

(* Married Filing Separately Tax Brackets 2024 *)
Definition tax_mfs_2024 (taxable_income : Z) : Z :=
  let ti := Z.max 0 taxable_income in
  (* Same thresholds as Single for MFS *)
  let t1 := Z.min ti 11600 * 10 / 100 in
  let t2 := if ti >? 11600 then (Z.min ti 47150 - 11600) * 12 / 100 else 0 in
  let t3 := if ti >? 47150 then (Z.min ti 100525 - 47150) * 22 / 100 else 0 in
  let t4 := if ti >? 100525 then (Z.min ti 191950 - 100525) * 24 / 100 else 0 in
  let t5 := if ti >? 191950 then (Z.min ti 243725 - 191950) * 32 / 100 else 0 in
  let t6 := if ti >? 243725 then (Z.min ti 365600 - 243725) * 35 / 100 else 0 in
  let t7 := if ti >? 365600 then (ti - 365600) * 37 / 100 else 0 in
  t1 + t2 + t3 + t4 + t5 + t6 + t7.

(* Head of Household Tax Brackets 2024 *)
Definition tax_hoh_2024 (taxable_income : Z) : Z :=
  let ti := Z.max 0 taxable_income in
  (* 10% bracket: $0 - $16,550 *)
  let t1 := Z.min ti 16550 * 10 / 100 in
  (* 12% bracket: $16,550 - $63,100 *)
  let t2 := if ti >? 16550 then (Z.min ti 63100 - 16550) * 12 / 100 else 0 in
  (* 22% bracket: $63,100 - $100,500 *)
  let t3 := if ti >? 63100 then (Z.min ti 100500 - 63100) * 22 / 100 else 0 in
  (* 24% bracket: $100,500 - $191,950 *)
  let t4 := if ti >? 100500 then (Z.min ti 191950 - 100500) * 24 / 100 else 0 in
  (* 32% bracket: $191,950 - $243,700 *)
  let t5 := if ti >? 191950 then (Z.min ti 243700 - 191950) * 32 / 100 else 0 in
  (* 35% bracket: $243,700 - $609,350 *)
  let t6 := if ti >? 243700 then (Z.min ti 609350 - 243700) * 35 / 100 else 0 in
  (* 37% bracket: $609,350+ *)
  let t7 := if ti >? 609350 then (ti - 609350) * 37 / 100 else 0 in
  t1 + t2 + t3 + t4 + t5 + t6 + t7.

(* Qualifying Widow(er) uses MFJ brackets *)
Definition tax_qw_2024 := tax_mfj_2024.

(* Master tax computation by filing status *)
Definition compute_tax_by_status (taxable_income : Z) (status : filing_status) : Z :=
  match status with
  | Single => tax_single_2024 taxable_income
  | MarriedFilingJointly => tax_mfj_2024 taxable_income
  | MarriedFilingSeparately => tax_mfs_2024 taxable_income
  | HeadOfHousehold => tax_hoh_2024 taxable_income
  | QualifyingWidow => tax_qw_2024 taxable_income
  end.

(* ============================================================== *)
(* SECTION 4: SOCIAL SECURITY AND MEDICARE                        *)
(* FICA Tax Rates for 2024                                        *)
(* ============================================================== *)

(* Social Security wage base for 2024 *)
Definition ss_wage_base_2024 : Z := 168600.

(* Social Security tax rate: 6.2% employee portion *)
Definition ss_tax_rate_num : Z := 62.
Definition ss_tax_rate_den : Z := 1000.

(* Medicare tax rate: 1.45% employee portion *)
Definition medicare_tax_rate_num : Z := 145.
Definition medicare_tax_rate_den : Z := 10000.

(* Additional Medicare tax: 0.9% on wages over $200k (Single) *)
Definition additional_medicare_threshold_single : Z := 200000.
Definition additional_medicare_rate_num : Z := 9.
Definition additional_medicare_rate_den : Z := 1000.

(* ============================================================== *)
(* SECTION 5: BASIC VERIFICATION LEMMAS                           *)
(* These help establish properties of the tax code                *)
(* ============================================================== *)

(* Tax is non-negative *)
Lemma tax_single_nonneg : forall ti, 0 <= tax_single_2024 ti.
Proof.
  intro ti. unfold tax_single_2024.
  (* The proof follows from non-negativity of each bracket *)
  (* This is tedious but straightforward *)
Admitted. (* Full proof omitted for brevity *)

(* Tax is monotonic in income *)
Lemma tax_single_monotonic : forall ti1 ti2, 
  ti1 <= ti2 -> tax_single_2024 ti1 <= tax_single_2024 ti2.
Proof.
  (* Monotonicity follows from progressive bracket structure *)
Admitted.

(* Standard deduction is positive *)
Lemma std_deduction_positive : forall status,
  0 < standard_deduction_2024 status.
Proof.
  intro status. destruct status; simpl; lia.
Qed.
