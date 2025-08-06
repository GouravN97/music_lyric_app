import sqlite3
import pickle
import torch
import torchaudio
from demucs import pretrained
from demucs.apply import apply_model
from forcealign import ForceAlign

def create_dct(all_words,sentence_list):
    counter=0
    sentence_counter=0
    lyrics_dct={}
    words_dct={}
    for i in range(len(all_words)):
        words_dct[i]=(all_words[i].word, all_words[i].time_start, all_words[i].time_end)

    '''for w in words:
        print(f"{w.word}: {w.time_start:.2f}s – {w.time_end:.2f}s")
        lyrics_dct[counter]=(w.word,w.time_start,w.time_end)
        counter+=1'''

    print(len(all_words))

    for sentence in sentence_list:
        words_list=sentence.split()

        starting=words_list[0]
        ending=words_list[-1]
        print(starting+" "+ all_words[counter].word+"\n"+ending+" "+all_words[counter+len(words_list)-1].word)
        
        if (starting==all_words[counter].word.lower()) and (ending==all_words[counter+len(words_list)-1].word.lower()):
            lyrics_dct[sentence_counter]=(sentence.upper(),all_words[counter].time_start, all_words[counter+len(words_list)-1].time_end)
        else:
            print("ERROR")
        
        counter+=len(words_list)
        sentence_counter+=1   
    return lyrics_dct,words_dct

def get_lyrics(filename):
    list1=[]
    sentences=""
    with open (filename,'r') as f1:
        list1=f1.readlines()

    new_list=[]
    for l in list1:
        l=l.lower()
        if '[' in l or ']' in l:
            continue
        if len(l)==1:
            continue

        lst=[c for c in l if ord(c) in range(97,123) or ord(c)==32]
        sentence=''.join(lst)
        print(sentence)
        sentences+=(sentence+' ')
        new_list.append(sentence)
    print(new_list)
    return (sentences,new_list)

def add_to_db(file_path,lyrics_file):
    lyrics_text,sentence_list=get_lyrics(lyrics_file)
    # Load the model
    model = pretrained.get_model('htdemucs')

    # Load audio
    waveform, sr = torchaudio.load(file_path)

    # Add batch dimension: (channels, length) -> (1, channels, length)
    waveform = waveform.unsqueeze(0)

    # Separate stems
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = model.to(device)
    waveform = waveform.to(device)

    estimates = apply_model(model, waveform, device=device)

    # Extract vocals and create instrumental
    vocals = estimates[0, 3].cpu()   # Vocals are the 4th source
    instrumental = (estimates[0, 0] + estimates[0, 1] + estimates[0, 2]).cpu()  # Sum drums, bass, other

    # Save vocals and instrumental
    torchaudio.save(lyrics_file[:-4]+'_vocals.wav', vocals, sr)
    torchaudio.save(lyrics_file[:-4]+'_instrumental.wav', instrumental, sr)
    align = ForceAlign(audio_file=lyrics_file[:-4]+'_vocals.wav', transcript=lyrics_text)
    words = align.inference()

    my_dct,words_dct=create_dct(words,sentence_list)
    #print(my_dct)

    record_id1=file_path[:-4]+"sentences"
    record_id2=file_path[:-4]+"words"
    conn=sqlite3.connect("lyricsdb2.db")
    c=conn.cursor()
    blob1= pickle.dumps(my_dct)
    c.execute(
        "INSERT INTO records_pickled (record_id,data) VALUES (?,?)",
        (record_id1,blob1)
    )
    blob2=pickle.dumps(words_dct)
    c.execute(
        "INSERT INTO records_pickled (record_id,data) VALUES (?,?)",
        (record_id2,blob2)
    )

    conn.commit()
    print("INSERTED INTO DATABASE")

if __name__=="__main__":
    get_lyrics('comealittlecloser_cagetheelephant.txt')