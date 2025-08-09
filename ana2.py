import librosa
import numpy as np
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def detect_beats(audio_file):
    """Detect beat timing in an audio file"""
    y, sr = librosa.load(audio_file)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)
    return beat_times, tempo, beat_frames, y, sr

def analyze_beat_energy(y, sr, beat_times):
    """
    Analyze energy between every 2 beats
    
    Args:
        y: audio signal
        sr: sample rate
        beat_times: array of beat timestamps
    
    Returns:
        list of segments with energy classification
    """
    hop_length = 512
    
    # Calculate audio features for entire track
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    rms_energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]
    
    # Smooth features
    spectral_centroids = gaussian_filter1d(spectral_centroids, sigma=1)
    rms_energy = gaussian_filter1d(rms_energy, sigma=1)
    
    # Convert to time frames for indexing
    time_frames = librosa.frames_to_time(range(len(rms_energy)), sr=sr, hop_length=hop_length)
    
    segments = []
    
    # Process every single beat
    for i in range(len(beat_times) - 1):
        start_time = beat_times[i]
        end_time = beat_times[i + 1] if i + 1 < len(beat_times) else beat_times[i] + (beat_times[i] - beat_times[i-1])
        
        # Find frame indices for this time range
        start_frame = np.argmin(np.abs(time_frames - start_time))
        end_frame = np.argmin(np.abs(time_frames - end_time))
        
        if start_frame >= end_frame:
            continue
            
        # Calculate average features for this segment
        segment_rms = np.mean(rms_energy[start_frame:end_frame])
        segment_centroid = np.mean(spectral_centroids[start_frame:end_frame])
        segment_zcr = np.mean(zero_crossing_rate[start_frame:end_frame])
        
        # Composite energy score
        energy_score = (
            0.5 * (segment_rms / np.max(rms_energy)) +
            0.5 * (segment_centroid / np.max(spectral_centroids)) +
            0.0 * (segment_zcr / np.max(zero_crossing_rate))
        )
        
        segments.append({
            'start_time': start_time,
            'end_time': end_time,
            'energy': energy_score,
            'beat_number': i + 1,
            'rms': segment_rms,
            'centroid': segment_centroid,
            'zcr': segment_zcr  # Added ZCR to the segment data
        })
    
    return segments

def classify_beat_segments(segments, threshold=0.5):
    """Classify beat segments as high or low energy"""
    energies = [seg['energy'] for seg in segments]
    energy_threshold = np.percentile(energies, threshold * 100)
    
    classified = []
    for seg in segments:
        classification = 'HIGH_ENERGY' if seg['energy'] >= energy_threshold else 'LOW_ENERGY'
        
        classified.append({
            **seg,
            'classification': classification
        })
    
    return classified

def identify_energy_neighborhoods(classified_segments, min_section_duration=8.0, hysteresis_factor=0.15):
    """
    Group consecutive segments into musically meaningful neighborhoods (verses, choruses, etc.)
    Every beat is analyzed but short sections are merged to create meaningful song structure
    
    Args:
        classified_segments: list of classified beat segments
        min_section_duration: minimum duration for a musical section (seconds)
        hysteresis_factor: additional threshold to prevent rapid switching
    
    Returns:
        list of energy neighborhoods representing song structure
    """
    if not classified_segments:
        return []
    
    # First pass: apply hysteresis to reduce rapid switching
    smoothed_segments = apply_energy_hysteresis(classified_segments, hysteresis_factor)
    
    # Second pass: create initial neighborhoods
    initial_neighborhoods = create_initial_neighborhoods(smoothed_segments)
    
    # Third pass: merge short sections to meet minimum duration
    final_neighborhoods = merge_short_neighborhoods(initial_neighborhoods, min_section_duration)
    
    # Assign final IDs
    for i, neighborhood in enumerate(final_neighborhoods):
        neighborhood['neighborhood_id'] = i + 1
        neighborhood['duration'] = neighborhood['end_time'] - neighborhood['start_time']
        neighborhood['avg_energy'] = np.mean([s['energy'] for s in neighborhood['segments']])
    
    return final_neighborhoods

