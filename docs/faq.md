# Questions and answers

**Does my contract get sent anywhere?**
No. The checker sends passages only to a Jeff server on the same computer,
and it refuses any other address unless you deliberately change a setting.
It also ignores proxy settings and won't follow redirects. Those are the
defaults; using a Jeff server elsewhere takes a deliberate setting. Details:
[privacy.md](privacy.md).

**Do I need an expensive computer?**
It was tested on a laptop with an 8 GB NVIDIA graphics card: a normal
gaming-class machine, not a workstation. With Jeff loaded, the card showed
about 1.4 GB in use. A computer with no graphics card hasn't been tested.

**How accurate is it?**
On 102 public contracts that lawyers had labelled, it scored 94.7% of the
clause types that were present at 0.5 or above. That is the halfway mark;
the stricter "found" verdict needs 0.91. Each question asks whether a contract has
that kind of clause, so a contract with two liability caps counts once. On contracts held back to test the verdicts:
- "found" was right 92% of the time
- "not found" hid 1 real clause in 204
- about 1 in 5 "check" items was a real clause

Full figures: [RESULTS.md](../RESULTS.md).

**Can I trust "not found"?**
Not as proof. It means no passage looked like the clause. On the held-out
public test contracts, 190 answers came back "not found" and 1 of them was
wrong. Put the other way, 1 of the 204 real clauses there ended up marked
"not found". Your contracts may differ, and UK-drafted contracts haven't
been tested at all. Treat it
as "probably not there, worth a glance if it matters".

**What does "check" mean?**
Jeff isn't sure. The report gives the position of the passage Jeff scored
highest, and quotes one sentence from it, picked by the keyword search, so a
lawyer can go straight to it. It came up on about 5 of every 12 questions,
and about 1 in 5 of those was real.

**Which clauses does it look for?**
Twelve, taken from the CUAD dataset:
- governing law
- anti-assignment
- cap on liability
- uncapped liability
- termination for convenience
- renewal term
- change of control
- non-compete
- exclusivity
- audit rights
- insurance
- liquidated damages

A lawyer's own checklist is the obvious next step.

**Does it work on UK contracts?**
Unknown. All testing so far used US contracts filed with the SEC. UK
drafting differs, so that is one of the first things a pilot should test.

**Can it spot contradictions between clauses?**
Not yet. A first step is planned using ContractNLI, a public set of NDAs
labelled for whether statements are entailed by, contradicted by or not
mentioned in each contract. That tests a contract against a given
statement, which is close to, but not the same as, clauses contradicting
each other. That would need its own test set, for example the simulated
contracts in the plan.

**Is it AI writing legal opinions?**
No. Jeff doesn't write text; it answers fixed yes/no questions with a
confidence score. Apart from the clause names and verdict labels, the
report is quotations from the contract and numbers, with no commentary. It
is a screening aid, not advice.

**What is the "cloud step"?**
A planned option. For hard questions, the relevant passages would be
pseudonymised on your computer and shown to you, then sent to a powerful
cloud AI only when you click send. The answer would come back with real
names restored locally. It isn't built yet. It may not be needed where
the firm has approved sending those documents to a cloud service, but that
is the firm's and the client's call. See
[overview.md](overview.md#3-maybe-you-dont-need-the-clever-bit-at-all).

**What does it cost?**
The software is free: legal-screen is Apache 2.0, and Jeff is open source.
Checking contracts locally has no per-use fees. The planned cloud step
would carry the cloud provider's usual charges.

**Who made it?**
legal-screen is by [Jono Gitty](https://github.com/JonoGitty). Jeff is by
Mathias Strasser. The test contracts and labels are from The Atticus
Project's CUAD dataset.
