from mido import MidiFile,MidiTrack,Message
import numpy as np
import os
import util

samples_per_measure=96
num_notes=96

i=0



def check_file_validity(filename,samples_per_measure=96):
    has_time_sig = False
    flag_warning = False
    mid = MidiFile(filename)
    ticks_per_beat = mid.ticks_per_beat
    ticks_per_measure = 4 * ticks_per_beat
    #print('filename:',filename)
    #print("ticks_per_beat:",ticks_per_beat)
    #print("ticks_per_sample:",ticks_per_measure/samples_per_measure)
    for i, track in enumerate(mid.tracks):
        for msg in track:
            if msg.type == 'time_signature':
                new_tpm = msg.numerator * ticks_per_beat * 4 / msg.denominator
                if has_time_sig and new_tpm != ticks_per_measure:
                    flag_warning = True
                ticks_per_measure = new_tpm
                has_time_sig = True
    if flag_warning:
        print("filename:",filename)
        print ("  ^^^^^^ WARNING ^^^^^^")
        print ("    " + filename)
        print ("    Detected multiple distinct time signatures.")
        print ("  ^^^^^^ WARNING ^^^^^^")
        return False
       
    else:
        return True
        




def midi_to_samples(filename,samples_per_measure=96,num_notes=96):

    
    mid = MidiFile(filename)
    ticks_per_measure=4*mid.ticks_per_beat
    all_notes = {}
    for i, track in enumerate(mid.tracks):
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type == 'note_on':
                if msg.velocity == 0:
                    continue
                note = msg.note - (128 - num_notes)/2
                assert(note >= 0 and note < num_notes)
                if note not in all_notes:
                    all_notes[note] = []
                else:
                    single_note = all_notes[note][-1]
                    if len(single_note) == 1:
                        single_note.append(single_note[0] + 1)
                all_notes[note].append([abs_time * samples_per_measure / ticks_per_measure])
            elif msg.type == 'note_off':
                if len(all_notes[note][-1]) != 1:
                    continue
                all_notes[note][-1].append(abs_time * samples_per_measure / ticks_per_measure)
        
        
        
    for note in all_notes:
        for start_end in all_notes[note]:
            if len(start_end) == 1:
                start_end.append(start_end[0] + 1)
    samples=[]
    for note in all_notes:
        for start, end in all_notes[note]:
            sample_ix = int(start /samples_per_measure)
            while len(samples) <= sample_ix:
                samples.append(np.zeros((samples_per_measure, num_notes), dtype=np.uint8))
            sample = samples[sample_ix]
            start_ix = int(start - sample_ix * samples_per_measure)
            if False:
                end_ix = min(end - sample_ix * samples_per_measure, samples_per_measure)
                while start_ix < end_ix:
                    sample[start_ix, note] = 1
                    start_ix += 1
            else:
                sample[int(start_ix), int(note)] = 1
    return samples





def samples_to_midi(samples, fname, ticks_per_sample, thresh=0.5):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    ticks_per_beat = mid.ticks_per_beat
    ticks_per_measure = 4 * ticks_per_beat
    ticks_per_sample = ticks_per_measure / samples_per_measure
    abs_time = 0
    last_time = 0
    for sample in samples:
        for y in range(sample.shape[0]):
            abs_time += ticks_per_sample
            for x in range(sample.shape[1]):
                note = int(x + (128 - num_notes)/2)
                if sample[y,x] >= thresh and (y == 0 or sample[y-1,x] < thresh):
                    delta_time = int(abs_time - last_time)
                    track.append(Message('note_on', note=note, velocity=127, time=delta_time))
                    last_time = abs_time
                if sample[y,x] >= thresh and (y == sample.shape[0]-1 or sample[y+1,x] < thresh):
                    delta_time = int(abs_time - last_time)
                    track.append(Message('note_off', note=note, velocity=127, time=delta_time))
                    last_time = abs_time
    mid.save(fname)





def load_songs(directories=['dataset']):
    genre=0
    all_samples=[]
    all_lens=[]
    all_genre=[]
    for dir in directories:
        files=[dir+'/'+filename for filename in os.listdir(dir)]
            
          
        for file in files:
            path=file
            if(not check_file_validity(path)):
                continue
                
            samples=midi_to_samples(path)
          
            if len(samples)<8:
                continue
            samples,lens=util.generate_add_centered_transpose(samples)
            all_samples+=samples
            all_lens+=lens
            all_genre.append(genre)

        genre+=1
                
                
    assert(sum(all_lens) == len(all_samples))
    print ("Saving " + str(len(all_samples)) + " samples...")
    all_samples = np.array(all_samples, dtype=np.uint8)
    all_lens = np.array(all_lens, dtype=np.uint32)
    np.save('samples.npy', all_samples)
    np.save('lengths.npy', all_lens)
    np.save('genre.npy',all_genre)
    print("Done")
    




def samples_to_midi(samples, fname, ticks_per_sample, thresh=0.5):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    ticks_per_beat = mid.ticks_per_beat
    ticks_per_measure = 4 * ticks_per_beat
    ticks_per_sample = ticks_per_measure / samples_per_measure
    abs_time = 0
    last_time = 0
    for sample in samples:
        for y in range(sample.shape[0]):
            abs_time += ticks_per_sample
            for x in range(sample.shape[1]):
                note = int(x + (128 - num_notes)/2)
                if sample[y,x] >= thresh and (y == 0 or sample[y-1,x] < thresh):
                    delta_time = int(abs_time - last_time)
                    track.append(Message('note_on', note=note, velocity=127, time=delta_time))
                    last_time = abs_time
                if sample[y,x] >= thresh and (y == sample.shape[0]-1 or sample[y+1,x] < thresh):
                    delta_time = int(abs_time - last_time)
                    track.append(Message('note_off', note=note, velocity=127, time=delta_time))
                    last_time = abs_time
    mid.save(fname)







