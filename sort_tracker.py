import numpy as np
from filterpy.kalman import KalmanFilter

class Track:
    count = 0

    def __init__(self, bbox):
        self.id = Track.count
        Track.count += 1
        self.bbox = bbox
        self.missed = 0


class SortTracker:

    def __init__(self):
        self.tracks = []

    def update(self, detections):

        updated_tracks = []

        for det in detections:

            matched = False

            for track in self.tracks:

                iou = self.iou(track.bbox, det)

                if iou > 0.3:
                    track.bbox = det
                    track.missed = 0
                    updated_tracks.append(track)
                    matched = True
                    break

            if not matched:
                updated_tracks.append(Track(det))

        self.tracks = updated_tracks

        return [(t.id, t.bbox) for t in self.tracks]

    def iou(self, boxA, boxB):

        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)

        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        return interArea / float(boxAArea + boxBArea - interArea + 1e-5)