(* ============================================================== *)
(* DocumentSpec.v - Certified Tax Document Schemas                *)
(* Published by: IRS (hypothetically)                             *)
(* Version: 2024.1                                                *)
(* ============================================================== *)

Require Import ZArith.
Require Import List.
Require Import String.
Open Scope Z_scope.

(* ============================================================== *)
(* SECTION 1: CRYPTOGRAPHIC PRIMITIVES (Abstract)                 *)
(* In practice, these would interface with actual crypto libs     *)
(* ============================================================== *)

(* Abstract type for digital signatures *)
Parameter signature : Type.

(* Signature verification predicate *)
(* In practice: verify against PKI / certificate authority *)
Parameter signature_valid : signature -> string -> bool.

(* Placeholder for a valid signature in examples *)
Parameter example_valid_sig : signature.
Axiom example_sig_valid : forall data, signature_valid example_valid_sig data = true.

(* ============================================================== *)
(* SECTION 2: FORM W-2 - Wage and Tax Statement                   *)
(* IRS Form W-2 Fields                                            *)
(* ============================================================== *)

Record W2 := mkW2 {
  (* Employer identification *)
  w2_employer_ein : string;        (* Box b: Employer EIN *)
  w2_employer_name : string;       (* Box c: Employer name *)
  w2_employer_address : string;    (* Box c: Employer address *)
  
  (* Employee identification *)
  w2_employee_ssn : string;        (* Box a: Employee SSN *)
  w2_employee_name : string;       (* Box e: Employee name *)
  w2_employee_address : string;    (* Box f: Employee address *)
  
  (* Compensation and withholding *)
  w2_wages : Z;                    (* Box 1: Wages, tips, other compensation *)
  w2_federal_withheld : Z;         (* Box 2: Federal income tax withheld *)
  w2_ss_wages : Z;                 (* Box 3: Social security wages *)
  w2_ss_withheld : Z;              (* Box 4: Social security tax withheld *)
  w2_medicare_wages : Z;           (* Box 5: Medicare wages and tips *)
  w2_medicare_withheld : Z;        (* Box 6: Medicare tax withheld *)
  
  (* Additional fields (simplified) *)
  w2_state : string;               (* Box 15: State *)
  w2_state_wages : Z;              (* Box 16: State wages *)
  w2_state_withheld : Z;           (* Box 17: State income tax *)
  
  (* Digital signature from employer *)
  w2_signature : signature;
  
  (* Tax year *)
  w2_tax_year : Z
}.

(* W-2 validity predicate *)
Definition w2_valid (w : W2) : Prop :=
  (* Wages must be non-negative *)
  0 <= w2_wages w /\
  (* Withholding must be non-negative *)
  0 <= w2_federal_withheld w /\
  (* SS wages cannot exceed total wages (simplified) *)
  w2_ss_wages w <= w2_wages w /\
  (* Tax year must be reasonable *)
  2000 <= w2_tax_year w <= 2100.

(* ============================================================== *)
(* SECTION 3: FORM 1099-INT - Interest Income                     *)
(* ============================================================== *)

