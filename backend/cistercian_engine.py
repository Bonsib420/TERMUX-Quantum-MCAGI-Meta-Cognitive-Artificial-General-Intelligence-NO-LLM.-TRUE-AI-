#!/usr/bin/env python3
"""
Cistercian Numeral Engine — Rosetta Code authoritative implementation.
Based on: https://rosettacode.org/wiki/Cistercian_numerals
Labeled points on the glyph:
a ■■■ b ■■■ c
top edge
|
d ■■■ e ■■■ f
upper-mid
|
g ■■■ h ■■■ i
lower-mid
|
j ■■■ k ■■■ l
bottom edge
Staff runs vertically: b → e → h → k
Quadrant layout:
Tens | Ones
------+-----1000s | 100s

(top half)
(bottom half)

SVG coordinate system: viewBox "-6 -6 12 12"
x = horizontal (negative=left, positive=right)
y = vertical (negative=up, positive=down)
Staff: (0,-5) to (0,5)
"""
POINTS = {
'a': (-2, -5), 'b': (0, -5), 'c': (2, -5),
'd': (-2, -3), 'e': (0, -3), 'f': (2, -3),
'g': (-2, 3), 'h': (0, 3), 'i': (2, 3),
'j': (-2, 5), 'k': (0, 5), 'l': (2, 5),
}
ONES_DRAWS = {
1: ['b', 'c'],
2: ['e', 'f'],
3: ['b', 'f'],
4: ['e', 'c'],
5: ['b', 'c', 'e'],
6: ['c', 'f'],
7: ['b', 'c', 'f'],
8: ['e', 'f', 'c'],
9: ['b', 'c', 'f', 'e'],
}
TENS_DRAWS = {
1: ['a', 'b'],
2: ['d', 'e'],
3: ['d', 'b'],
4: ['a', 'e'],
5: ['b', 'a', 'e'],
6: ['a', 'd'],
7: ['d', 'a', 'b'],
8: ['a', 'd', 'e'],
9: ['b', 'a', 'd', 'e'],
}
HUNDREDS_DRAWS = {
1: ['k', 'l'],
2: ['h', 'i'],
3: ['k', 'i'],
4: ['h', 'l'],
5: ['k', 'l', 'h'],
6: ['l', 'i'],
7: ['k', 'l', 'i'],
8: ['h', 'i', 'l'],
9: ['k', 'l', 'i', 'h'],
}
THOUSANDS_DRAWS = {
1: ['j', 'k'],
2: ['g', 'h'],
3: ['g', 'k'],
4: ['j', 'h'],
5: ['k', 'j', 'h'],
6: ['j', 'g'],
7: ['g', 'j', 'k'],
8: ['j', 'g', 'h'],
9: ['k', 'j', 'g', 'h'],
}

def _polyline_to_segments(point_labels):
segments = []
for i in range(len(point_labels) - 1):
p1 = POINTS[point_labels[i]]
p2 = POINTS[point_labels[i + 1]]
segments.append({
"x1": p1[0], "y1": p1[1],
"x2": p2[0], "y2": p2[1],
})
return segments
def generate_cistercian(number: int):

