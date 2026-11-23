# -*- coding: utf-8 -*-
"""오디오 관리: BGM(ogg 루프)과 효과음(코드로 합성)"""
import os
import pygame

from . import config, sfx
from .utils import resource_path


class Audio:
    def __init__(self, db):
        self.db = db
        self.enabled = False
        self.sounds = {}
        self.current = None          # 지금 재생 중인 BGM 역할 이름
        self.paused = False
        self.bgm_vol = int(db.get_setting("bgm_vol", config.DEFAULT_SETTINGS["bgm_vol"])) / 100.0
        self.sfx_vol = int(db.get_setting("sfx_vol", config.DEFAULT_SETTINGS["sfx_vol"])) / 100.0
        self.files = self._find_bgm_files()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            self.enabled = pygame.mixer.get_init() is not None
        except pygame.error:
            self.enabled = False
        self.apply_volumes()

    # ------------------------------------------------------------ BGM
    def _find_bgm_files(self):
        folder = resource_path("assets", "bgm")
        found = {}
        try:
            names = os.listdir(folder)
        except OSError:
            names = []
        def norm(s):
            # 공백, 밑줄, 대괄호, 점 등을 모두 없애고 소문자 영문/숫자만 비교해요
            # (예: 'Stage 1' 도 'Stage_1' 도 모두 'stage1' 로 맞춰져요)
            return "".join(ch for ch in s.lower() if ch.isalnum())

        for role, keyword in config.BGM_KEYWORDS.items():
            for n in names:
                if norm(keyword) in norm(n) and n.lower().endswith((".ogg", ".mp3", ".wav")):
                    found[role] = os.path.join(folder, n)
                    break
        return found

    def apply_volumes(self):
        if not self.enabled:
            return
        pygame.mixer.music.set_volume(self.bgm_vol)
        for s in self.sounds.values():
            s.set_volume(self.sfx_vol)

    def play_bgm(self, role, restart=False):
        """같은 곡이 이미 나오고 있으면 그대로 두고, 아니면 처음부터 루프 재생해요."""
        if not self.enabled:
            return
        if self.current == role and not restart and pygame.mixer.music.get_busy():
            return
        path = self.files.get(role)
        if not path:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.bgm_vol)
            pygame.mixer.music.play(loops=-1, fade_ms=250)
            self.current = role
            self.paused = False
        except pygame.error:
            self.current = None

    def stop_bgm(self):
        if not self.enabled:
            return
        pygame.mixer.music.stop()
        self.current = None
        self.paused = False

    def pause_bgm(self):
        if self.enabled and self.current and not self.paused:
            pygame.mixer.music.pause()
            self.paused = True

    def resume_bgm(self):
        if self.enabled and self.current and self.paused:
            pygame.mixer.music.unpause()
            self.paused = False

    # ------------------------------------------------------------ 효과음
    def play(self, name):
        if not self.enabled or self.sfx_vol <= 0:
            return
        snd = self.sounds.get(name)
        if snd is None:
            try:
                init = pygame.mixer.get_init()
                channels = init[2] if init else 2
                samples = sfx.build_samples(name)
                snd = pygame.mixer.Sound(buffer=sfx.to_pcm16(samples, channels))
                snd.set_volume(self.sfx_vol)
                self.sounds[name] = snd
            except (pygame.error, KeyError, TypeError):
                return
        snd.play()

    def preload(self, names):
        for n in names:
            self.play_silent(n)

    def play_silent(self, name):
        """미리 만들어 두기만 하고 소리는 내지 않아요 (처음 재생할 때 끊기지 않게)."""
        if not self.enabled or name in self.sounds:
            return
        try:
            init = pygame.mixer.get_init()
            channels = init[2] if init else 2
            snd = pygame.mixer.Sound(buffer=sfx.to_pcm16(sfx.build_samples(name), channels))
            snd.set_volume(self.sfx_vol)
            self.sounds[name] = snd
        except (pygame.error, KeyError, TypeError):
            pass

    # ------------------------------------------------------------ 설정값 저장
    def set_bgm_volume(self, pct):
        self.bgm_vol = max(0, min(100, int(pct))) / 100.0
        self.db.set_setting("bgm_vol", int(self.bgm_vol * 100))
        self.apply_volumes()

    def set_sfx_volume(self, pct):
        self.sfx_vol = max(0, min(100, int(pct))) / 100.0
        self.db.set_setting("sfx_vol", int(self.sfx_vol * 100))
        self.apply_volumes()
