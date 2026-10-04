"""The default checklist: twelve clause types a contract reviewer looks for.

Names and descriptions follow CUAD's categories (The Atticus Project,
CC BY 4.0), so results can be scored against CUAD's lawyer labels. The
keyword patterns were written before any results were seen, and must not be
tuned on the test contracts.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    key: str
    name: str  # CUAD category name
    description: str  # CUAD's description of what counts
    patterns: tuple[str, ...]  # regexes (case-insensitive)

    def question(self, wording: str = "short") -> str:
        if wording == "short":
            return f"Does this passage of a contract contain a {self.name.lower()} clause?"
        if wording == "described":
            return (
                f"Does this passage of a contract contain a {self.name.lower()} clause? "
                f"That is: {self.description}"
            )
        raise ValueError(f"unknown wording {wording!r}")


CHECKLIST: tuple[Item, ...] = (
    Item(
        "governing_law",
        "Governing Law",
        "Which state/country's law governs the interpretation of the contract?",
        (r"govern(ed|ing)\s+by", r"governing\s+law", r"construed\s+(in\s+accordance\s+with|under)", r"laws?\s+of\s+the\s+state\s+of"),
    ),
    Item(
        "anti_assignment",
        "Anti-Assignment",
        "Is consent or notice required of a party if the contract is assigned to a third party?",
        (r"(may|shall|will)\s+not\s+(be\s+)?assign", r"assign\w*.{0,100}(prior\s+written\s+consent|without\s+(the\s+)?(prior\s+)?(written\s+)?consent)", r"non-?assignab"),
    ),
    Item(
        "cap_on_liability",
        "Cap On Liability",
        "Does the contract include a cap on liability upon the breach of a party's obligation? This includes time limitation for the counterparty to bring claims or maximum amount for recovery.",
        (r"(aggregate|total|maximum|cumulative)\s+liability", r"liab\w*.{0,80}(shall\s+not\s+exceed|limited\s+to|in\s+excess\s+of)", r"in\s+no\s+event\s+shall.{0,100}liab", r"limitation\s+of\s+liability"),
    ),
    Item(
        "uncapped_liability",
        "Uncapped Liability",
        "Is a party's liability uncapped upon the breach of its obligation in the contract? This also includes uncapped liability for a particular type of breach such as IP infringement or breach of confidentiality obligation.",
        (r"unlimited\s+liability", r"(shall\s+not|will\s+not|does\s+not)\s+(apply|limit).{0,120}(gross\s+negligence|wil+ful\s+misconduct|indemnif|confidential|infring)", r"(foregoing|above)\s+limitations?.{0,60}(shall|will)\s+not\s+apply"),
    ),
    Item(
        "termination_for_convenience",
        "Termination For Convenience",
        "Can a party terminate this contract without cause (solely by giving a notice and allowing a waiting period to expire)?",
        (r"terminat\w*.{0,80}(for\s+(any|no)\s+reason|for\s+convenience|without\s+cause|at\s+any\s+time)", r"(upon|with|by\s+giving).{0,40}(days|months).{0,40}notice.{0,80}terminat", r"terminat\w*.{0,80}(upon|with|by\s+giving).{0,40}(days|months).{0,30}notice"),
    ),
    Item(
        "renewal_term",
        "Renewal Term",
        "What is the renewal term after the initial term expires? This includes automatic extensions and unilateral extensions with prior notice.",
        (r"automatic\w*\s+(be\s+)?(renew|extend)", r"renew(al|ed)?\s+(term|period)", r"successive.{0,40}(year|term|period)", r"auto-?renew"),
    ),
    Item(
        "change_of_control",
        "Change Of Control",
        "Does one party have the right to terminate or is consent or notice required of the counterparty if such party undergoes a change of control, such as a merger, stock sale, transfer of all or substantially all of its assets or business, or assignment by operation of law?",
        (r"change\s+(of|in)\s+control", r"(merger|consolidation|reorgani[sz]ation)", r"(sale|transfer)\s+of\s+(all\s+or\s+)?substantially\s+all", r"operation\s+of\s+law"),
    ),
    Item(
        "non_compete",
        "Non-Compete",
        "Is there a restriction on the ability of a party to compete with the counterparty or operate in a certain geography or business or technology sector?",
        (r"non-?compet", r"(shall|will)\s+not.{0,100}compet", r"competing\s+(product|business|service)", r"compete\s+with"),
    ),
    Item(
        "exclusivity",
        "Exclusivity",
        "Is there an exclusive dealing commitment with the counterparty? This includes a commitment to procure all requirements from one party of certain technology, goods, or services or a prohibition on licensing or selling technology, goods or services to third parties, or a prohibition on collaborating or working with other parties.",
        (r"\bexclusiv", r"sole\s+(and\s+exclusive\s+)?(supplier|distributor|provider|source|reseller)", r"all\s+of\s+its\s+requirements"),
    ),
    Item(
        "audit_rights",
        "Audit Rights",
        "Does a party have the right to audit the books, records, or physical locations of the counterparty to ensure compliance with the contract?",
        (r"\baudit", r"inspect\w*.{0,60}(books|records|premises|facilit)", r"(books|records).{0,80}(examin|inspect)"),
    ),
    Item(
        "insurance",
        "Insurance",
        "Is there a requirement for insurance that must be maintained by one party for the benefit of the counterparty?",
        (r"\binsurance\b", r"\binsured\b", r"\binsurer"),
    ),
    Item(
        "liquidated_damages",
        "Liquidated Damages",
        "Does the contract contain a clause that would award either party liquidated damages for breach or a fee upon the termination of a contract (termination fee)?",
        (r"liquidated\s+damages", r"termination\s+fee", r"(break|break-up|penalty)\s+fee"),
    ),
)
