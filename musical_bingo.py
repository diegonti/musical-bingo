"""
Simple Python program to create bingo cards for Musical Bingo.
The program works with an input file where the configuration and format of the bingo card is given.
The program takes the given songs, images and format, and creates the specified musical bingo cards
in an output folder, calculating the winner card.

A quick way to make bingo cards for a fun night with friends and family!

Diego Ontiveros - 22/12/2023
"""

from PIL import Image, ImageDraw, ImageFont, ImageChops
import textwrap

from argparse import ArgumentParser
import numpy as np
import random
import time
import shutil
import os
import ast


def text_to_image(image, text,rectangle_area,font_size=40):
    """
    Puts the given text in a certain rectangular area of an image.

    Parameters
    --------------
    `image` : PIL image object where the cards is being drawn.\n
    `text`  : String of text to add to the image.\n
    `rectangle_area` : (x1,y1,x2,y2) array with the 2 corners of a rectangle.\n
    `font_size` : Text font size. Defaults to 40.

    Returns
    -------------
    `image` : Modifyed base image with the text added.
    """

    # Create an ImageDraw object
    draw = ImageDraw.Draw(image)

    # Define the default font
    font = ImageFont.truetype("arial.ttf", font_size,encoding="unic")

    # Define the rectangle area to add text
    x1, y1, x2, y2 = rectangle_area

    # Calculate the available width and height inside the rectangle area
    available_width = x2 - x1
    available_height = y2 - y1

    # Wrap the text to fit inside the available width
    wrapped_text = textwrap.wrap(text, width=int(available_width / font_size)+6)

    # Calculate the total height of the wrapped text
    total_text_height = len(wrapped_text) * font_size

    # Calculate the position to center the wrapped text vertically within the rectangle area
    text_y = y1 + (available_height - total_text_height) // 2

    # Add the wrapped text to the image
    for line in wrapped_text:
        # Calculate the bounding box of the text line
        text_bbox = draw.textbbox((0, 0), line, font=font)

        # Calculate the position to center the text line horizontally within the rectangle area
        text_x = x1 + (available_width - (text_bbox[2] - text_bbox[0])) // 2

        # Draw the text line
        draw.text((text_x, text_y), line, fill="black", font=font)
        text_y += font_size

    # Save the image with the added text
    return image


def add_corners(im, rad=100):
    """
    Adds rounded corners to an image. Thought for user input images.
    
    `im`    : PIL Image object.
    `rad`   : Rounded border radius.
    
    """
    # Creates a image with a white circle
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)

    # Use the circle to create an alpha mask (for the corners to desappear)
    alpha = Image.new('L', im.size, "white")
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))

    # Use the mask to elimiate the corners, leaving them round
    alpha = ImageChops.darker(alpha, im.split()[-1])
    im.putalpha(alpha)

    return im


def tile_to_image(image,tile_path,rectangular_area):
    """
    Adds user image to the bingo card image, into a specified rectangle.

    `image` : PIL image object where the cards is being drawn.\n
    `tile_path` : String containing the path of the user image.\n
    `rectangle_area` : (x1,y1,x2,y2) array with the 2 corners of a rectangle.\n

    """

    tile = Image.open(tile_path).convert("RGBA")

    # Calculate the size of the rectangle area
    rectangular_area = np.array(rectangular_area).astype(int)
    insert_width = rectangular_area[2] - rectangular_area[0]
    insert_height = rectangular_area[3] - rectangular_area[1]

    # Resize the picture to fit within the specified rectangle
    resized_picture = tile.resize((int(insert_width), int(insert_height)), Image.Resampling.LANCZOS)

    resized_picture = add_corners(resized_picture,int(0.02*image.size[0]))

    # Paste the resized picture onto the main image at the specified position
    image.paste(resized_picture, tuple(rectangular_area[:2]),resized_picture)

    return image


class Rectangle:
    """Class representing a rectangular tile of the bingo card"""

    def __init__(self, xy, text, colour, edge_colour, tile_image,image, type) -> None:
        self.xy = xy
        self.type = type
        
        self.text = text
        self.colour = colour
        self.tile_image = tile_image
        self.image = image
        self.edge_colour = edge_colour
        
    def draw(self):
        """Draws rectangle to main image"""
        w,h = self.image.size
        draw = ImageDraw.Draw(self.image)
        
        if self.tile_image != "":
            tile_to_image(self.image,self.tile_image,self.xy)

        draw.rounded_rectangle(self.xy, fill=self.colour, outline=self.edge_colour,
                    width=3, radius=0.02*w)
        
        if self.text != "":
            text_to_image(self.image,self.text,self.xy)
        

