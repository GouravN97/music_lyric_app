import numpy as np

import librosa

y,sr=librosa.load(librosa.ex('nutcracker'))

hop_length=512 #512 samples ~23ms

# Separate harmonics and percussives into two waveforms
y_harmonic, y_percussive=librosa.effects.hpss(y)

#beat track on percussive signals
tempo,beat_frames=librosa.beat.beat_track(y=y_percussive,sr=sr)

# Compute MFCC features from the raw signal
mfcc=librosa.feature.mfcc(y=y,sr=sr,hop_length=hop_length,n_mfcc=13)

# And the first-order differences (delta features)
mfcc_delta=librosa.feature.delta(mfcc)

# Stack and synchronize between beat events
# This time, we'll use the mean value (default) instead of median
beat_mfcc_delta = librosa.util.sync(np.vstack([mfcc, mfcc_delta]),beat_frames)

# Compute chroma features from the harmonic signal
chromagram= librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
beat_chroma=librosa.util.sync(chromagram, beat_frames,aggregate=np.median)


# Finally, stack all beat-synchronous features together
beat_features=np.vstack([beat_chroma,beat_mfcc_delta])