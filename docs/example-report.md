# Example report

This is real output from `python3 -m legal_screen contract.txt` on one
**public** contract: a 1999 website-hosting agreement from the CUAD test
set (The Atticus Project, CC BY 4.0). Jeff ran locally on a laptop GPU.
It took about 15 seconds with the GPU free.

| Clause | Verdict | P | Where (characters) | Passage |
|---|---|---|---|---|
| Governing Law | **found** | 0.99 | 13,693–15,176 | This Agreement was entered into in the State of Florida, and its validity, construction, interpretation, and legal effect shall be governed by the laws and judicial decisions of the State of Florida applicable to contracts entered into and performed entirely within the State of Florida. |
| Anti-Assignment | not found in any of 5 passages | 0.05 (highest) | – | – |
| Cap On Liability | **found** | 0.99 | 10,349–14,093 | LIMITATION OF LIABILITY — i-on will not be liable under any circumstances for any lost profits or other consequential damages, even if i-on has been advised as to the possibility of such damages |
| Uncapped Liability | **check** | 0.40 | 6,870–10,749 | The Customer is solely responsible for the security of its administrator account(s) and respective password(s) for the Hosted Site, and is solely responsible for any loss of data or damage to the Hosted Site that arises out of any breach of such security. |
| Termination For Convenience | **check** | 0.82 | 10,349–14,093 | Either party may terminate this Agreement without cause at any time effective upon thirty (30) days' written notice. |
| Renewal Term | **found** | 0.97 | 10,349–14,093 | This Agreement shall automatically be renewed for one (1) or more one (1) month periods unless either the Customer or i-on gives notice to the other party of its intention not to renew the… |
| Change Of Control | not found in any of 5 passages | 0.05 (highest) | – | – |
| Non-Compete | not found in any of 5 passages | 0.04 (highest) | – | – |
| Exclusivity | **check** | 0.18 | 3,526–7,270 | 13. up to 1 hour per month of Web site administration services at no additional charge, limited to: |
| Audit Rights | **check** | 0.23 | 6,870–10,749 | Any such programs, scripts, or components that might affect the stability of the Hosting Computer … must be approved by i-on before being installed on the Hosted Site… |
| Insurance | not found in any of 5 passages | 0.09 (highest) | – | – |
| Liquidated Damages | **check** | 0.33 | 10,349–14,093 | This Agreement shall automatically be renewed for one (1) or more one (1) month periods… |

## Against the lawyers' labels for this contract

CUAD's lawyers marked **4** of these 12 clause types as present: governing
law, cap on liability, termination for convenience and renewal term.

- **All 4 were caught.**
  - Governing law, the cap and renewal came back **found**, with the right
    wording quoted.
  - Termination for convenience came back **check** at 0.82. That is just
    under the 0.91 bar for "found", but it quoted exactly the right
    sentence.
- **Of the 8 types that aren't in the contract:**
  - 4 came back **not found**, which is correct.
  - 4 came back **check**: uncapped liability, exclusivity, audit rights
    and liquidated damages. These are false alarms, which a lawyer can rule
    out by reading the quoted sentence and its passage.

That is the trade the tool is tuned for: **it doesn't miss real clauses,
and it asks a person about the borderline ones**.

## How to read the columns

- **P** is Jeff's confidence, from 0 to 1, that the passage contains the
  clause. The verdict comes from P:
  - **found** at 0.91 or more
  - **check** from 0.15 to 0.91
  - **not found** below 0.15 in every passage
  - These cut-offs were set on half of the public test contracts and
    checked on the other half; see [RESULTS.md](../RESULTS.md).
- **Where** is the passage's position in the document, in characters.
- **Passage** is the sentence in that passage most likely to be the
  clause, picked by the keyword search. Check it against the contract
  itself.
- **"Not found"** reports the highest P seen anywhere, so you can see how
  close it came.
