"""The song: tempo, melody, lyrics, chords and the shared timeline.

Audio (music, voice, sound effects) and picture (lip sync, karaoke, actions)
both read their timing from here, so they stay in sync."""

BPM = 100
BEAT = 60.0 / BPM          # 0.6 s
BAR = 4 * BEAT             # 2.4 s
INTRO_BARS = 2
DURATION = 68.0            # 28 bars = 67.2 s + a short tail

NOTE_IDX = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def hz(name):
    n = NOTE_IDX[name[0]] + 12 * (int(name[-1]) + 1)
    return 440.0 * 2 ** ((n - 69) / 12.0)


def R(beats):
    return (None, None, [(None, beats)])


# chunk = (display text, text sent to the TTS, [(note, beats), ...])  — one note per syllable
WASH = [("Wash", "wash", [("E4", 1)]), ("wash", "wash", [("E4", 1)]), ("wash,", "wash", [("E4", 1)]), R(1),
        ("scrub", "scrub", [("F4", 1)]), ("scrub", "scrub", [("F4", 1)]), ("scrub,", "scrub", [("F4", 1)]), R(1)]

LINES = [
    [("Bath", "bath", [("G4", 1)]), ("time,", "time", [("E4", 1)]), ("bath", "bath", [("G4", 1)]),
     ("time,", "time", [("E4", 1)]), ("splash", "splash", [("A4", 1)]), ("splash", "splash", [("A4", 1)]),
     ("splash!", "splash", [("G4", 1)]), R(1)],
    [("Bubbles", "bubbles", [("E4", .5), ("F4", .5)]), ("everywhere,", "everywhere", [("G4", .5), ("A4", .5), ("G4", 1)]),
     ("in a", "in a", [("E4", .5), ("D4", .5)]), ("flash!", "flash", [("C4", 2)]), R(2)],
    [("Rubber", "rubber", [("G4", .5), ("G4", .5)]), ("duck", "duck", [("A4", 1)]), ("says", "says", [("G4", 1)]),
     ("quack", "quack", [("E4", 1)]), ("quack", "quack", [("E4", 1)]), ("quack,", "quack", [("E4", 1)]), R(2)],
    [("Bobo", "bobo", [("F4", .5), ("F4", .5)]), ("sprays", "sprays", [("A4", 1)]),
     ("the water", "the water", [("G4", .5), ("F4", .5), ("E4", 1)]), ("back!", "back", [("D4", 2)]), R(2)],
    WASH,
    [("having", "having", [("G4", .5), ("G4", .5)]), ("fun", "fun", [("A4", 1)]), ("in the", "in the", [("G4", .5), ("F4", .5)]),
     ("bubble", "bubble", [("E4", .5), ("D4", .5)]), ("tub!", "tub", [("C4", 2)]), R(2)],
    WASH,
    [("I love my", "I love my", [("G4", .5), ("A4", .5), ("G4", .5)]), ("bath,", "bath", [("E4", 1.5)]),
     ("rub-a-dub-dub!", "rub a dub dub", [("F4", .5), ("E4", .5), ("D4", .5), ("C4", 1.5)]), R(2)],
    [("Shampoo", "shampoo", [("G4", .5), ("G4", .5)]), ("bubbles", "bubbles", [("A4", .5), ("A4", .5)]),
     ("on my", "on my", [("G4", 1), ("E4", 1)]), ("head,", "head", [("G4", 2)]), R(2)],
    [("now I'm", "now I'm", [("F4", .5), ("F4", .5)]), ("clean", "clean", [("A4", 1)]), ("and", "and", [("G4", .5)]),
     ("ready", "ready", [("F4", .5), ("E4", .5)]), ("for", "for", [("D4", .5)]), ("bed!", "bed", [("C4", 2)]), R(2)],
    [("Fluffy", "fluffy", [("G4", .5), ("E4", .5)]), ("towel,", "towel", [("G4", .5), ("E4", .5)]),
     ("warm", "warm", [("A4", 1)]), ("and", "and", [("G4", 1)]), ("dry,", "dry", [("E4", 2)]), R(2)],
    [("goodnight", "goodnight", [("F4", .5), ("A4", .5)]), ("bubbles,", "bubbles", [("G4", .5), ("F4", .5)]),
     ("bye", "bye", [("E4", 1)]), ("bye", "bye", [("D4", 1)]), ("bye!", "bye", [("C4", 2)]), R(2)],
]