Record Form1099_INT := mk1099INT {
  (* Payer identification *)
  f1099int_payer_tin : string;     (* Payer's TIN *)
  f1099int_payer_name : string;    (* Payer's name *)
  
  (* Recipient identification *)
  f1099int_recipient_ssn : string; (* Recipient's SSN *)
  f1099int_recipient_name : string;
  
  (* Income amounts *)
  f1099int_interest : Z;           (* Box 1: Interest income *)
  f1099int_early_withdrawal : Z;   (* Box 2: Early withdrawal penalty *)
  f1099int_us_savings_bonds : Z;   (* Box 3: Interest on U.S. Savings Bonds *)
  f1099int_federal_withheld : Z;   (* Box 4: Federal income tax withheld *)
  f1099int_tax_exempt : Z;         (* Box 8: Tax-exempt interest *)
  
  (* Signature and year *)
  f1099int_signature : signature;
  f1099int_tax_year : Z
}.

Definition f1099int_valid (f : Form1099_INT) : Prop :=
  0 <= f1099int_interest f /\
  0 <= f1099int_federal_withheld f /\
  2000 <= f1099int_tax_year f <= 2100.

(* ============================================================== *)
(* SECTION 4: FORM 1099-DIV - Dividends and Distributions         *)
(* ============================================================== *)

Record Form1099_DIV := mk1099DIV {
  f1099div_payer_tin : string;
  f1099div_payer_name : string;
  f1099div_recipient_ssn : string;
  f1099div_recipient_name : string;
  
  f1099div_ordinary_dividends : Z;      (* Box 1a *)
  f1099div_qualified_dividends : Z;     (* Box 1b *)
  f1099div_capital_gain_dist : Z;       (* Box 2a *)
  f1099div_federal_withheld : Z;        (* Box 4 *)
  
  f1099div_signature : signature;
  f1099div_tax_year : Z
}.

Definition f1099div_valid (f : Form1099_DIV) : Prop :=
  0 <= f1099div_ordinary_dividends f /\
  f1099div_qualified_dividends f <= f1099div_ordinary_dividends f /\
  0 <= f1099div_federal_withheld f.

(* ============================================================== *)
(* SECTION 5: FORM 1099-MISC - Miscellaneous Income               *)
(* ============================================================== *)

Record Form1099_MISC := mk1099MISC {
  f1099misc_payer_tin : string;
  f1099misc_payer_name : string;
  f1099misc_recipient_ssn : string;
  f1099misc_recipient_name : string;
  
  f1099misc_rents : Z;                  (* Box 1 *)
  f1099misc_royalties : Z;              (* Box 2 *)
  f1099misc_other_income : Z;           (* Box 3 *)
  f1099misc_federal_withheld : Z;       (* Box 4 *)
  
  f1099misc_signature : signature;
  f1099misc_tax_year : Z
}.

(* ============================================================== *)
(* SECTION 6: FORM 1099-NEC - Nonemployee Compensation            *)
(* ============================================================== *)

Record Form1099_NEC := mk1099NEC {
  f1099nec_payer_tin : string;
  f1099nec_payer_name : string;
  f1099nec_recipient_ssn : string;
  f1099nec_recipient_name : string;
  
  f1099nec_compensation : Z;            (* Box 1: Nonemployee compensation *)
  f1099nec_federal_withheld : Z;        (* Box 4 *)
  
  f1099nec_signature : signature;
  f1099nec_tax_year : Z
}.

(* ============================================================== *)
(* SECTION 7: AGGREGATION FUNCTIONS                               *)
(* Used by ComputeSpec.v                                          *)
(* ============================================================== *)

(* Sum wages from all W-2s *)
Definition sum_w2_wages (w2s : list W2) : Z :=
  fold_right (fun w acc => w2_wages w + acc) 0 w2s.

(* Sum federal withholding from all W-2s *)
Definition sum_w2_federal_withheld (w2s : list W2) : Z :=
  fold_right (fun w acc => w2_federal_withheld w + acc) 0 w2s.

(* Sum interest from all 1099-INTs *)
Definition sum_1099int_interest (forms : list Form1099_INT) : Z :=
  fold_right (fun f acc => f1099int_interest f + acc) 0 forms.

(* Sum federal withholding from 1099-INTs *)
Definition sum_1099int_withheld (forms : list Form1099_INT) : Z :=
  fold_right (fun f acc => f1099int_federal_withheld f + acc) 0 forms.

(* Sum ordinary dividends from all 1099-DIVs *)
Definition sum_1099div_ordinary (forms : list Form1099_DIV) : Z :=
  fold_right (fun f acc => f1099div_ordinary_dividends f + acc) 0 forms.

(* Sum qualified dividends from all 1099-DIVs *)
Definition sum_1099div_qualified (forms : list Form1099_DIV) : Z :=
  fold_right (fun f acc => f1099div_qualified_dividends f + acc) 0 forms.

(* ============================================================== *)
(* SECTION 8: DOCUMENT COLLECTION                                 *)
(* A taxpayer's complete set of documents for a tax year          *)
(* ============================================================== *)

Record TaxDocuments := mkTaxDocs {
  docs_ssn : string;                    (* Taxpayer's SSN *)
  docs_tax_year : Z;                    (* Tax year *)
  docs_w2s : list W2;                   (* All W-2s received *)
  docs_1099_int : list Form1099_INT;    (* All 1099-INTs *)
  docs_1099_div : list Form1099_DIV;    (* All 1099-DIVs *)
  docs_1099_misc : list Form1099_MISC;  (* All 1099-MISCs *)
  docs_1099_nec : list Form1099_NEC     (* All 1099-NECs *)
}.

(* Verify all documents belong to the same taxpayer and year *)
Definition docs_consistent (d : TaxDocuments) : Prop :=
  (* All W-2s have matching SSN and year *)
  (forall w, In w (docs_w2s d) -> 
    w2_employee_ssn w = docs_ssn d /\ w2_tax_year w = docs_tax_year d) /\
  (* All 1099-INTs have matching SSN and year *)
  (forall f, In f (docs_1099_int d) ->
    f1099int_recipient_ssn f = docs_ssn d /\ f1099int_tax_year f = docs_tax_year d) /\
  (* Similar for other forms... *)
  True.

(* ============================================================== *)
(* SECTION 9: CONVENIENCE LEMMAS                                  *)
(* ============================================================== *)

Lemma sum_w2_wages_nil : sum_w2_wages nil = 0.
Proof. reflexivity. Qed.

Lemma sum_w2_wages_cons : forall w ws,
  sum_w2_wages (w :: ws) = w2_wages w + sum_w2_wages ws.
Proof. reflexivity. Qed.

Lemma sum_1099int_nil : sum_1099int_interest nil = 0.
Proof. reflexivity. Qed.

Lemma sum_1099int_cons : forall f fs,
  sum_1099int_interest (f :: fs) = f1099int_interest f + sum_1099int_interest fs.
Proof. reflexivity. Qed.
