from enum import IntEnum
from datetime import timedelta


# This is the save icon bitmap data for CTR (same for PAL and NTSC, not sure about Japan)
SAVE_SIG = bytes((
    0x53, 0x43, 0x11, 0x01, 0x82, 0x62, 0x82, 0x73, 0x82, 0x71,
    0x81, 0x46, 0x82, 0x72, 0x82, 0x81, 0x82, 0x96, 0x82, 0x85,
    0x82, 0x84, 0x81, 0x40, 0x82, 0x66, 0x82, 0x81, 0x82, 0x8D,
    0x82, 0x85, 0x82, 0x93, 0x81, 0x40, 0x82, 0x81, 0x82, 0x8E,
    0x82, 0x84, 0x81, 0x40, 0x82, 0x72, 0x82, 0x83, 0x82, 0x8F,
    0x82, 0x92, 0x82, 0x85, 0x82, 0x93, 0x81, 0x40, 0x81, 0x40,
    0x81, 0x40, 0x81, 0x40, 0x81, 0x40, 0x81, 0x40, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xA0, 0xFC, 0xB2, 0x84,
    0x6C, 0x88, 0x59, 0x89, 0x22, 0x84, 0xDF, 0xFB, 0xAD, 0xAD,
    0x25, 0x85, 0x9D, 0xCE, 0x18, 0xBE, 0xA0, 0xE8, 0xF1, 0x9C,
    0xF8, 0xE2, 0x61, 0xBC, 0x96, 0xB5, 0x81, 0xC8))

SIG_LEN = 0x80

LEADERBOARD_OFFSET = 0x2D0

PROFILE_OFFSET = 0x19C
PROFILE_LEN = 0x50

TRACK_COUNT = 18
TRACK_DATA_LEN = 0x124
LEADERBOARD_LEN = TRACK_DATA_LEN * TRACK_COUNT

RECORD_COUNT = 12
RECORD_LEN = 0x18

SAVE_LEN = 0x1800

TICK = 1000 / 960
# 1.041667 old constant if the new precision breaks it

CHARACTER = IntEnum(
    value='Character',
    names=[
        ("Crash", 0),
        ("Cortex", 1),
        ("Tiny", 2),
        ("Coco", 3),
        ("N.Gin", 4),
        ("Dingodile", 5),
        ("Polar", 6),
        ("Pura", 7),
        ("Pinstripe", 8),
        ("Papu Papu", 9),
        ("Ripper Roo", 10),
        ("Komodo Joe", 11),
        ("N.Tropy", 12),
        ("Penta Penguin", 13),
        ("Fake Crash", 14),
        ("Oxide (?)", 15)])


TRACK = IntEnum(
    value='Track',
    names=[
        ("Dingo Canyon", 0),
        ("Dragon Mines", 1),
        ("Blizzard Bluff", 2),
        ("Crash Cove", 3),
        ("Tiger Temple", 4),
        ("Papu's Pyramid", 5),
        ("Roo's Tubes", 6),
        ("Hot Air Skyway", 7),
        ("Sewer Speedway", 8),
        ("Mystery Caves", 9),
        ("Cortex Castle", 10),
        ("N.Gin Labs", 11),
        ("Polar Pass", 12),
        ("Oxide Station", 13),
        ("Coco Park", 14),
        ("Tiny Arena", 15),
        ("Slide Coliseum", 16),
        ("Turbo Track", 17)])


class CTR:
    def __init__(self, filename):
        self._save_path = filename
        self._saves = []
        self.update()

    def update(self):
        self._saves = list(self._saves)
        with open(self._save_path, 'rb') as f:
            memcard = f.read()

        search_pos = memcard.find(SAVE_SIG, 0)
        save_index = 0
        while search_pos != -1:
            start = search_pos - SIG_LEN
            end = start + SAVE_LEN
            save_data = memcard[start:end]
            if save_index < len(self._saves):
                self._saves[save_index].update(save_data)
            else:
                save = Save(save_data)
                self._saves.append(save)

            search_pos = memcard.find(SAVE_SIG, search_pos + 1)
            save_index += 1

        self._saves = tuple(self._saves)

    def __getitem__(self, i):
        return self._saves[i]

    @property
    def saves(self):
        return self._saves


