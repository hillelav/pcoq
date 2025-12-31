(* ============================================================== *)
(* TaxProof_Example.v - Example LLM-Generated Tax Return Proof    *)
(*                                                                *)
(* This file demonstrates what an LLM would produce given:        *)
(* - Certified tax documents (W-2s, 1099s)                        *)
(* - Filing status                                                *)
(* - The IRS specification files                                  *)
(*                                                                *)
(* The LLM outputs BOTH the tax return values AND this proof      *)
(* that the values are correct per the IRS specification.         *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Require Import String.
Require Import TaxCode.
Require Import DocumentSpec.
Require Import ComputeSpec.
Open Scope Z_scope.

(* ============================================================== *)
(* TAXPAYER SCENARIO                                              *)
(*                                                                *)
(* Jane Doe (SSN: ***-**-1234) for Tax Year 2024                 *)
(* - One W-2 from Acme Corp: $75,000 wages, $12,000 withheld      *)
(* - One 1099-INT from First Bank: $500 interest                  *)
(* - Filing Status: Single                                        *)
(* ============================================================== *)

(* ============================================================== *)
(* SECTION 1: CERTIFIED DOCUMENTS (from user input)               *)
(* ============================================================== *)

(* W-2 from Acme Corporation *)
Definition jane_w2 : W2 := mkW2
  "12-3456789"           (* Employer EIN *)
  "Acme Corporation"     (* Employer name *)
  "123 Main St, NYC"     (* Employer address *)
  "***-**-1234"          (* Employee SSN - redacted for display *)
  "Jane Doe"             (* Employee name *)
  "456 Oak Ave, NYC"     (* Employee address *)
  75000                  (* Box 1: Wages *)
  12000                  (* Box 2: Federal withheld *)
  75000                  (* Box 3: SS wages *)
  4650                   (* Box 4: SS withheld (6.2%) *)
  75000                  (* Box 5: Medicare wages *)
  1088                   (* Box 6: Medicare withheld (1.45%) *)
  "NY"                   (* State *)
  75000                  (* State wages *)
  4500                   (* State withheld *)
  example_valid_sig      (* Employer's digital signature *)
  2024.                  (* Tax year *)

(* 1099-INT from First National Bank *)
Definition jane_1099int : Form1099_INT := mk1099INT
  "98-7654321"           (* Payer TIN *)
  "First National Bank"  (* Payer name *)
  "***-**-1234"          (* Recipient SSN *)
  "Jane Doe"             (* Recipient name *)
  500                    (* Box 1: Interest income *)
  0                      (* Box 2: Early withdrawal penalty *)
  0                      (* Box 3: US Savings Bond interest *)
  0                      (* Box 4: Federal withheld *)
  0                      (* Box 8: Tax-exempt interest *)
  example_valid_sig      (* Payer's digital signature *)
  2024.                  (* Tax year *)

(* Complete document collection *)
Definition jane_docs : TaxDocuments := mkTaxDocs
  "***-**-1234"          (* Taxpayer SSN *)
  2024                   (* Tax year *)
  (jane_w2 :: nil)       (* W-2s *)
  (jane_1099int :: nil)  (* 1099-INTs *)
  nil                    (* 1099-DIVs - none *)
  nil                    (* 1099-MISCs - none *)
  nil.                   (* 1099-NECs - none *)

Definition jane_status : filing_status := Single.

(* ============================================================== *)
(* SECTION 2: COMPUTED VALUES (the tax return)                    *)
(* ============================================================== *)

(*
   CALCULATION WALKTHROUGH:
   
   Gross Income:
     Wages (W-2):        $75,000
     Interest (1099):       $500
     ─────────────────────────────
     Total:              $75,500
   
   AGI = Gross Income = $75,500 (no above-line deductions)
   
   Standard Deduction (Single, 2024): $14,600
   
   Taxable Income = $75,500 - $14,600 = $60,900
   
   Tax Calculation (Single 2024 brackets):
     10% on first $11,600:           $1,160
     12% on $11,600 to $47,150:      $4,266  [(47150-11600)*0.12]
     22% on $47,150 to $60,900:      $3,025  [(60900-47150)*0.22]
     ─────────────────────────────────────────
     Total Tax:                      $8,451
   
   Withholding:                     $12,000
   
   Refund = $12,000 - $8,451 =       $3,549
*)

(* The claim the LLM is making *)
Definition jane_claim : TaxReturnClaim := mkClaim
  8451                   (* Tax liability *)
  12000                  (* Total withheld *)
  3549                   (* Refund *)
  75500                  (* AGI *)
  60900.                 (* Taxable income *)

(* ============================================================== *)
(* SECTION 3: THE PROOF                                           *)
(* ============================================================== *)

(* First, prove some computational lemmas *)

Lemma jane_wages_correct :
  sum_w2_wages (docs_w2s jane_docs) = 75000.
Proof.
  unfold jane_docs, docs_w2s, jane_w2.
  unfold sum_w2_wages. simpl.
  reflexivity.
Qed.

Lemma jane_interest_correct :
  sum_1099int_interest (docs_1099_int jane_docs) = 500.
Proof.
  unfold jane_docs, docs_1099_int, jane_1099int.
  unfold sum_1099int_interest. simpl.
  reflexivity.
Qed.

Lemma jane_agi_correct :
  compute_agi_simple jane_docs = 75500.
Proof.
  unfold compute_agi_simple, compute_gross_income.
  unfold compute_wage_income, compute_interest_income, compute_dividend_income.
  rewrite jane_wages_correct.
  rewrite jane_interest_correct.
  unfold jane_docs, docs_1099_div, sum_1099div_ordinary. simpl.
  reflexivity.
Qed.

Lemma jane_std_deduction_correct :
  standard_deduction_2024 Single = 14600.
Proof.
  reflexivity.
Qed.

Lemma jane_taxable_correct :
  compute_taxable_income_std 75500 Single = 60900.
Proof.
  unfold compute_taxable_income_std.
  rewrite jane_std_deduction_correct.
  (* 75500 - 14600 = 60900, and 60900 > 0 so Z.max returns it *)
  reflexivity.
Qed.

Lemma jane_tax_correct :
  compute_tax_by_status 60900 Single = 8451.
Proof.
  unfold compute_tax_by_status, tax_single_2024.
  (* 
     Let's trace the computation:
     ti = Z.max 0 60900 = 60900
     
     t1 = Z.min 60900 11600 * 10 / 100 = 11600 * 10 / 100 = 1160
     
     60900 >? 11600 = true, so:
     t2 = (Z.min 60900 47150 - 11600) * 12 / 100
        = (47150 - 11600) * 12 / 100 = 35550 * 12 / 100 = 4266
     
     60900 >? 47150 = true, so:
     t3 = (Z.min 60900 100525 - 47150) * 22 / 100
        = (60900 - 47150) * 22 / 100 = 13750 * 22 / 100 = 3025
     
     60900 >? 100525 = false, so t4 = 0
     t5, t6, t7 = 0
     
     Total = 1160 + 4266 + 3025 + 0 + 0 + 0 + 0 = 8451
  *)
  reflexivity.
Qed.

Lemma jane_withheld_correct :
  compute_total_withheld jane_docs = 12000.
Proof.
  unfold compute_total_withheld.
  unfold jane_docs, docs_w2s, docs_1099_int.
  unfold sum_w2_federal_withheld, sum_1099int_withheld.
  unfold jane_w2, jane_1099int. simpl.
  reflexivity.
Qed.

(* ============================================================== *)
(* MAIN THEOREM: Jane's tax return is correct                     *)
(* ============================================================== *)

Theorem jane_return_correct :
  claim_is_correct jane_docs jane_status jane_claim.
Proof.
  unfold claim_is_correct, jane_claim, jane_status.
  unfold compute_agi_simple, compute_gross_income.
  unfold compute_wage_income, compute_interest_income, compute_dividend_income.
  unfold jane_docs, docs_w2s, docs_1099_int, docs_1099_div.
  unfold sum_w2_wages, sum_1099int_interest, sum_1099div_ordinary.
  unfold jane_w2, jane_1099int.
  unfold compute_taxable_income_std, standard_deduction_2024.
  unfold compute_tax_by_status, tax_single_2024.
  unfold compute_total_withheld.
  unfold sum_w2_federal_withheld, sum_1099int_withheld.
  simpl.
  repeat split; reflexivity.
Qed.

(* ============================================================== *)
(* COROLLARY: The refund amount is verified                       *)
(* ============================================================== *)

Corollary jane_refund_verified :
  claim_refund jane_claim = compute_refund_or_due jane_docs jane_status.
Proof.
  apply tax_return_correct.
  exact jane_return_correct.
Qed.

(* ============================================================== *)
(* HUMAN-READABLE SUMMARY                                         *)
(* This is what gets shown to the user                            *)
(* ============================================================== *)

(*
   ╔══════════════════════════════════════════════════════════════╗
   ║           VERIFIED TAX RETURN - TAX YEAR 2024                ║
   ╠══════════════════════════════════════════════════════════════╣
   ║  Taxpayer: Jane Doe                                          ║
   ║  Filing Status: Single                                       ║
   ╠══════════════════════════════════════════════════════════════╣
   ║  INCOME                                                      ║
   ║    Wages (W-2):                           $75,000            ║
   ║    Interest (1099-INT):                      $500            ║
   ║    ────────────────────────────────────────────────          ║
   ║    Adjusted Gross Income:                 $75,500            ║
   ╠══════════════════════════════════════════════════════════════╣
   ║  DEDUCTIONS                                                  ║
   ║    Standard Deduction:                    $14,600            ║
   ║    ────────────────────────────────────────────────          ║
   ║    Taxable Income:                        $60,900            ║
   ╠══════════════════════════════════════════════════════════════╣
   ║  TAX COMPUTATION                                             ║
   ║    Tax Liability:                          $8,451            ║
   ║    Federal Withheld:                      $12,000            ║
   ║    ────────────────────────────────────────────────          ║
   ║    REFUND DUE:                             $3,549            ║
   ╠══════════════════════════════════════════════════════════════╣
   ║  VERIFICATION STATUS: ✓ PROVEN CORRECT                       ║
   ║  Proof: jane_return_correct                                  ║
   ║  Verified against: IRS TaxCode.v v2024.1                     ║
   ╚══════════════════════════════════════════════════════════════╝
*)

Print Assumptions jane_return_correct.
(* Should show only the signature axiom, which is verified separately *)
