from forcealign import ForceAlign
import pickle
def create_dct(words):
    counter=0
    lyrics_dct={}
    for w in words:
        #print(f"{w.word}: {w.time_start:.2f}s – {w.time_end:.2f}s")
        lyrics_dct[counter]=(w.word,w.time_start,w.time_end)
        counter+=1
    return lyrics_dct

lyrics_text="Im a scary gargoyle on a tower that you made with plastic power Your rhinestone eyes are like factories far away When the paralytic dreams that we all seem to keep Drive on engines tiLl they weep With future pixels in factories far away So call the mainland from the beach All parties now washed up in bleach The waves are rising for this time of year And nobody knows what to do with the heat Under sunshine pylons, we'll meet While rain is falling like rhinestones from the sky I got a feeling now my heart is frozen All the verses and the corrosion Have been after native in my soul I prayed on the unmovable Yeah, clinging to the atoms of rock Seasons, the adjustments Times have changed I can't see now, she said, 'Taxi' Now that light is so I can take This storm brings strange loyalties and skies I'm a scary gargoyle on a tower That you made with plastic power Your rhinestone eyes are like factories far away Here we go again That's electric That's electric Helicopters fly over the beach Same time every day, same routine A clear target in the summer when skies are blue It's part of the noise when winter comes It reverberates in my lungs Nature's corrupted in factories far away Here we go again That's electric Your love's like rhinestones falling from the sky That's electric With future pixels in factories far away Here we go again That's electric Your love's like rhinestones falling from the sky That's electric With future pixels in factories far away Here we go again"
lyrics_text="Theyre gonna clean up your looks With all the lies in the books To make a citizen out of you Because they sleep with a gun And keep an eye on you son So they can watch all the things you do Because the drugs never work Theyre gonna give you a smirk Cause they got methods of keeping you clean Theyre gonna rip up your heads Your aspirations to shreds Another cog in the murder machine They said All teenagers scare the livin shit out of me They could care less as long as someonell bleed So darken your clothes or strike a violent pose Maybe theyll leave you alone but not me The boys and girls in the clique The awful names that they stick Youre never gonna fit in much kid But if you're troubled and hurt What you got under your shirt Will make them pay for the things that they did They said All teenagers scare the livin shit out of me They could care less as long as someonell bleed So darken your clothes or strike a violent pose Maybe theyll leave you alone, but not me Oh yeah They said, All teenagers scare the livin shit out of me They could care less as long as someonell bleed So darken your clothes, or strike a violent pose Maybe theyll leave you alone, but not me All together now Teenagers scare the livin shit out of me They could care less as long as someonell bleed So darken your clothes, or strike a violent pose Maybe theyll leave you alone, but not me Teenagers scare the livin shit out of me They could care less as long as someonell bleed So darken your clothes, or strike a violent pose Maybe theyll leave you alone, but not me"
align = ForceAlign(audio_file='vocals0.wav', transcript=lyrics_text)
words = align.inference()

dct=create_dct(words)
with open("lyrics.dat","wb") as lyric_file:
    pickle.dump(dct,lyric_file)

lyric_file.close()