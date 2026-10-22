#!/usr/bin/env python3
"""Compare saved Serval 4.3 TPX4 single-chip file/TCP captures, offline.

This diagnostic accepts the binary-ToA representation observed in Serval 4.3
captures, with PID/PTS/MIN/MAX metadata. It is not a hardware packet decoder
or a fine-time/calibration implementation. Event identity includes the full
64-bit pixel word and unwrapped coarse ToA; multiplicity is preserved.

By default, every completed shutter interval must match. An explicit frame
period can exclude a short final interval caused by stopping mid-frame; the
excluded interval remains visible in the JSON and in whole-capture differences.

Exit codes: 0 = equal within selected shutters; 1 = event differences;
2 = unsupported, malformed or incompatible inputs. JSON goes to stdout.
"""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import sys


MASK48 = (1 << 48) - 1
MASK54 = (1 << 54) - 1
HEADER = struct.Struct("<4sBBH")
STATUS_NAMES = {224: "heartbeat", 225: "shutter_rise", 226: "shutter_fall"}
METADATA_NAMES = {252: "pid", 253: "pts", 254: "min", 255: "max"}


@dataclass
class Capture:
    summary: dict
    events: Counter
    intervals: dict


def eoc(word):
    return (word >> 55) & 255


def read_capture(path):
    digest = hashlib.sha256()
    events = Counter()
    chunks, controls = Counter(), Counter()
    intervals = defaultdict(list)
    opened, last_pid = {}, {}
    pid_gaps = 0
    byte_count = 0
    with path.open("rb") as source:
        while True:
            offset = byte_count
            header = source.read(HEADER.size)
            if not header:
                break
            if len(header) != HEADER.size:
                raise ValueError(f"{path.name}: truncated header at {offset}")
            magic, stream, reserved, size = HEADER.unpack(header)
            if magic != b"TPX4" or stream not in (0, 1) or reserved:
                raise ValueError(f"{path.name}: unsupported header at {offset}")
            if not size or size % 8:
                raise ValueError(f"{path.name}: invalid payload size at {offset}")
            payload = source.read(size)
            if len(payload) != size:
                raise ValueError(f"{path.name}: truncated payload at {offset}")
            digest.update(header)
            digest.update(payload)
            byte_count += HEADER.size + size
            words = [item[0] for item in struct.iter_unpack("<Q", payload)]
            if len(words) < 4 or eoc(words[0]) != 252 or [eoc(w) for w in words[-3:]] != [253, 254, 255]:
                raise ValueError(f"{path.name}: missing PID/PTS/MIN/MAX at {offset}")
            if any((word >> 63) != stream for word in words):
                raise ValueError(f"{path.name}: stream/top-bit mismatch at {offset}")
            minimum, maximum = words[-2] & MASK54, words[-1] & MASK54
            if minimum > maximum or minimum % 16 or maximum % 16:
                raise ValueError(f"{path.name}: invalid coarse packet bounds at {offset}")
            pid = words[0] & MASK48
            if pid != last_pid.get(stream, pid - 1) + 1:
                pid_gaps += 1
            last_pid[stream] = pid
            # Bounds are in 1.5625-ns units; pixel coarse ToA is in 25-ns units.
            reference = minimum >> 4
            for index, word in enumerate(words):
                code = eoc(word)
                if code < 224:
                    low_toa = (word >> 30) & 65535
                    delta = (low_toa - reference + 32768) % 65536 - 32768
                    coarse = reference + delta
                    if not minimum >> 4 <= coarse <= maximum >> 4:
                        raise ValueError(f"{path.name}: ambiguous/out-of-bounds ToA at {offset}, word {index}")
                    events[(stream, coarse, word)] += 1
                elif code in STATUS_NAMES:
                    if word & (127 << 48):
                        raise ValueError(f"{path.name}: invalid status timestamp at {offset}")
                    reference = word & MASK48
                    controls[STATUS_NAMES[code]] += 1
                    if code == 225:
                        if stream in opened:
                            raise ValueError(f"{path.name}: repeated shutter rise for stream {stream}")
                        opened[stream] = reference
                    elif code == 226:
                        start = opened.pop(stream, None)
                        if start is None or reference <= start:
                            raise ValueError(f"{path.name}: unpaired/nonpositive shutter interval for stream {stream}")
                        if intervals[stream] and start < intervals[stream][-1][1]:
                            raise ValueError(f"{path.name}: overlapping shutter intervals for stream {stream}")
                        intervals[stream].append((start, reference))
                elif code in METADATA_NAMES:
                    if index not in (0, len(words) - 3, len(words) - 2, len(words) - 1):
                        raise ValueError(f"{path.name}: unexpected embedded metadata at {offset}")
                    controls[METADATA_NAMES[code]] += 1
                else:
                    raise ValueError(f"{path.name}: unsupported EOC {code} at {offset}")
            chunks[stream] += 1
    if not events or set(intervals) != set(chunks) or any(not value for value in intervals.values()):
        raise ValueError(f"{path.name}: no complete shutter coverage for every stream")
    summary = {
        "name": path.name,
        "bytes": byte_count,
        "sha256": digest.hexdigest(),
        "chunks_per_stream": dict(chunks),
        "pixel_events": sum(events.values()),
        "controls": dict(controls),
        "packet_id_discontinuities": pid_gaps,
        "unclosed_shutter_start_25ns": dict(opened),
        "last_pixel_coarse_25ns": max(key[1] for key in events),
    }
    return Capture(summary, events, dict(intervals))


