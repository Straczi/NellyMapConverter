import numpy as np
import sys

VALUE_UNSCANNED = 205
VALUE_INDOOR = 254
VALUE_BORDER = 0
VALUE_OUTDOOR = 128

def load_pgm_to_array(filename):
    with open(filename, 'rb') as f:
        # Read magic number (P5)
        magic = f.readline().strip()
        if magic != b'P5':
            raise ValueError("Not a valid PGM (P5) file")

        # Read header (skip comments)
        width = height = maxval = None
        while True:
            line = f.readline()
            if line.startswith(b'#'):
                continue
            else:
                parts = line.strip().split()
                if width is None:
                    width, height = map(int, parts)
                else:
                    maxval = int(parts[0])
                    break

        # Read pixel data
        img = np.frombuffer(f.read(), dtype='u1' if maxval < 256 else '>u2')
        img = img.reshape((height, width))
        return img.copy()
    
def map_outside(array, x, y):
    if array[x, y] == VALUE_UNSCANNED:
        array[x, y] = VALUE_OUTDOOR
    if x > 0 and array[x - 1, y] == VALUE_UNSCANNED:
            map_outside(array, x - 1, y)
    if x < array.shape[0] - 1 and array[x + 1, y] == VALUE_UNSCANNED:
            map_outside(array, x + 1, y)
    if y > 0 and array[x, y - 1] == VALUE_UNSCANNED:
            map_outside(array, x, y - 1)
    if y < array.shape[1] - 1 and array[x, y + 1] == VALUE_UNSCANNED:
            map_outside(array, x, y + 1)

def mark_outdoors(array):
    for i in range(array.shape[0]):
        if array[i, 0] == VALUE_UNSCANNED:
            map_outside(array, i, 0)
        if array[i, 0] == VALUE_INDOOR:
            new_array = np.full((array.shape[0], array.shape[1] + 1), VALUE_OUTDOOR, dtype=array.dtype)
            new_array[:, -array.shape[1]:] = array
            array = new_array

    for i in range(array.shape[0]):
        if array[i, array.shape[1] - 1] == VALUE_UNSCANNED:
            map_outside(array, i, array.shape[1] - 1)
        if array[i, array.shape[1] - 1] == VALUE_INDOOR:
            new_array = np.full((array.shape[0], array.shape[1] + 1), VALUE_OUTDOOR, dtype=array.dtype)
            new_array[:, :-1] = array
            array = new_array

    for i in range(array.shape[1]):
        if array[0, i] == VALUE_UNSCANNED:
            map_outside(array, 0, i)
        if array[0, i] == VALUE_INDOOR:
            new_array = np.full((array.shape[0] + 1, array.shape[1]), VALUE_OUTDOOR, dtype=array.dtype)
            new_array[1:, :] = array
            array = new_array

    for i in range(array.shape[1]):
        if array[array.shape[0] - 1, i] == VALUE_UNSCANNED:
            map_outside(array, array.shape[0] - 1, i)
        if array[array.shape[0] - 1, i] == VALUE_INDOOR:
            new_array = np.full((array.shape[0] + 1, array.shape[1]), VALUE_OUTDOOR, dtype=array.dtype)
            new_array[:-1, :] = array
            array = new_array
    return array

def insert_walls(array):
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            turn_to_border_if_facing_indoors(array, i, j)
    return array

def turn_to_border_if_facing_indoors(array, x, y):
    if array[x, y] != VALUE_OUTDOOR:
        return
    if x > 0 and array[x - 1, y] == VALUE_INDOOR:
            array[x,y] = VALUE_BORDER
    if x < array.shape[0] - 1 and array[x + 1, y] == VALUE_INDOOR:
            array[x,y] = VALUE_BORDER
    if y > 0 and array[x, y - 1] == VALUE_INDOOR:
            array[x,y] = VALUE_BORDER
    if y < array.shape[1] - 1 and array[x, y + 1] == VALUE_INDOOR:
            array[x,y] = VALUE_BORDER

def save_array_to_pgm(array):
    with open('map_out.pgm', 'wb') as f:
        f.write(b'P5\n')
        f.write(f'{array.shape[1]} {array.shape[0]}\n'.encode())
        f.write(b'255\n')
        f.write(array.astype(np.uint8).tobytes())

def turn_outdoor_back_to_unscanned(array):
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            if array[i, j] == VALUE_OUTDOOR:
                array[i, j] = VALUE_UNSCANNED
    return array

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_pgm_file>")
        sys.exit(1)
    file_location = sys.argv[1]
    array = load_pgm_to_array(file_location)
    array = mark_outdoors(array)
    array = insert_walls(array)
    array = turn_outdoor_back_to_unscanned(array)
    save_array_to_pgm(array)
    print("Map processing complete. Output saved to map_out.pgm.")