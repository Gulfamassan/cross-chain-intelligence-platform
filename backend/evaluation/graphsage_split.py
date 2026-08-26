"""
GraphSAGE Dev / Held-out Split (Sprint 17, Day 4)

Ye module `evaluation/ground_truth.py` ke 7 verified wallet-pair cases
ko do groups mein banta hai:

    Development set   -> model develop/tune karte waqt use hota hai
    Held-out set       -> SIRF final evaluation ke liye, ek hi baar dekha jaye

Important: n=7 itna chhota hai ke ek RANDOM split khatarnak hoga —
chance se ek group mein sirf ek hi class ("Related" ya "Unrelated")
aa sakti hai, jo evaluation ko meaningless bana degi. Isliye ye split
haath se (manually) banaya gaya hai, taake dono groups mein dono classes
maujood rahein (stratified):

    Development (4 cases): 1, 3, 4, 6  -> 2 Related, 2 Unrelated
    Held-out    (3 cases): 2, 5, 7     -> 1 Related, 2 Unrelated

CRITICAL DISCLAIMER: Ye n=7 dataset ek chhota case-study/benchmark hai,
statistically reliable ML benchmark NAHI hai. Kisi bhi single number
(jaise "accuracy") ko is dataset se nikaal kar general claim ("GraphSAGE
X% accurate hai") ke taur par report NAHI karna chahiye. Held-out set
ka result sirf ek qualitative signal hai — "in in specific verified
cases model ne kya kaha" — na ke ek statistically valid metric.
Zyada reliable evaluation ke liye zyada labelled wallet-pairs chahiye
honge (future sprint).
"""

from evaluation.ground_truth import get_dataset


DEV_CASE_IDS = [1, 3, 4, 6]
HELD_OUT_CASE_IDS = [2, 5, 7]


def get_dev_cases() -> list:
    """
    Development set return karta hai — model develop/tune karte waqt
    (jaise similarity threshold adjust karna) inhi cases ko dekhein.

    Returns:
        list: 4 cases (2 Related, 2 Unrelated)
    """
    dataset = get_dataset()
    return [case for case in dataset if case["case_id"] in DEV_CASE_IDS]


def get_held_out_cases() -> list:
    """
    Held-out set return karta hai — SIRF final evaluation ke liye.
    Development/tuning ke dauran ye cases repeatedly nahi dekhne chahiye,
    warna ye bhi "development data" ban jayega aur evaluation biased
    ho jayegi.

    Returns:
        list: 3 cases (1 Related, 2 Unrelated)
    """
    dataset = get_dataset()
    return [case for case in dataset if case["case_id"] in HELD_OUT_CASE_IDS]