if number < 0 or number > 9999:
return {"error": "Number must be between 0 and 9999", "strokes": [], "staff": {}}
staff = {"x1": 0, "y1": -5, "x2": 0, "y2": 5}
units = number % 10
tens = (number // 10) % 10
hundreds = (number // 100) % 10
thousands = (number // 1000) % 10
strokes = []
if units and units in ONES_DRAWS:
strokes.extend(_polyline_to_segments(ONES_DRAWS[units]))
if tens and tens in TENS_DRAWS:
strokes.extend(_polyline_to_segments(TENS_DRAWS[tens]))
if hundreds and hundreds in HUNDREDS_DRAWS:
strokes.extend(_polyline_to_segments(HUNDREDS_DRAWS[hundreds]))
if thousands and thousands in THOUSANDS_DRAWS:
strokes.extend(_polyline_to_segments(THOUSANDS_DRAWS[thousands]))
return {
"number": number,
"strokes": strokes,
"staff": staff,
"digits": {
"units": units,
"tens": tens,
"hundreds": hundreds,
"thousands": thousands,
},
}

KEFQUWMNEX_ORDER = [
"K", "E", "F", "Q", "U", "W", "M", "N", "T", "O",
"X", "H", "G", "C", "J", "I", "R", "S", "V", "L",
"Z", "Y", "A", "D", "B", "P",
]
THRYZUNEL_ALPHABET = {
"K": {"name": "Kem'ral",
"E": {"name": "Eth'ral",
"F": {"name": "Fel'kyn",
"Q": {"name": "Qol'ral",
"U": {"name": "Ul'thun",
"W": {"name": "Wex'ral",
"M": {"name": "Mel'nex",
"N": {"name": "Nor'vel",
"T": {"name": "Tel'vel",
"O": {"name": "Ox'thun",
"X": {"name": "Xol'kyn",
"H": {"name": "Hes'vel",
"G": {"name": "Gol'nex",
"C": {"name": "Cer'mox",
"J": {"name": "Jel'mox",
"I": {"name": "Ix'thun",
"R": {"name": "Ret'kyn",
"S": {"name": "Sol'nex",
"V": {"name": "Vel'mex",
"L": {"name": "Lor'kyn",
"Z": {"name": "Zul'kem",
"Y": {"name": "Yth'nex",
"A": {"name": "Ar'vel",
"D": {"name": "Del'wyn",
"B": {"name": "Bek'tun",
"P": {"name": "Pel'mox",
}

"code": 7294, "phoneme": "/k/", "novatmpcais": 1, "position"
"code": 174, "phoneme": "/\u025b/", "novatmpcais": 2, "position&q
"code": 420, "phoneme": "/f/", "novatmpcais": 2, "position"
"code": 2224, "phoneme": "/kw/", "novatmpcais": 2, "position"
"code": 7692, "phoneme": "/u\u02d0/","novatmpcais": 2, "position&q
"code": 3467, "phoneme": "/w/", "novatmpcais": 2, "position"
"code": 7472, "phoneme": "/m/", "novatmpcais": 3, "position"
"code": 6644, "phoneme": "/n/", "novatmpcais": 4, "position"
"code": 6373, "phoneme": "/t/", "novatmpcais": 4, "position"
"code": 6824, "phoneme": "/o\u028a/","novatmpcais": 4, "position&q
"code": 1358, "phoneme": "/\u0283/", "novatmpcais": 5, "position&q
"code": 8409, "phoneme": "/h/", "novatmpcais": 5, "position"
"code": 666, "phoneme": "/g/", "novatmpcais": 6, "position"
"code": 1964, "phoneme": "/\u0283/", "novatmpcais": 6, "position&q
"code": 5968, "phoneme": "/d\u0292/","novatmpcais": 6, "position&q
"code": 6012, "phoneme": "/\u026a/", "novatmpcais": 6, "position&q
"code": 6782, "phoneme": "/r/", "novatmpcais": 6, "position"
"code": 5595, "phoneme": "/s/", "novatmpcais": 7, "position"
"code": 6344, "phoneme": "/v/", "novatmpcais": 8, "position"
"code": 9028, "phoneme": "/l/", "novatmpcais": 8, "position"
"code": 7533, "phoneme": "/z/", "novatmpcais": 9, "position"
"code": 9766, "phoneme": "/j/", "novatmpcais": 9, "position"
"code": 1320, "phoneme": "/a/", "novatmpcais": 11, "position"
"code": 1991, "phoneme": "/d/", "novatmpcais": 11, "position"
"code": 2420, "phoneme": "/b/", "novatmpcais": 11, "position"
"code": 9999, "phoneme": "/p/", "novatmpcais": 11, "position"

THRYZUNEL_PUNCTUATION = {
1: {"symbol": "\u0745", "name": "Period",
"desc": "Sentence completion"},
2: {"symbol": "\u073e", "name": "Comma",
"desc": "Pause/separation"},
3: {"symbol": "\u0f31", "name": "Question",
"desc": "Inquiry marker"},
4: {"symbol": "\u073d", "name": "Exclamation", "desc": "Emotion/intensity"},
5: {"symbol": "\u0737", "name": "Sacred Pause","desc": "Religious emphasis"},
6: {"symbol": "\u0734", "name": "Binary Link", "desc": "Dual connection"},
7: {"symbol": "\u0733", "name": "Aurora Flow", "desc": "Electromagnetic transition"},
8: {"symbol": "\u0731", "name": "Eternal Mark","desc": "Time dilation"},
9: {"symbol": "\u06e1", "name": "Completion", "desc": "N-S circle closure"},
}
THRYZUNEL_COUNTING = {
73: {"value": 1,
"name": "Base unit"},
66: {"value": 5,
"name": "Five-marker"},
99: {"value": 10,
"name": "Ten-marker"},
88: {"value": 50,
"name": "Fifty-marker"},
77: {"value": 100, "name": "Hundred-marker"},
69: {"value": 500, "name": "Five-hundred"},
13: {"value": 1000, "name": "Thousand-marker"},
33: {"value": None, "name": "Transformation marker"},
}

def get_thryzunel_data():
alphabet = []
for letter in KEFQUWMNEX_ORDER:
info = THRYZUNEL_ALPHABET[letter]
glyph = generate_cistercian(info["code"])
alphabet.append({
"letter": letter,
"name": info["name"],

"code": info["code"],
"phoneme": info["phoneme"],
"novatmpcais": info["novatmpcais"],
"position": info["position"],
"origin": info["origin"],
"glyph": glyph,
})
punctuation = []
for code, info in THRYZUNEL_PUNCTUATION.items():
glyph = generate_cistercian(code)
punctuation.append({
"code": code,
"symbol": info["symbol"],
"name": info["name"],
"desc": info["desc"],
"glyph": glyph,
})
counting = []
for code, info in THRYZUNEL_COUNTING.items():
glyph = generate_cistercian(code)
counting.append({
"code": code,
"value": info["value"],
"name": info["name"],
"glyph": glyph,
})
return {
"alphabet": alphabet,
"punctuation": punctuation,
"counting": counting,
}

def get_status():
return {
"engine": "cistercian",
"range": "0-9999",
"quadrants": [
"upper-right (units/ones)",
"upper-left (tens)",
"lower-right (hundreds)",
"lower-left (thousands)",
],
"thryzunel": {
"alphabet_count": len(THRYZUNEL_ALPHABET),
"punctuation_count": len(THRYZUNEL_PUNCTUATION),
"counting_tokens": len(THRYZUNEL_COUNTING),
},
"description": "Cistercian numeral system with Thryzunel language encoding",
}

