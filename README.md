# music_lyric_app

This program , given the title and artist of any english* song, automatically creates a lyric video out of it, displaying each word when it is sung. The entire project is done in python.

1.Download the song into your working directory as a .wav file in the format <title>_<artist>.wav where the title and artist names have no caps, spaces or other special characters.
E.g., blindinglights_theweeknd.wav , 

2. Open genius4.py .Give the song name and the artist. The Genius API is used to fetch the lyrics of the song, and click on "CREATE LYRIC VIDEO"

3. The lyrics are parsed, word by word, and also sentence by sentence. This is so that the program knows when each sentence starts and ends.
   
4. The vocals of the song get separated from the rest of the instruments using the demucs python library.

5. Now each word is "aligned" to the exact time at which it is sung, using the ForceAlign library.

6. This data gets stored in a dictionary in the format {<chronological order no> : (word, start_time, end_time)}
   
7. A similar dictionary is created for the sentences.

8. Using the spotify and wikipedia api s , we fetch a bunch of images related to the song chosen.

9. The background effects in the final video are created using moviepy. The text is displayed using PIL.

10. Changes in the song are pinpointed using the librosa library.It can be used to detect beats accurately. That way we can change each background effect exactly on that beat, and not out of sync.

11. The librosa library is used to analyse the audio of the song and calculate the amplitude, frequency, etc and ultimately calculate the "energy" of each beat. This energy is visually saved as a graph in matplotlib.

12. So by calculating the energy of each beat, if we calculate the median and mean, we see that the parts above the mean always are in the chorus and parts below it are usually verses.
13. Therefore we have classified each lyric according to its "intensity".
14. Depending upon the intensity we 
   
