# -*- coding: utf-8 -*-
"""
효과음 합성기
사각파/삼각파/노이즈를 직접 계산해서 8비트 효과음을 만들어요. 외부 소리 파일이 필요 없어서
저작권 걱정이 없고, exe로 묶을 때도 편해요.
"""
import math
import random
import array

RATE = 44100


def _osc(kind, phase, duty):
    """phase: 0~1 사이 값 → -1~1 파형"""
    if kind == "square":
        return 1.0 if phase < duty else -1.0
    if kind == "tri":
        return 4.0 * abs(phase - 0.5) - 1.0
    if kind == "saw":
        return 2.0 * phase - 1.0
    return random.uniform(-1.0, 1.0)  # noise


def tone(freq, dur, vol=0.5, kind="square", duty=0.5, slide=0.0, decay=0.85):
    """freq(Hz)에서 시작해 slide(Hz/초)만큼 음이 변하는 소리. decay: 끝에서 얼마나 작아지는지(0~1)."""
    n = int(RATE * dur)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / RATE
        f = max(20.0, freq + slide * t)
        phase = (phase + f / RATE) % 1.0
        env = 1.0 - decay * (i / n)
        attack = min(1.0, i / (RATE * 0.004))
        out.append(_osc(kind, phase, duty) * vol * env * attack)
    return out


def noise(dur, vol=0.4, decay=0.95, hold=1):
    """hold 샘플마다 값을 바꿔서 '거친' 정도를 조절하는 노이즈 (hold가 클수록 낮은 소리)"""
    n = int(RATE * dur)
    out = []
    v = 0.0
    for i in range(n):
        if i % hold == 0:
            v = random.uniform(-1.0, 1.0)
        out.append(v * vol * (1.0 - decay * (i / n)))
    return out


def silence(dur):
    return [0.0] * int(RATE * dur)


def seq(*parts):
    out = []
    for p in parts:
        out.extend(p)
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def note(semitone_from_a4, dur, vol=0.45, kind="square", duty=0.5):
    return tone(440.0 * 2 ** (semitone_from_a4 / 12.0), dur, vol, kind, duty, decay=0.6)


# ---------------------------------------------------------------- 효과음 정의
def _arp(semis, step=0.07, last=0.22, vol=0.4):
    parts = [note(s, step, vol) for s in semis[:-1]]
    parts.append(note(semis[-1], last, vol))
    return seq(*parts)


BUILDERS = {
    "tick": lambda: tone(760, 0.022, 0.22),
    "click": lambda: seq(tone(880, 0.045, 0.35), tone(1320, 0.06, 0.35)),
    "back": lambda: seq(tone(660, 0.045, 0.3), tone(440, 0.07, 0.3)),
    "correct": lambda: seq(note(3, 0.07), note(10, 0.16)),
    "wrong": lambda: mix(tone(170, 0.22, 0.45, slide=-120), noise(0.12, 0.25, hold=6)),
    "flip": lambda: tone(540, 0.04, 0.3),
    "match": lambda: seq(note(7, 0.06), note(12, 0.06), note(16, 0.14)),
    "count": lambda: tone(660, 0.1, 0.4),
    "go": lambda: tone(990, 0.28, 0.45, decay=0.7),
    "clear": lambda: _arp([3, 7, 10, 15], 0.075, 0.3, 0.42),
    "warn": lambda: seq(tone(520, 0.05, 0.35), silence(0.04), tone(520, 0.05, 0.35)),
    "skip": lambda: seq(tone(500, 0.06, 0.35, slide=-300), tone(330, 0.1, 0.35, slide=-300)),
    "gameover": lambda: seq(note(-2, 0.18, 0.45, "tri"), note(-6, 0.18, 0.45, "tri"), note(-10, 0.18, 0.45, "tri"),
                            tone(110, 0.6, 0.5, "tri", slide=-50)),
    "dial": lambda: seq(noise(0.02, 0.5, 0.9, hold=3), silence(0.03), noise(0.02, 0.5, 0.9, hold=3)),
    "unlock": lambda: mix(tone(120, 0.5, 0.5, "tri", slide=300), noise(0.5, 0.3, 0.9, hold=40)),
    "vault_open": lambda: mix(
        noise(1.4, 0.4, 0.8, hold=30),
        seq(silence(0.25), _arp([0, 4, 7, 12, 16, 19, 24], 0.09, 0.8, 0.35)),
    ),
    "move": lambda: tone(300, 0.02, 0.18, "tri"),
    "rotate": lambda: tone(480, 0.04, 0.22, "tri"),
    "hold": lambda: seq(tone(400, 0.04, 0.25, "tri"), tone(560, 0.05, 0.25, "tri")),
    "drop": lambda: mix(tone(160, 0.09, 0.45, "tri", slide=-400), noise(0.06, 0.3, hold=8)),
    "line": lambda: _arp([7, 12, 16], 0.05, 0.14, 0.4),
    "pc": lambda: _arp([0, 4, 7, 12, 16, 19, 24, 28], 0.06, 0.4, 0.4),
    "level": lambda: seq(note(0, 0.08), note(7, 0.14)),
}


def build_samples(name):
    return BUILDERS[name]()


def to_pcm16(samples, channels=2):
    """float(-1~1) 샘플 → 16bit 정수 바이트 (모노를 채널 수만큼 복제)"""
    data = array.array("h")
    for v in samples:
        iv = int(max(-1.0, min(1.0, v)) * 30000)
        for _ in range(channels):
            data.append(iv)
    return data.tobytes()