class Grid:
    """Class representing the grid of the bingo card."""

    def __init__(self,image,metadata,NROWS,NCOLS) -> None:
        self.image = image
        self.metatada = metadata
        self.NROWS = NROWS
        self.NCOLS = NCOLS

        self.grid = [[''] * NCOLS for _ in range(NROWS)]
        self.grid_labels = [[''] * NCOLS for _ in range(NROWS)]

        self.positions = self.get_rect_positions()

    def set_info(self,song_list,img_list):
        self.song_list = song_list
        self.img_list = img_list
        

    def get_rect_positions(self):
        """Creates a grid of rectangle positions (x1,y1,x2,y2) for the given image and metadata of inner rectangle.

        Parameters
        ----------
        `metadata` : xy of inner rectangle
        `NCOLS` : Number of columns
        `NROWS` : Number of rows

        Returns
        -------
        `rect_positions` : List of all the xy positions for the rectangles in a grid
        """
        metadata,NROWS,NCOLS = self.metatada,self.NROWS,self.NCOLS
        
        start_x,start_y,end_x,end_y = metadata
        edge_percent = 0.005     # Percent of blank spaces on the edges
        extra_spacing = 10
        
        spacing_x = (end_x-start_x)*edge_percent
        spacing_y = (end_y-start_y)*edge_percent

        tile_w = ((end_x-start_x)-(NCOLS+extra_spacing+1)*spacing_x)/NCOLS
        tile_h = ((end_y-start_y)-(NROWS+extra_spacing+1)*spacing_y)/NROWS

        rect_positions = [[()] * NCOLS for _ in range(NROWS)]
        for i in range(NROWS):
            for j in range(NCOLS):
                x1 = start_x + (0.5*extra_spacing+1)*spacing_x + (tile_w+spacing_x)*j
                x2 = (start_x + (0.5*extra_spacing+1)*spacing_x + (tile_w+spacing_x)*(j+1)) - spacing_x
                y1 = start_y + (0.5*extra_spacing+1)*spacing_y + (tile_h+spacing_y)*i
                y2 = (start_y + (0.5*extra_spacing+1)*spacing_y + (tile_h+spacing_y)*(i+1)) - spacing_y

                rect_position = (x1,y1,x2,y2)
                rect_positions[i][j] = rect_position
                
        
        return rect_positions
        

    def fill(self, n_songs, n_img, colours):
        """Fills the grid with the different tiles."""

        bg_fills,tile_fill,tile_edge = colours

        ncols,nrows = self.NCOLS,self.NROWS
        total_cells = ncols*nrows
        n_blanks = total_cells - n_songs - n_img

        total_classes = n_songs + n_img + n_blanks

        if total_classes > total_cells:
            raise ValueError("The total number of classes exceeds the available grid cells.")

        # Calculate the number of instances of class A in each row
        songs_per_row = n_songs // nrows

        # Create a list to keep track of the row indices and shuffle it
        row_indices = list(range(nrows))
        random.shuffle(row_indices)

        # Create an empty grid to store the classes
        grid = [[''] * ncols for _ in range(nrows)]

        # Distribute class A to the grid, ensuring each row has the same number of instances
        count = 0
        for row in row_indices:
            for i in range(songs_per_row):
                col = random.randint(0, ncols - 1)
                while grid[row][col]:
                    col = random.randint(0, ncols - 1)
                 
                grid[row][col] = Rectangle(self.positions[row][col],text=self.song_list[count],colour=tile_fill,edge_colour=tile_edge,tile_image="",image=self.image,type="Song")
                self.grid_labels[row][col] = "S"
                count += 1

        # Randomly distribute class B to the grid
        for i in range(n_img):
            row, col = random.randint(0, nrows - 1), random.randint(0, ncols - 1)
            while grid[row][col]:
                row, col = random.randint(0, nrows - 1), random.randint(0, ncols - 1)
            grid[row][col] = Rectangle(self.positions[row][col],text="",colour=None,edge_colour=tile_edge,tile_image=self.img_list[i],image=self.image,type="Image")
            self.grid_labels[row][col] = "I"

        # Randomly distribute class C to the grid
        for i in range(n_blanks):
            row, col = random.randint(0, nrows - 1), random.randint(0, ncols - 1)
            while grid[row][col]:
                row, col = random.randint(0, nrows - 1), random.randint(0, ncols - 1)
            grid[row][col] = Rectangle(self.positions[row][col],text="",colour=bg_fills[-1],edge_colour=tile_edge,tile_image="",image=self.image,type="Blank")
            self.grid_labels[row][col] = "B"
        
        self.grid = grid
        return grid
    

    def log(self,mode="type"):
        """Print grid to screen"""

        if mode.lower() == "type":
            for row in self.grid_labels: print(row)
        elif mode.lower() == "object":
            for row in self.grid: print(row)
        
    
    def draw(self):
        """Draws all the rectangles in the grid."""
        w,h = self.image.size

        draw = ImageDraw.Draw(self.image)
        for row in self.grid:
            for Rect in row:
                Rect.draw()
        return self.image


