import time,pygame,pickle

with open('lyrics.dat','rb') as lyric_file:
    lyrics_dct=pickle.load(lyric_file)

pygame.init()
pygame.mixer.init()
pygame.mixer.music.load("input.wav")

start_time=time.time()
pygame.mixer.music.play()

running=True
current_index=0
avg=0.0;

while running and pygame.mixer.music.get_busy():
    elapsed=time.time()-start_time    
    if elapsed>=lyrics_dct[current_index][1]:
        try:
            print(lyrics_dct[current_index][0])
            current_index+=1
            avg=(avg*current_index+lyrics_dct[current_index][2]-lyrics_dct[current_index][1])/(current_index+1)
        except:
            break
    
    
while pygame.mixer.music.get_busy()==True:
    pass
pygame.quit()
print(avg)