def apply_energy_hysteresis(classified_segments, hysteresis_factor):
    """Apply hysteresis to prevent rapid energy classification switching"""
    if not classified_segments:
        return []
    
    # Calculate energy threshold with hysteresis bands
    energies = [seg['energy'] for seg in classified_segments]
    base_threshold = np.percentile(energies, 50)  # median
    
    high_threshold = base_threshold * (1 + hysteresis_factor)
    low_threshold = base_threshold * (1 - hysteresis_factor)
    
    smoothed = []
    current_state = classified_segments[0]['classification']
    
    for segment in classified_segments:
        original_energy = segment['energy']
        
        # Apply hysteresis logic
        if current_state == 'LOW_ENERGY':
            # Need to exceed high threshold to switch to high energy
            new_classification = 'HIGH_ENERGY' if original_energy > high_threshold else 'LOW_ENERGY'
        else:  # current_state == 'HIGH_ENERGY'
            # Need to drop below low threshold to switch to low energy
            new_classification = 'LOW_ENERGY' if original_energy < low_threshold else 'HIGH_ENERGY'
        
        current_state = new_classification
        
        # Create smoothed segment
        smoothed_segment = segment.copy()
        smoothed_segment['classification'] = new_classification
        smoothed_segment['original_classification'] = segment['classification']
        smoothed.append(smoothed_segment)
    
    return smoothed

