import matplotlib.pyplot as plt
plt.style.use('bmh')

def plot_coords(coords):
    # plt.axis('off')
    # Ensures equal aspect ratio.
    plt.axes().set_aspect('equal', 'datalim')
    # zip converts a list of coordinates into 
    # lists of X and Y values, respectively.
    # Draws the plot.
    x, y = zip(*coords)
    plt.plot(x, y)
    return plt