class Save:
    def __init__(self, save_data):
        self._tracks = {}
        self._save_slots = []
        self.update(save_data)

    def update(self, save_data):
        self._save_slots = list(self._save_slots)
        self._checksum = save_data[6142:6144]
        self._calc_checksum = Save.check(save_data)
        self._valid = self._checksum == self._calc_checksum

        for i in range(TRACK_COUNT):
            start = LEADERBOARD_OFFSET + i * TRACK_DATA_LEN
            end = start + TRACK_DATA_LEN
            track_data = save_data[start:end]
            
            if self._tracks.get(TRACK(i)):
                self._tracks[TRACK(i)].update(track_data)
            else:
                track = Track(track_data)
                self._tracks[TRACK(i)] = track

        for i in range(4):
            start = PROFILE_OFFSET + i * PROFILE_LEN
            end = start + PROFILE_LEN
            if save_data[start + 19] != 255:
                save_slot = SaveSlot(save_data[start:end])
            else:
                save_slot = None
            self._save_slots.append(save_slot)

        self._save_slots = tuple(self._save_slots)

    def __getitem__(self, i):
        return self._tracks[i]

    @staticmethod
    def check(save_data):
        save_data = bytearray(save_data)
        a = 0
        for b in range(5760):
            c = save_data[b + 384]
            d = 7
            e = 65536
            f = e
            f |= 4129
            save_data[6142] = 0
            save_data[6143] = 0
            while d < 65535:
                a <<= 1
                g = c >> d
                g &= 1
                a |= g
                g = a & e
                if g != 0:
                    a ^= f
                d = d + 65535 & 65535
        save_data[6142] = a >> 8
        save_data[6143] = a & 255
        return bytes(save_data[6142:6144])

    @staticmethod
    def decode_name(s):
        return s.decode("utf-8").replace("\x00", "")

    @property
    def tracks(self):
        return self._tracks

    @property
    def checksum(self):
        return self._checksum

    @property
    def calc_checksum(self):
        return self._calc_checksum

    @property
    def valid(self):
        return self._valid
    
    @property
    def save_slots(self):
        return self._save_slots


class SaveSlot:
    def __init__(self, save_data):
        self._name = Save.decode_name(save_data[0:8])
        self._character = CHARACTER(save_data[19])

    @property
    def name(self):
        return self._name

    @property
    def character(self):
        return self._character


class Track:

    def __init__(self, track_data):
        self.update(track_data)
    
    def update(self, track_data):
        records = []
        for i in range(12):
            start = i * RECORD_LEN
            end = start + RECORD_LEN
            record = Record(track_data[start:end])
            records.append(record)

        self._trial_best_lap = records[0]
        self._trials = sorted(records[1:6], key=lambda r: r._time._ticks)

        self._relic_best_lap = records[6]
        self._relics = sorted(records[7:12], key=lambda r: r._time._ticks)

        self._trials = tuple(self._trials)
        self._relics = tuple(self._relics)

    @property
    def trial_best_lap(self):
        return self._trial_best_lap

    @property
    def relic_best_lap(self):
        return self._relic_best_lap

    @property
    def trials(self):
        return self._trials

    @property
    def relics(self):
        return self._relics


class Record:
    def __init__(self, record_data):
        ticks = int.from_bytes(record_data[0:4], byteorder='little')
        self._time = RecordTime(ticks)
        self._name = Save.decode_name(record_data[4:12])
        self._character = CHARACTER(record_data[22])

    @property
    def time(self):
        return self._time

    @property
    def name(self):
        return self._name

    @property
    def character(self):
        return self._character


class RecordTime:
    @staticmethod
    def to_ms(ticks): return ticks * TICK

    def __init__(self, ticks):
        self._ticks = ticks
        self._ms = RecordTime.to_ms(ticks)

    def ctr_format(self):
        secs = self._ms / 1000
        m = int(secs / 60)
        s = secs % 60
        ss = s-s % 0.001
        return '{}:{:05.2f}'.format(m, ss)

    def __str__(self):
        return self.ctr_format()

    @property
    def ticks(self):
        return self._ticks

    @property
    def ms(self):
        return self._ms