def create_initial_neighborhoods(segments):
    """Create initial neighborhoods from consecutive same-classification segments"""
    if not segments:
        return []
    
    neighborhoods = []
    current_neighborhood = {
        'classification': segments[0]['classification'],
        'start_time': segments[0]['start_time'],
        'end_time': segments[0]['end_time'],
        'segments': [segments[0]]
    }
    
    for segment in segments[1:]:
        if segment['classification'] == current_neighborhood['classification']:
            # Extend current neighborhood
            current_neighborhood['end_time'] = segment['end_time']
            current_neighborhood['segments'].append(segment)
        else:
            # Finalize current neighborhood
            neighborhoods.append(current_neighborhood)
            
            # Start new neighborhood
            current_neighborhood = {
                'classification': segment['classification'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'segments': [segment]
            }
    
    # Add final neighborhood
    neighborhoods.append(current_neighborhood)
    return neighborhoods

def merge_short_neighborhoods(neighborhoods, min_duration):
    """Merge neighborhoods that are shorter than minimum duration"""
    if not neighborhoods:
        return []
    
    merged = []
    used = [False] * len(neighborhoods)  # Track which neighborhoods have been consumed
    
    i = 0
    while i < len(neighborhoods):
        if used[i]:
            i += 1
            continue
            
        current = neighborhoods[i]
        current_duration = current['end_time'] - current['start_time']
        
        if current_duration >= min_duration:
            # Neighborhood is long enough, keep as is
            merged.append(current)
            used[i] = True
            i += 1
        else:
            # Neighborhood is too short, merge with adjacent ones
            merged_neighborhood, consumed_indices = expand_neighborhood_to_min_duration(
                neighborhoods, i, min_duration, used)
            
            # Mark all consumed neighborhoods as used
            for idx in consumed_indices:
                used[idx] = True
            
            merged.append(merged_neighborhood)
            i += 1
    
    return merged

def expand_neighborhood_to_min_duration(neighborhoods, center_idx, min_duration, used):
    """Expand a neighborhood in both directions until minimum duration is reached"""
    if used[center_idx]:
        return None, []
    
    # Start with center neighborhood
    merged = {
        'classification': neighborhoods[center_idx]['classification'],
        'start_time': neighborhoods[center_idx]['start_time'],
        'end_time': neighborhoods[center_idx]['end_time'],
        'segments': neighborhoods[center_idx]['segments'][:]
    }
    
    consumed_indices = [center_idx]
    left_idx = center_idx - 1
    right_idx = center_idx + 1
    
    # Expand until we reach minimum duration
    while (merged['end_time'] - merged['start_time']) < min_duration:
        can_extend_left = left_idx >= 0 and not used[left_idx]
        can_extend_right = right_idx < len(neighborhoods) and not used[right_idx]
        
        if not can_extend_left and not can_extend_right:
            break
        
        # Prefer extending in direction with more similar energy
        if can_extend_left and can_extend_right:
            left_energy = np.mean([s['energy'] for s in neighborhoods[left_idx]['segments']])
            right_energy = np.mean([s['energy'] for s in neighborhoods[right_idx]['segments']])
            current_energy = np.mean([s['energy'] for s in merged['segments']])
            
            left_similarity = abs(left_energy - current_energy)
            right_similarity = abs(right_energy - current_energy)
            extend_left = left_similarity <= right_similarity
        else:
            extend_left = can_extend_left
        
        if extend_left:
            # Extend leftward
            left_neighbor = neighborhoods[left_idx]
            merged['start_time'] = left_neighbor['start_time']
            merged['segments'] = left_neighbor['segments'] + merged['segments']
            consumed_indices.append(left_idx)
            left_idx -= 1
        else:
            # Extend rightward  
            right_neighbor = neighborhoods[right_idx]
            merged['end_time'] = right_neighbor['end_time']
            merged['segments'] = merged['segments'] + right_neighbor['segments']
            consumed_indices.append(right_idx)
            right_idx += 1
    
    # Determine final classification based on majority of segments
    classifications = [neighborhoods[idx]['classification'] for idx in consumed_indices]
    high_count = classifications.count('HIGH_ENERGY')
    low_count = classifications.count('LOW_ENERGY')
    merged['classification'] = 'HIGH_ENERGY' if high_count >= low_count else 'LOW_ENERGY'
    
    return merged, consumed_indices

def detect_energy_transitions(classified_segments, spike_threshold=0.3, lookback_window=3):
    """
    Detect sharp spikes and falls in energy that indicate verse/chorus transitions
    
    Args:
        classified_segments: list of classified beat segments
        spike_threshold: minimum energy change to consider a transition
        lookback_window: number of beats to look back for comparison
    
    Returns:
        list of energy transitions (spikes and falls)
    """
    if len(classified_segments) < lookback_window + 1:
        return []
    
    transitions = []
    
    for i in range(lookback_window, len(classified_segments)):
        current_energy = classified_segments[i]['energy']
        
        # Calculate baseline energy from lookback window
        baseline_energies = [classified_segments[j]['energy'] 
                           for j in range(i - lookback_window, i)]
        baseline_energy = np.mean(baseline_energies)
        
        # Calculate energy change
        energy_change = current_energy - baseline_energy
        relative_change = energy_change / baseline_energy if baseline_energy > 0 else 0
        
        # Detect significant transitions
        if abs(relative_change) >= spike_threshold:
            transition_type = 'SPIKE' if energy_change > 0 else 'FALL'
            
            # Determine likely musical transition
            if transition_type == 'SPIKE':
                musical_transition = 'VERSE_TO_CHORUS'
                description = f"Energy spike (+{relative_change:.1%}) - likely verse to chorus"
            else:
                musical_transition = 'CHORUS_TO_VERSE'
                description = f"Energy fall ({relative_change:.1%}) - likely chorus to verse"
            
            transition = {
                'beat_number': classified_segments[i]['beat_number'],
                'time': classified_segments[i]['start_time'],
                'transition_type': transition_type,
                'musical_transition': musical_transition,
                'energy_change': energy_change,
                'relative_change': relative_change,
                'current_energy': current_energy,
                'baseline_energy': baseline_energy,
                'description': description
            }
            
            transitions.append(transition)
    
    return transitions

def refine_transitions(transitions, min_time_gap=5.0):
    """
    Remove transitions that are too close together to avoid noise
    Keep the strongest transition in each time window
    
    Args:
        transitions: list of detected transitions
        min_time_gap: minimum time between transitions (seconds)
    
    Returns:
        filtered list of significant transitions
    """
    if not transitions:
        return []
    
    refined = []
    last_time = -float('inf')
    
    # Sort by time
    transitions_sorted = sorted(transitions, key=lambda x: x['time'])
    
    for transition in transitions_sorted:
        if transition['time'] - last_time >= min_time_gap:
            refined.append(transition)
            last_time = transition['time']
        else:
            # If too close, keep the stronger transition
            if refined and abs(transition['relative_change']) > abs(refined[-1]['relative_change']):
                refined[-1] = transition
    
    return refined

def analyze_neighborhood_patterns(neighborhoods):
    """Analyze patterns in energy neighborhoods"""
    high_energy_neighborhoods = [n for n in neighborhoods if n['classification'] == 'HIGH_ENERGY']
    low_energy_neighborhoods = [n for n in neighborhoods if n['classification'] == 'LOW_ENERGY']
    
    stats = {
        'total_neighborhoods': len(neighborhoods),
        'high_energy_count': len(high_energy_neighborhoods),
        'low_energy_count': len(low_energy_neighborhoods),
        'avg_high_energy_duration': np.mean([n['duration'] for n in high_energy_neighborhoods]) if high_energy_neighborhoods else 0,
        'avg_low_energy_duration': np.mean([n['duration'] for n in low_energy_neighborhoods]) if low_energy_neighborhoods else 0,
        'longest_high_energy': max([n['duration'] for n in high_energy_neighborhoods]) if high_energy_neighborhoods else 0,
        'longest_low_energy': max([n['duration'] for n in low_energy_neighborhoods]) if low_energy_neighborhoods else 0
    }
    
    return stats, high_energy_neighborhoods, low_energy_neighborhoods

def plot_energy_with_transitions(y, sr, beat_times, classified_segments, neighborhoods, transitions, output_file=None):
    """
    Plot energy analysis with neighborhoods and transitions
    
    Args:
        y: audio signal
        sr: sample rate
        beat_times: beat timestamps
        classified_segments: classified beat segments
        neighborhoods: energy neighborhoods
        transitions: significant transitions
        output_file: optional file name to save plot
    """
    # Create figure with subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
    
    # Calculate time axis for audio waveform
    time_axis = np.linspace(0, len(y) / sr, len(y))
    
    # Plot 1: Waveform with neighborhoods
    ax1.plot(time_axis, y, alpha=0.3, color='gray', linewidth=0.5)
    ax1.set_ylabel('Amplitude')
    ax1.set_title('Audio Waveform with Energy Neighborhoods')
    
    # Add neighborhood background colors
    for neighborhood in neighborhoods:
        color = 'red' if neighborhood['classification'] == 'HIGH_ENERGY' else 'blue'
        alpha = 0.2
        ax1.axvspan(neighborhood['start_time'], neighborhood['end_time'], 
                   color=color, alpha=alpha, 
                   label=f"N{neighborhood['neighborhood_id']} ({neighborhood['classification']})")
    
    # Add beat markers
    ax1.vlines(beat_times, ymin=np.min(y), ymax=np.max(y), 
              colors='black', alpha=0.1, linewidth=0.5)
    
    # Plot 2: Energy levels over time
    segment_times = [seg['start_time'] for seg in classified_segments]
    segment_energies = [seg['energy'] for seg in classified_segments]
    
    # Color code by classification
    high_energy_mask = [seg['classification'] == 'HIGH_ENERGY' for seg in classified_segments]
    low_energy_mask = [seg['classification'] == 'LOW_ENERGY' for seg in classified_segments]
    
    ax2.scatter([t for i, t in enumerate(segment_times) if high_energy_mask[i]], 
               [e for i, e in enumerate(segment_energies) if high_energy_mask[i]], 
               c='red', alpha=0.6, s=10, label='High Energy')
    ax2.scatter([t for i, t in enumerate(segment_times) if low_energy_mask[i]], 
               [e for i, e in enumerate(segment_energies) if low_energy_mask[i]], 
               c='blue', alpha=0.6, s=10, label='Low Energy')
    
    # Add energy trend line
    ax2.plot(segment_times, segment_energies, color='black', alpha=0.3, linewidth=1)
    
    # Mark transitions
    for transition in transitions:
        color = 'orange' if transition['transition_type'] == 'SPIKE' else 'purple'
        ax2.axvline(transition['time'], color=color, linestyle='--', alpha=0.8, linewidth=2)
        ax2.annotate(f"{transition['musical_transition']}\n{transition['relative_change']:+.1%}", 
                    xy=(transition['time'], transition['current_energy']),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.7),
                    fontsize=8, ha='left')
    
    ax2.set_ylabel('Energy Level')
    ax2.set_title('Beat-by-Beat Energy Analysis with Transitions')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Neighborhood timeline
    for i, neighborhood in enumerate(neighborhoods):
        y_pos = i % 2  # Alternate positions
        color = 'red' if neighborhood['classification'] == 'HIGH_ENERGY' else 'blue'
        
        # Draw neighborhood bar
        rect = patches.Rectangle((neighborhood['start_time'], y_pos - 0.1), 
                               neighborhood['duration'], 0.2,
                               facecolor=color, alpha=0.6, edgecolor='black')
        ax3.add_patch(rect)
        
        # Add neighborhood label
        ax3.text(neighborhood['start_time'] + neighborhood['duration']/2, y_pos,
                f"N{neighborhood['neighborhood_id']}\n{neighborhood['duration']:.1f}s",
                ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Mark transitions on timeline
    for transition in transitions:
        ax3.axvline(transition['time'], color='orange' if transition['transition_type'] == 'SPIKE' else 'purple', 
                   linestyle='--', alpha=0.8, linewidth=2)
    
    ax3.set_xlim(0, max([n['end_time'] for n in neighborhoods]) if neighborhoods else len(y)/sr)
    ax3.set_ylim(-0.5, 1.5)
    ax3.set_ylabel('Neighborhoods')
    ax3.set_xlabel('Time (seconds)')
    ax3.set_title('Song Structure Timeline')
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(['Even', 'Odd'])
    ax3.grid(True, alpha=0.3)
    
    # Add legend for transitions
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='orange', linestyle='--', label='Energy Spike (Verse→Chorus)'),
        Line2D([0], [0], color='purple', linestyle='--', label='Energy Fall (Chorus→Verse)')
    ]
    ax3.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    
    # Save plot if filename provided
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved as {output_file}")
    
    plt.show()

