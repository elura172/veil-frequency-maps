from __future__ import annotations


ONES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen")
TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")


def number_words(value: int) -> str:
    value = max(0, min(99, int(value)))
    if value < 20:
        return ONES[value]
    tens, ones = divmod(value, 10)
    return TENS[tens] if not ones else TENS[tens] + "-" + ONES[ones]


def poetic_descriptor(value: int, qualities: dict[str, float]) -> str:
    words = number_words(value)
    light = max((("bright", qualities["brightness"]), ("warm", qualities["warmth"]),
                 ("silver", qualities["shimmer"]), ("dark", 1.0 - qualities["brightness"])), key=lambda item: item[1])[0]
    image = max((("embers", qualities["energy"] + qualities["warmth"]),
                 ("veils", qualities["spaciousness"] + qualities["shimmer"]),
                 ("stones", qualities["weight"] + qualities["coherence"]),
                 ("signals", qualities["pulse"] + qualities["novelty"])), key=lambda item: item[1])[0]
    direction = max((("rise", qualities["brightness"] + qualities["motion"]),
                     ("gather", qualities["density"] + qualities["weight"]),
                     ("drift", qualities["spaciousness"] + qualities["shimmer"]),
                     ("hold", qualities["coherence"] + (1.0 - qualities["motion"]))), key=lambda item: item[1])[0]
    return f"{words} {light} {image} {direction}"