def check_repeated(list,sublists,song_list,N_SONGS_BILL):
    """Check if are repeated bill cards."""
    for sl in sublists:
        if set(list) == set(sl):
            list = random.sample(song_list, N_SONGS_BILL)
            break
    return list


def generate_sublists(big_list, N, M):
    """Generates N random sampled sublists of lenght M, from a larger list of songs."""

    # Create a list to store the sublists
    sublists = []
    big_list = big_list.copy()

    # Shuffle the big list to randomize the order of elements
    random.shuffle(big_list)

    # Divide the big list into N sublists of M elements each
    for i in range(N):
        if M == 0:
            sublist = []
        else:
            sublist = random.sample(big_list, M)
            sublist = check_repeated(sublist,sublists,big_list,M)

        sublists.append(sublist)

    return sublists


def background(image:Image, fills:list, edges:list):
    """Generates background of billet onto a given PIL image with the selected list of
    fill and edge colours of rounded rectangles (from outside to inside).

    Parameters
    ----------
    `image` : PIL image
    `fills` : List of fill colours for the rounded rectangles, from outer to inner
    `edges` : List of edge colours for the rounded rectangles, from outer to inner

    Returns
    -------
    `image` : Drawn image with background
    `metadata` : Pixel data of the last (inner) rectangle position
    """

    edge_percent = 0.04     # Percent of blank spaces on the edges
    
    w,h = image.size
    draw = ImageDraw.Draw(image)

    # Draw rounded rectangles
    for i,(fill,edge) in enumerate(zip(fills,edges)):
        ep_i = edge_percent * (i+1) * 0.4
        draw.rounded_rectangle((ep_i*w, ep_i*h, (1-ep_i)*w, (1-ep_i)*h), fill=fill, outline=edge,
                            width=3, radius=edge_percent*w)
        
    metadata = np.array((ep_i*w, ep_i*h, (1-ep_i)*w, (1-ep_i)*h)).astype(int)
    return image, metadata


def read_song_file(song_file):
    """Reads and parses song file"""  
    song_list = []
    with open(song_file,"r",encoding="utf-8") as inFile: 
        for line in inFile:
            if len(line) == 0 or line == "\n": continue
            data = line.split(" - ")
            artist,song = data[0].strip(),data[1].strip()
            text = f"{artist} – {song}"
            song_list.append(text)
    return song_list


def read_input(input_file):
    """Reads and parses input file"""  
    parameters = {}
    with open(input_file,"r") as inFile: 
        for line in inFile:
            if line.strip() == "": continue
            elif line.strip().startswith("!"): continue
            key_value, comment = line.strip().split('!', 1) if '!' in line else (line.strip(), '')
            key, value = key_value.split('=', 1)
            parameters[key.strip()] = value.strip()

    return parameters


def expand_img_list(img_list, n_images_card):
    """Repeate some images if not enough present. Warns if executed."""

    if len(img_list) < n_images_card:
        print("Warning! The number of images given is less than the number of images selected per card. Some will be repeated.")
        for _ in range(n_images_card-len(img_list)):
            img_list.append(img_list[0])
    
    return img_list


def parse_fills(FILLS,EDGES):
    FILLS = FILLS.split("/")
    for i,fill in enumerate(FILLS):
        f = fill.strip()
        if f.startswith("("):
            f = ast.literal_eval(f)
        FILLS[i] = f

    if EDGES == "same": EDGES = FILLS
    else:
        EDGES = EDGES.split("/")
        for i,edge in enumerate(EDGES):
            e = edge.strip()
            if e.startswith("("):
                e = ast.literal_eval(e)
            EDGES[i] = e
    return FILLS, EDGES


def ensure_elements_present(bills, required_elements):
   
    for i,input_list in enumerate(bills):
        # Count the occurrences of required elements in the input list
        element_counts = {element: input_list.count(element) for element in required_elements}
        
        # Add missing elements with counts calculated to maintain the original list length
        for element, count in element_counts.items():
            while count < 1:
                for i, item in enumerate(input_list):
                    if item not in required_elements:
                        input_list[i] = element
                        count += 1
                        break
        bills[i] = input_list
    return bills