def frame_intervals(capture, period):
    if period is None:
        return capture.intervals, {}
    if period <= 0:
        raise ValueError("frame period must be positive")
    selected, excluded = {}, {}
    for stream, ranges in capture.intervals.items():
        selected[stream] = []
        for index, (start, stop) in enumerate(ranges):
            if stop - start == period:
                selected[stream].append((start, stop))
            elif index == len(ranges) - 1 and 0 < stop - start < period:
                excluded[stream] = [(start, stop)]
            else:
                raise ValueError(f"{capture.summary['name']}: expected full frames; only a shorter final interval can be excluded")
        if not selected[stream]:
            raise ValueError(f"{capture.summary['name']}: no full frames for stream {stream}")
    return selected, excluded


def selected_events(capture, intervals=None):
    if intervals is None:
        intervals = capture.intervals
    selected = Counter()
    counts = {stream: [0] * len(ranges) for stream, ranges in intervals.items()}
    excluded = Counter()
    for key, multiplicity in capture.events.items():
        stream, coarse, _ = key
        for index, (start, stop) in enumerate(intervals[stream]):
            if start <= coarse < stop:
                selected[key] = multiplicity
                counts[stream][index] += multiplicity
                break
        else:
            excluded[stream] += multiplicity
    capture.summary.update({
        "selected_events": sum(selected.values()),
        "events_per_interval_per_stream": counts,
        "excluded_events_per_stream": dict(excluded),
    })
    return selected


def difference_summary(events):
    return {
        "events": sum(events.values()),
        "examples": [
            {"stream": stream, "coarse_25ns": coarse, "word": f"0x{word:016x}", "count": count}
            for (stream, coarse, word), count in sorted(events.items())[:8]
        ],
    }


def compare(left, right, frame_period=None):
    left_intervals, left_partial = frame_intervals(left, frame_period)
    right_intervals, right_partial = frame_intervals(right, frame_period)
    if left_intervals != right_intervals:
        raise ValueError("completed shutter intervals differ between captures")
    lhs, rhs = selected_events(left, left_intervals), selected_events(right, right_intervals)
    selected_left_only, selected_right_only = lhs - rhs, rhs - lhs
    return {
        "schema": "serval43-tpx4-coarse-comparison-v2",
        "equivalent_within_completed_shutters": lhs == rhs,
        "equivalent_within_selected_shutters": lhs == rhs,
        "selection": {
            "mode": "all_completed_shutters" if frame_period is None else "full_frame_period",
            "frame_period_25ns": frame_period,
            "left_excluded_final_partial_intervals_25ns_per_stream": left_partial,
            "right_excluded_final_partial_intervals_25ns_per_stream": right_partial,
        },
        "identity": "stream, unwrapped binary coarse ToA, full 64-bit pixel word; multiplicity preserved",
        "intervals_25ns_per_stream": left_intervals,
        "original_left_intervals_25ns_per_stream": left.intervals,
        "original_right_intervals_25ns_per_stream": right.intervals,
        "left": left.summary,
        "right": right.summary,
        "selected_left_only": difference_summary(selected_left_only),
        "selected_right_only": difference_summary(selected_right_only),
        "all_left_only": difference_summary(left.events - right.events),
        "all_right_only": difference_summary(right.events - left.events),
        "limitations": "Saved Serval 4.3 single-chip captures only; no fine-time, calibration, hardware-loss or throughput qualification.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--frame-period-25ns", type=int,
                        help="compare only full frames of this coarse duration; explicitly report a shorter final interval")
    args = parser.parse_args()
    try:
        report = compare(read_capture(args.left), read_capture(args.right), args.frame_period_25ns)
    except (OSError, ValueError) as error:
        print(f"TPX4 comparison failed: {error}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0 if report["equivalent_within_completed_shutters"] else 1


if __name__ == "__main__":
    sys.exit(main())
