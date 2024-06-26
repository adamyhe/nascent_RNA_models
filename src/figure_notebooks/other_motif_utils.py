import numpy as np
import pandas as pd
import logomaker

BACKGROUND_FREQS = np.array([0.25] * 4)

def compute_per_position_ic(ppm, background=BACKGROUND_FREQS, pseudocount=0.001):
    alphabet_len = len(background)
    
    ppm_with_pseudocount = (ppm+pseudocount)/(1 + pseudocount*alphabet_len)
    ppm_logodds = np.log(ppm_with_pseudocount) * ppm / np.log(2)
    background_logodds = np.log(background) * background / np.log(2)
    ic = (ppm_logodds - background_logodds[None,:])
    return np.sum(ic, axis=1)


def trim_motif_by_thresh(pfm, trim_threshold=0.3, pad=2):
    trim_thresh = np.max(pfm) * trim_threshold
    pass_inds = np.where(pfm >= trim_thresh)[0]

    start = max(np.min(pass_inds) - pad, 0)
    end = min(np.max(pass_inds) + pad + 1, len(pfm) + 1)
    
    return pfm[start:end]


def trim_two_motifs_by_thresh(motif1, motif2, trim_threshold=0.3, pad=2):
    # goal: delete
    motif1_trim_thresh = np.max(motif1) * trim_threshold
    motif1_pass_inds = np.where(motif1 >= motif1_trim_thresh)[0]

    motif1_start = max(np.min(motif1_pass_inds) - pad, 0)
    motif1_end = min(np.max(motif1_pass_inds) + pad + 1, len(motif1) + 1)
    
    motif2_trim_thresh = np.max(motif2) * trim_threshold
    motif2_pass_inds = np.where(motif2 >= motif2_trim_thresh)[0]

    motif2_start = max(np.min(motif2_pass_inds) - pad, 0)
    motif2_end = min(np.max(motif2_pass_inds) + pad + 1, len(motif2) + 1)
    
    start = min(motif1_start, motif2_start)
    end = max(motif1_end, motif2_end)
    
    return motif1[start:end], motif2[start:end]


def trim_motifs_by_same_thresh(motifs, trim_threshold=0.3, pad=2):
    # This function trims a set of motifs consistently,
    # calculating potential trim start and end positions
    # for each motif according to the threshold and then
    # applying the outermost trim start and end positions
    # uniformly to all the motifs. This way, they line up
    # when you plot the motifs vertically.
    
    starts = []
    ends = []
    for motif in motifs:
        # calculate threshold as fraction of tallest base's count/frac/score
        trim_thresh = np.max(motif) * trim_threshold
        # determine which bases pass the threshold
        pass_inds = np.where(motif >= trim_thresh)[0]
        
        # start = earliest/leftmost base passing threshold, and then pad
        # max --> don't go over the edge of the motif
        start = max(np.min(pass_inds) - pad, 0)
        
        # end = last/rightmost base passing threshold, and then pad
        # + 1 is because python indexing at the end will be right-exclusive
        # min --> don't go over the edge of the motif
        end = min(np.max(pass_inds) + pad + 1, len(motif) + 1)
        
        starts.append(start)
        ends.append(end)
    
    # take the leftmost start across all motifs as the start to use
    start = min(*starts)
    
    # take the rightmost end across all motifs as the end to use
    end = max(*ends)
    
    # trim each motif with the same start and end
    trimmed_motifs = [motif[start:end] for motif in motifs]
    
    return trimmed_motifs


def trim_motif_by_ic(ppm, seq, target_len=25):
    # frankensteined together from how the original modisco hit caller trims
    per_pos_ic = compute_per_position_ic(seq)
    
    best_i = -1
    best_sum = 0
    for i in range(ppm.shape[0] - target_len + 1):
        new_sum = np.sum(per_pos_ic[i : i + target_len])
        if new_sum > best_sum:
            best_sum = new_sum
            best_i = i

    return ppm[best_i:best_i + target_len]


def plot_motif_on_ax(array, ax):
    assert len(array.shape) == 2 and array.shape[-1] == 4, array.shape
    # reformat pwm to what logomaker expects
    df = pd.DataFrame(array, columns=['A', 'C', 'G', 'T'])
    df.index.name = 'pos'

    # plot motif ("baseline_width=0" removes the y=0 line)
    crp_logo = logomaker.Logo(df, ax=ax, font_name='Arial Rounded', baseline_width=0)
    
    # fix appearance to be less terrible
    crp_logo.style_spines(visible=False)
    ax.set_ylim(min(df.sum(axis=1).min(), 0), df.sum(axis=1).max())
    ax.set_xticks([])
    ax.set_yticks([])
    
    return crp_logo
    
    