# one chord per bar, 28 bars (intro 2, 12 lines x 2, outro 2)
CHORDS = ["C", "G",
          "C", "F", "G", "C", "C", "C", "F", "G", "C", "F", "G", "C",
          "C", "F", "G", "C", "C", "Am", "F", "C", "C", "Am", "F", "C",
          "F", "C"]


def line_start(i):
    return (INTRO_BARS + 2 * i) * BAR


def build_schedule():
    """Returns (chunks, syllables). Times in seconds."""
    chunks, syls = [], []
    for li, line in enumerate(LINES):
        t = line_start(li)
        for ci, (disp, tts, notes) in enumerate(line):
            dur = sum(b for _, b in notes) * BEAT
            if disp is not None:
                c = dict(line=li, idx=ci, text=disp, tts=tts, t0=t, t1=t + dur,
                         notes=[(n, b * BEAT) for n, b in notes])
                chunks.append(c)
                tt = t
                for n, b in notes:
                    syls.append(dict(line=li, chunk=len(chunks) - 1, note=n, t0=tt, t1=tt + b * BEAT, word=disp))
                    tt += b * BEAT
            t += dur
    return chunks, syls


CHUNKS, SYLLABLES = build_schedule()


def mouth_open(t):
    """0..1 lip-sync openness of the singer at time t."""
    for s in SYLLABLES:
        if s['t0'] - 0.04 <= t < s['t1']:
            d = s['t1'] - s['t0']
            u = (t - s['t0'] + 0.04) / (d * 0.9)
            if u > 1:
                return 0.15
            att = min(1.0, u * 6)
            return att * (1.0 - 0.35 * u)
    return 0.0


def current_line(t):
    for li in range(len(LINES)):
        a = line_start(li) - 0.35
        b = line_start(li) + 2 * BAR - 0.35
        if a <= t < b:
            return li
    return None


def syllable_times(word, line=None):
    return [s['t0'] for s in SYLLABLES if s['word'].strip(',!').lower() == word and (line is None or s['line'] == line)]


# ---- shots (start, end) in seconds ----------------------------------------
SHOTS = [
    (0.0, 4 * BAR),            # 1: Lilo runs in, waves            (intro + line 1)
    (4 * BAR, 6 * BAR),        # 2: tub fills, clapping/jumping    (line 2)
    (6 * BAR, 14 * BAR),       # 3: toys, Bobo sprays, splashing   (lines 3-6)
    (14 * BAR, 20 * BAR),      # 4: shampoo bubble crown           (lines 7-9)
    (20 * BAR, 24 * BAR),      # 5: towel + mom drying             (lines 10-11)
    (24 * BAR, DURATION),      # 6: pajamas, goodnight             (line 12 + outro)
]


def shot_at(t):
    for i, (a, b) in enumerate(SHOTS):
        if a <= t < b:
            return i
    return len(SHOTS) - 1


# ---- sound-effect / action cues shared by audio and picture ---------------
QUACKS = syllable_times('quack')                                   # duck squeaks
SPLASH_WORDS = syllable_times('splash')                            # line 1
WASH_S3 = [t for t in syllable_times('wash', 4)]                   # Lilo splashes in the tub
SCRUB_S3 = [t for t in syllable_times('scrub', 4)]
WASH_S4 = [t for t in syllable_times('wash', 6)]                   # shampoo scrubbing
SCRUB_S4 = [t for t in syllable_times('scrub', 6)]
SPRAY = (line_start(3) + 0.3, line_start(3) + 4.2)                 # Bobo's trunk shower
FILL = (SHOTS[1][0] - 0.2, SHOTS[1][1])                            # running water
CLAPS_S2 = [SHOTS[1][0] + i * BEAT for i in range(8)]
FROG_HOP = syllable_times('fun', 5)[0]
STAR_TIMES = [SHOTS[5][0] + 0.3 + i * BEAT * 0.75 for i in range(12)]