def get_winner(song_list,songs_per_bill,OUTPUT_FOLDER):
    print("\n")
    for i,song in enumerate(song_list):
        for j,card in enumerate(songs_per_bill):
            if song in card:
                songs_per_bill[j].remove(song)

        lens = [len(card) for card in songs_per_bill]
        if 0 in lens:
            print(lens)
            winner = lens.index(0)
            iteration = i
            win_song = song
            break

    print(f"Winner = bill{winner} at song {iteration+1} ({win_song})")
    print(lens.count(0),lens.count(1))
    with open(OUTPUT_FOLDER + "winner.txt","w") as outFile:
        outFile.write(f"Winner = bill{winner} at song {iteration+1} ({win_song})")

    return winner,iteration,win_song,lens


########################################################################################################
#########################################   MAIN PROGRAM   #############################################
########################################################################################################

to = time.time()

# Hand-put colours
# OUTER = "#84d5f5"
# INNER = "white" # #9e4ae8
# LOUTER = "#d9edfa"

SEED = random.randrange(1234567890)
random.seed(SEED)

# Parsing user arguments
parser = ArgumentParser(
    description = "Generates bingo cards for playing musical bingo. The cards have songs and images from the given lists.")
parser.add_argument("file",type=str,nargs="?",help="Input file path. (Searches for input.txt if not present)",default="input.txt")

args = parser.parse_args()
input_file = args.file

####################   READING USER INPUT   ####################
parameters = read_input(input_file)

# Card structure
NROWS, NCOLS = int(parameters.get("NROWS",3)), int(parameters.get("NCOLS",10))
N_PLAYERS = int(parameters.get("N_PLAYERS",10))
N_SONGS_CARD = int(parameters.get("N_SONGS_CARD",12))
N_IMAGES_CARD = int(parameters.get("N_IMAGES_CARD",0))

# Card image format
TIMES = int(parameters.get("TIMES",1))
WIDTH, HEIGHT = int(parameters.get("WIDTH",3200))*TIMES, int(parameters.get("HEIGHT",1400))*TIMES
DPI = int(parameters.get("DPI",600))

# Card colour format
BG_COLOUR = parameters.get("BG_COLOUR","white")
FILLS = parameters.get("FILLS","#e36fea")
EDGES = parameters.get("EDGES","same")
TILE_FILL = parameters.get("TILE_FILL","#f1b5f4")
TILE_EDGE = parameters.get("TILE_EDGE","black")

# I/O files
IMG_FOLDER = parameters.get("IMG_FOLDER","./img/")
IMG_FOLDER = IMG_FOLDER if IMG_FOLDER.endswith("/") else IMG_FOLDER + "/"

SONGS_FILE = parameters.get("SONGS_FILE","songs.txt")
OUTPUT_FOLDER = parameters.get("OUTPUT_FOLDER","./bills/")

####################   PARSING INPUT and PREPARATION   ####################

img_list = [IMG_FOLDER + img for img in os.listdir(IMG_FOLDER)]
img_list = expand_img_list(img_list,N_IMAGES_CARD)
song_list = read_song_file(SONGS_FILE)

songs_per_bill = generate_sublists(song_list, N_PLAYERS, N_SONGS_CARD)
images_per_bill = generate_sublists(img_list,N_PLAYERS,N_IMAGES_CARD)

## Uncomment this part for assuring some images appear in all cards
# required_images = ["test1.jpg","test2.jpg","test3.jpg","test4.jpg"]
# if not required_images[0].startswith(IMG_FOLDER): required_images = [IMG_FOLDER + i for i in required_images]
# if not N_IMAGES_CARD == 0: images_per_bill = ensure_elements_present(images_per_bill, required_images)

FILLS,EDGES = parse_fills(FILLS,EDGES)

# TILE_FILL = LOUTER
# FILLS = [OUTER,INNER,OUTER]
# EDGES = [OUTER,INNER,OUTER]

try: shutil.rmtree(OUTPUT_FOLDER)
except FileNotFoundError: pass

try: os.mkdir(OUTPUT_FOLDER)
except FileExistsError: pass


####################   CARD CREATION LOOP   ####################

print("Cards generated: ",flush=True, end="")
for i in range(N_PLAYERS):
    image = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOUR)

    image, metadata = background(image,FILLS,EDGES)

    song_list_i = songs_per_bill[i]
    img_list = images_per_bill[i]

    grid = Grid(image,metadata,NROWS,NCOLS)
    grid.set_info(song_list_i,img_list)
    grid.fill(N_SONGS_CARD,N_IMAGES_CARD,colours=[FILLS,TILE_FILL,TILE_EDGE])
    # grid.log()
    image = grid.draw()
    image.save(f"{OUTPUT_FOLDER}/bill{i}.png",dpi=(DPI,DPI))

    print(i+1,flush=True, end=" ")

get_winner(song_list,songs_per_bill,OUTPUT_FOLDER)
print("SEED = ",SEED)

tf = time.time()
print(f"\nProcess finished in {tf-to:.2f}s")