def save_complete_analysis(neighborhoods, stats, transitions, classified_segments, output_file='complete_energy_analysis_miserybusiness.txt'):
    """Save complete analysis including neighborhoods, transitions, and beat-level features"""
    import pandas as pd
    
    start_and_end_times = {}
    
    # Save summary analysis to text file
    with open(output_file, 'w') as f:
        f.write("=== COMPLETE ENERGY ANALYSIS ===\n\n")
        
        # Neighborhood analysis
        f.write("ENERGY NEIGHBORHOODS (Song Structure):\n")
        f.write(f"Total neighborhoods: {stats['total_neighborhoods']}\n")
        f.write(f"High energy neighborhoods: {stats['high_energy_count']}\n")
        f.write(f"Low energy neighborhoods: {stats['low_energy_count']}\n")
        f.write(f"Average high energy duration: {stats['avg_high_energy_duration']:.2f}s\n")
        f.write(f"Average low energy duration: {stats['avg_low_energy_duration']:.2f}s\n\n")
        
        for neighborhood in neighborhoods:
            f.write(f"Neighborhood {neighborhood['neighborhood_id']}: "
                   f"{neighborhood['classification']} "
                   f"({neighborhood['start_time']:.2f}s - {neighborhood['end_time']:.2f}s) "
                   f"Duration: {neighborhood['duration']:.2f}s, "
                   f"Avg Energy: {neighborhood['avg_energy']:.3f}\n")
            start_and_end_times[neighborhood['neighborhood_id']] = (neighborhood['start_time'], neighborhood['end_time'])
        
        # Transition analysis  
        f.write(f"\n\nENERGY TRANSITIONS (Verse/Chorus Changes):\n")
        f.write(f"Total significant transitions: {len(transitions)}\n\n")
        
        if transitions:
            for i, transition in enumerate(transitions, 1):
                f.write(f"Transition {i}: {transition['description']}\n")
                f.write(f"  Time: {transition['time']:.2f}s (Beat {transition['beat_number']})\n")
                f.write(f"  Type: {transition['musical_transition']}\n")
                f.write(f"  Energy change: {transition['energy_change']:.3f} ({transition['relative_change']:.1%})\n")
                f.write(f"  Current energy: {transition['current_energy']:.3f}\n")
                f.write(f"  Baseline energy: {transition['baseline_energy']:.3f}\n\n")
        else:
            f.write("No significant energy transitions detected.\n")
            f.write("Try lowering the spike_threshold parameter.\n")
        
        # Additional statistics for the beat-level features
        f.write(f"\n\nBEAT-LEVEL FEATURE STATISTICS:\n")
        all_rms = [seg['rms'] for seg in classified_segments]
        all_centroids = [seg['centroid'] for seg in classified_segments]
        all_zcr = [seg['zcr'] for seg in classified_segments]
        
        f.write(f"RMS Energy:\n")
        f.write(f"  Mean: {np.mean(all_rms):.6f}\n")
        f.write(f"  Std:  {np.std(all_rms):.6f}\n")
        f.write(f"  Min:  {np.min(all_rms):.6f}\n")
        f.write(f"  Max:  {np.max(all_rms):.6f}\n\n")
        
        f.write(f"Spectral Centroid:\n")
        f.write(f"  Mean: {np.mean(all_centroids):.2f} Hz\n")
        f.write(f"  Std:  {np.std(all_centroids):.2f} Hz\n")
        f.write(f"  Min:  {np.min(all_centroids):.2f} Hz\n")
        f.write(f"  Max:  {np.max(all_centroids):.2f} Hz\n\n")
        
        f.write(f"Zero Crossing Rate:\n")
        f.write(f"  Mean: {np.mean(all_zcr):.6f}\n")
        f.write(f"  Std:  {np.std(all_zcr):.6f}\n")
        f.write(f"  Min:  {np.min(all_zcr):.6f}\n")
        f.write(f"  Max:  {np.max(all_zcr):.6f}\n\n")
        
        f.write(f"Beat-by-beat data saved to: {output_file.replace('.txt', '_beats.csv')}\n")
    
    # Save beat-by-beat analysis to CSV file
    csv_file = output_file.replace('.txt', '_beats.csv')
    
    # Prepare beat data for CSV
    beat_data = []
    for segment in classified_segments:
        duration = segment['end_time'] - segment['start_time']
        beat_data.append({
            'beat_number': segment['beat_number'],
            'start_time': round(segment['start_time'], 3),
            'end_time': round(segment['end_time'], 3),
            'duration': round(duration, 3),
            'energy': round(segment['energy'], 6),
            'classification': segment['classification'],
            'rms': round(segment['rms'], 8),
            'centroid': round(segment['centroid'], 2),
            'zcr': round(segment['zcr'], 8)
        })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(beat_data)
    df.to_csv(csv_file, index=False)
    
    print(f"Summary analysis saved to {output_file}")
    print(f"Beat-by-beat data saved to {csv_file}")
    print(f"Total beats analyzed: {len(classified_segments)}")
    print(start_and_end_times)
    return start_and_end_times

