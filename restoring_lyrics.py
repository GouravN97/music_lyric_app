import sqlite3
import pickle,time,pygame

#ADD PAUSE BUTTON
def retrieve_lyrics(file_path):
    conn=sqlite3.connect("lyricsdb2.db")
    c=conn.cursor()
    c.execute("SELECT data FROM records_pickled WHERE record_id = ? ",(file_path[:-4]+"words",))
    row=c.fetchone()
    restored={}
    if row:
        restored=pickle.loads(row[0])
    #print(restored)

    avg_gap=0.0
    avg_dur=0.0
    prev=0.0
    for i in range(len(restored)):
        avg_gap=avg_gap*i+(restored[i][1]-prev)
        avg_gap/=(i+1)
        avg_dur=avg_dur*i+(restored[i][2]-restored[i][1])
        avg_dur/=(i+1)
        prev=restored[i][2]
    return restored,avg_dur,avg_gap

def test(restored,avg_gap,avg_dur,):
    print("average gap=",avg_gap)
    print("average duration =",avg_dur)

    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load("ComeALittleCloser.wav")

    start_time=time.time()
    pygame.mixer.music.play()

    running=True
    current_index=0


    while running and pygame.mixer.music.get_busy():
        elapsed=time.time()-start_time    
        
        try:
            if  elapsed>restored[current_index][2]-avg_dur-avg_gap and elapsed>restored[current_index-1][2] :
                print(restored[current_index][0])
                current_index+=1            
        except:
            if current_index<len(restored) and elapsed>restored[current_index][2]-avg_dur-avg_gap:
                print(restored[current_index][0])
                current_index+=1
            continue
        if (current_index>=len(restored)):
            break
        
        
    while pygame.mixer.music.get_busy()==True:
        pass
    pygame.quit()

if __name__=="__main__":
    test(*retrieve_lyrics('ComeaLittleCloser.wav'))