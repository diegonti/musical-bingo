# Musical Bingo: Card Generation

This Python script allows for an automatic generation of bingo cards for Musical Bingo (Normal bingo but with songs). You must supply the song list and images (optional), and specify some fromat in the input file (otherwhise it will take the default values).

There is a web app version of this project in this [repository](https://github.com/diegonti/musical-bingo-app) and deployed in this [link](http://musicalbingodoc.pythonanywhere.com/).

# Usage

To use it simply fill the input file with the desired parameters and values and run the main program as:

```
$ python3 musical_bingo.py input.txt
```

Here is an example of [input](./input.txt) file, with the possible parameters and their default values. The coments are set with thr ! character:

```
NROWS = 3                   ! Number of rows in card [Defaults to 3]
NCOLS = 9                   ! Number of columns in card [Defaults to 10]

N_PLAYERS = 10              ! Number of bingo players [Defults to 10]
N_SONGS_CARD = 12           ! Number of songs per bingo card [Defaults to 15]
N_IMAGES_CARD = 10          ! Number of images per bingo card [Defaults to 0]

WIDTH = 16                  ! Width of bingo card (X, in pixels or aspect ratio) [Defaults to 3200]
HEIGHT = 7                  ! Height of bingo card (Y, in pixels or aspect ratio) [Defaults to 1400]
TIMES = 200                 ! Multiplier of width and height [Defaults to 1]
DPI = 600                   ! DPI of the saved images [Defaults to 600]

IMG_FOLDER = img/           ! Images folder [Defaults to "./img/"]
SONGS_FILE = songs.txt      ! Song list file, with format artist - song [Defaults to "songs.txt"]
OUTPUT_FOLDER = bills/      ! Output folder where the card images will be created [Defaults to "./bills/"]

BG_COLOUR = white                   ! Background colour of the bingo card [Defaults to white]
FILLS = (0,100,100)/ red/ #FFFFFF   ! Fill background colours of the bingo card (rounded rectangles)
EDGES = same                        ! Edge colours of the bingo card (rounded rectangles). Can be colours or "same" (same as FILLS) [Defaults to "same"]
TILE_FILL =  green                  ! Song tile fill colour 
TILE_EDGE =  black                  ! Song tile edge colour 

```

## Help

In the input.txt template there is a brief exmplanation of each parameter and the default values.

For usage help, run the command:

```
python3 musical_bingo.py -h
```

To easily export a Spotify playlist you can use [TuneMyMusic](https://www.tunemymusic.com/es/transfer). Otherwhise, make shure the format is "Author - Song", hyphen-separated. In the `test/` folder is an [example](test/song_list.txt) of song list.

For any doubts or questions, contact [Diego Ontiveros](https://github.com/diegonti) ([Mail](mailto:diegonti.doc@gmail.com)).

<br><br>
