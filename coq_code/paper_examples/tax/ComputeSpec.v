(* ============================================================== *)
(* ComputeSpec.v - Tax Computation Specification                  *)
(* Published by: IRS (hypothetically)                             *)
(* Version: 2024.1                                                *)
(*                                                                *)
(* This file defines THE CORRECT WAY to compute tax liability.    *)
(* Any LLM output must produce a proof that its result equals     *)
(* the value computed by these functions.                         *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Require Import String.
Require Import Lia.
Require Import TaxCode.
Require Import DocumentSpec.
Open Scope Z_scope.

(* ============================================================== *)
(* SECTION 1: GROSS INCOME COMPUTATION                            *)
(* IRC Section 61 - Gross Income Defined                          *)
(* ============================================================== *)

(* Wages from employment (W-2 income) *)
Definition compute_wage_income (docs : TaxDocuments) : Z :=
  sum_w2_wages (docs_w2s docs).

(* Interest income (1099-INT) *)
Definition compute_interest_income (docs : TaxDocuments) : Z :=
  sum_1099int_interest (docs_1099_int docs).

(* Dividend income (1099-DIV) - ordinary dividends *)
Definition compute_dividend_income (docs : TaxDocuments) : Z :=
  sum_1099div_ordinary (docs_1099_div docs).

(* Total gross income (simplified - real tax code has many more categories) *)
Definition compute_gross_income (docs : TaxDocuments) : Z :=
  compute_wage_income docs +
  compute_interest_income docs +
  compute_dividend_income docs.

(* ============================================================== *)
(* SECTION 2: ADJUSTED GROSS INCOME (AGI)                         *)
(* IRC Section 62                                                  *)
(* ============================================================== *)

(* Above-the-line deductions (simplified) *)
Record AboveLineDeductions := mkAboveLine {
  ald_educator_expenses : Z;        (* Up to $300 *)
  ald_student_loan_interest : Z;    (* Up to $2,500 *)
  ald_ira_contribution : Z;         (* Traditional IRA *)
  ald_hsa_contribution : Z;         (* Health Savings Account *)
  ald_self_employment_tax : Z       (* Deductible portion *)
}.

Definition zero_above_line : AboveLineDeductions := mkAboveLine 0 0 0 0 0.

Definition total_above_line (ald : AboveLineDeductions) : Z :=
  ald_educator_expenses ald +
  ald_student_loan_interest ald +
  ald_ira_contribution ald +
  ald_hsa_contribution ald +
  ald_self_employment_tax ald.

(* Compute AGI *)
Definition compute_agi (docs : TaxDocuments) (ald : AboveLineDeductions) : Z :=
  compute_gross_income docs - total_above_line ald.

(* Simple version without above-line deductions *)
Definition compute_agi_simple (docs : TaxDocuments) : Z :=
  compute_gross_income docs.

(* ============================================================== *)
(* SECTION 3: TAXABLE INCOME                                      *)
(* IRC Section 63                                                 *)
(* ============================================================== *)

(* Compute taxable income using standard deduction *)
Definition compute_taxable_income_std 
    (agi : Z) (status : filing_status) : Z :=
  Z.max 0 (agi - standard_deduction_2024 status).

(* Compute taxable income given itemized deductions *)
Definition compute_taxable_income_itemized 
    (agi : Z) (itemized : Z) : Z :=
  Z.max 0 (agi - itemized).

(* Choose better of standard or itemized *)
Definition compute_taxable_income 
    (agi : Z) (status : filing_status) (itemized : Z) : Z :=
  let std := standard_deduction_2024 status in
  if itemized >? std then
    compute_taxable_income_itemized agi itemized
  else
    compute_taxable_income_std agi status.

(* ============================================================== *)
(* SECTION 4: TAX LIABILITY COMPUTATION                           *)
(* The main specification                                          *)
(* ============================================================== *)

(* Full tax liability computation (standard deduction) *)
Definition compute_tax_liability_std
    (docs : TaxDocuments)
    (status : filing_status) : Z :=
  let agi := compute_agi_simple docs in
  let taxable := compute_taxable_income_std agi status in
  compute_tax_by_status taxable status.

(* Full tax liability computation (with above-line deductions) *)
Definition compute_tax_liability
    (docs : TaxDocuments)
    (ald : AboveLineDeductions)
    (status : filing_status)
    (itemized_deductions : Z) : Z :=
  let agi := compute_agi docs ald in
  let taxable := compute_taxable_income agi status itemized_deductions in
  compute_tax_by_status taxable status.

(* ============================================================== *)
(* SECTION 5: WITHHOLDING AND REFUND/AMOUNT DUE                   *)
(* ============================================================== *)

(* Total federal tax withheld from all sources *)
Definition compute_total_withheld (docs : TaxDocuments) : Z :=
  sum_w2_federal_withheld (docs_w2s docs) +
  sum_1099int_withheld (docs_1099_int docs).

(* Refund (positive) or amount due (negative) *)
Definition compute_refund_or_due
    (docs : TaxDocuments)
    (status : filing_status) : Z :=
  let withheld := compute_total_withheld docs in
  let liability := compute_tax_liability_std docs status in
  withheld - liability.

(* ============================================================== *)
(* SECTION 6: THE CORRECTNESS SPECIFICATION                       *)
(* This is what LLM proofs must establish                         *)
(* ============================================================== *)

(* A tax return claim *)
Record TaxReturnClaim := mkClaim {
  claim_tax_liability : Z;
  claim_total_withheld : Z;
  claim_refund : Z;           (* Positive = refund, negative = due *)
  claim_agi : Z;
  claim_taxable_income : Z
}.

(* THE MAIN CORRECTNESS THEOREM *)
(* An LLM must prove this for any claim it makes *)
Definition claim_is_correct 
    (docs : TaxDocuments)
    (status : filing_status)
    (claim : TaxReturnClaim) : Prop :=
  (* AGI is computed correctly *)
  claim_agi claim = compute_agi_simple docs /\
  (* Taxable income is computed correctly *)
  claim_taxable_income claim = 
    compute_taxable_income_std (claim_agi claim) status /\
  (* Tax liability is computed correctly *)
  claim_tax_liability claim = 
    compute_tax_by_status (claim_taxable_income claim) status /\
  (* Withholding is summed correctly *)
  claim_total_withheld claim = compute_total_withheld docs /\
  (* Refund/due is computed correctly *)
  claim_refund claim = claim_total_withheld claim - claim_tax_liability claim.

(* Alternative: single theorem combining everything *)
Theorem tax_return_correct : 
  forall (docs : TaxDocuments) (status : filing_status) (claim : TaxReturnClaim),
  claim_is_correct docs status claim ->
  claim_refund claim = compute_refund_or_due docs status.
Proof.
  intros docs status claim H.
  destruct H as [Hagi [Htaxable [Hliab [Hwith Href]]]].
  unfold compute_refund_or_due, compute_tax_liability_std.
  rewrite <- Hwith.
  rewrite <- Hagi.
  rewrite <- Htaxable.
  rewrite <- Hliab.
  exact Href.
Qed.

(* ============================================================== *)
(* SECTION 7: VERIFICATION HELPERS                                *)
(* Tactics and lemmas to help prove correctness                   *)
(* ============================================================== *)

(* Compute AGI step by step *)
Lemma agi_step : forall docs,
  compute_agi_simple docs = 
    sum_w2_wages (docs_w2s docs) +
    sum_1099int_interest (docs_1099_int docs) +
    sum_1099div_ordinary (docs_1099_div docs).
Proof.
  intro docs.
  unfold compute_agi_simple, compute_gross_income.
  unfold compute_wage_income, compute_interest_income, compute_dividend_income.
  reflexivity.
Qed.

(* For documents with only W-2s and 1099-INTs *)
Lemma agi_simple_no_div : forall docs,
  docs_1099_div docs = nil ->
  compute_agi_simple docs = 
    sum_w2_wages (docs_w2s docs) + sum_1099int_interest (docs_1099_int docs).
Proof.
  intros docs Hnil.
  rewrite agi_step.
  rewrite Hnil.
  unfold sum_1099div_ordinary. simpl.
  lia.
Qed.

(* Tax liability is non-negative *)
Lemma tax_liability_nonneg : forall docs status,
  0 <= compute_tax_liability_std docs status.
Proof.
  intros docs status.
  unfold compute_tax_liability_std.
  (* Would need to prove tax_by_status is non-negative *)
Admitted.

(* ============================================================== *)
(* SECTION 8: EXAMPLE - TEMPLATE FOR LLM PROOFS                   *)
(* ============================================================== *)

(* 
   An LLM should produce proofs following this template:
   
   1. Define the specific documents (from user input)
   2. Define the TaxReturnClaim with computed values
   3. Prove claim_is_correct by unfolding and computing
   
   Example structure:
   
   Definition user_w2 := mkW2 ... (specific values).
   Definition user_docs := mkTaxDocs ... [user_w2] ... .
   Definition user_claim := mkClaim 
     (computed_liability)
     (computed_withheld)
     (computed_refund)
     (computed_agi)
     (computed_taxable).
   
   Theorem user_return_correct :
     claim_is_correct user_docs Single user_claim.
   Proof.
     unfold claim_is_correct.
     repeat split; reflexivity.
   Qed.
*)