# Modified main function with transition detection
def main_with_neighborhoods(audio_file):
    timestamps = {}
    try:
        # Existing analysis
        beat_times, tempo, beat_frames, y, sr = detect_beats(audio_file[:-4].lower()+"_paramore_drums.wav")
        segments = analyze_beat_energy(y, sr, beat_times)
        classified_segments = classify_beat_segments(segments)
        
        # Neighborhood analysis for song structure
        neighborhoods = identify_energy_neighborhoods(classified_segments, hysteresis_factor=0.01, min_section_duration=2)
        stats, high_neighborhoods, low_neighborhoods = analyze_neighborhood_patterns(neighborhoods)
        
        # NEW: Transition detection for verse/chorus changes
        raw_transitions = detect_energy_transitions(classified_segments, 
                                                   spike_threshold=0.25, 
                                                   lookback_window=4)
        significant_transitions = refine_transitions(raw_transitions, min_time_gap=8.0)
        
        # Save analysis with beat-level features
        timestamps = save_complete_analysis(neighborhoods, stats, significant_transitions, classified_segments, audio_file[:-4]+'_paramore_drums.txt')
        
    except FileNotFoundError:
        print(f"Error: File '{audio_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")
    return neighborhoods, stats, significant_transitions, timestamps


if __name__ == "__main__":
    neighborhoods, stats, transitions, timestamps = main_with_neighborhoods('miserybusiness.wav')
    print(type(neighborhoods[0]))
