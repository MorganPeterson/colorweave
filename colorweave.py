import colorsys
import json
import random
import requests
import sys
import webcolors
from collections import Counter, namedtuple
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie1976, delta_e_cie1994
from colormath.color_diff import delta_e_cie2000, delta_e_cmc
from colormath.color_objects import LabColor, sRGBColor
from io import BytesIO
from math import sqrt
from operator import itemgetter, mul, attrgetter
from PIL import Image as Im
from PIL import ImageChops

if sys.version_info < (3,):
    rng = xrange
else:
    rng = range

Color = namedtuple('Color', ['value', 'prominence'])
Palette = namedtuple('Palette', 'colors bgcolor')
Point = namedtuple('Point', ('coords', 'n', 'ct'))
Cluster = namedtuple('Cluster', ('points', 'center', 'n'))
Algo = ('delta_e_cmc', 'delta_e_cie1976', 'delta_e_cie1994', 'delta_e_cie2000')

convert3To21 = {"indigo": "purple", "gold": "orange", "firebrick": "red",
                "indianred": "red", "yellow": "yellow",
                "darkolivegreen": "green", "darkseagreen": "green",
                "mediumvioletred": "pink", "mediumorchid": "purple",
                "chartreuse": "green", "mediumslateblue": "purple",
                "black": "black", "springgreen": "green", "orange": "orange",
                "lightsalmon": "red", "brown": "brown", "turquoise": "teal",
                "olivedrab": "green", "cyan": "cyan", "silver": "gray",
                "skyblue": "blue", "darkturquoise": "teal",
                "goldenrod": "brown", "darkgreen": "green",
                "darkviolet": "purple", "darkgray": "gray",
                "lightpink": "pink", "teal": "teal", "darkmagenta": "purple",
                "lightgoldenrodyellow": "yellow", "lavender": "purple",
                "yellowgreen": "green", "thistle": "purple",
                "violet": "purple", "navy": "blue", "dimgrey": "gray",
                "orchid": "purple", "blue": "blue", "ghostwhite": "white",
                "honeydew": "white", "cornflowerblue": "blue",
                "darkblue": "blue", "darkkhaki": "yellow",
                "mediumpurple": "purple", "cornsilk": "brown", "red": "red",
                "bisque": "brown", "slategray": "gray", "darkcyan": "teal",
                "khaki": "yellow", "wheat": "brown", "deepskyblue": "blue",
                "darkred": "red", "steelblue": "blue", "aliceblue": "white",
                "lightslategrey": "gray", "gainsboro": "gray",
                "mediumturquoise": "teal", "floralwhite": "white",
                "coral": "orange", "aqua": "cyan", "burlywood": "brown",
                "darksalmon": "red", "beige": "white", "azure": "white",
                "lightsteelblue": "blue", "oldlace": "white",
                "greenyellow": "green", "fuchsia": "purple",
                "lightseagreen": "teal", "mistyrose": "white",
                "sienna": "brown", "lightcoral": "red", "orangered": "orange",
                "navajowhite": "brown", "lime": "green", "palegreen": "green",
                "lightcyan": "cyan", "seashell": "white",
                "mediumspringgreen": "green", "royalblue": "blue",
                "papayawhip": "yellow", "blanchedalmond": "brown",
                "peru": "brown", "aquamarine": "cyan", "white": "white",
                "darkslategray": "gray", "lightgray": "gray", "ivory": "white",
                "dodgerblue": "blue", "lawngreen": "green",
                "chocolate": "brown", "crimson": "red", "forestgreen": "green",
                "slateblue": "purple", "olive": "green", "mintcream": "white",
                "antiquewhite": "white", "hotpink": "pink",
                "moccasin": "yellow", "limegreen": "green",
                "saddlebrown": "brown", "grey": "gray",
                "darkslateblue": "purple", "lightskyblue": "blue",
                "deeppink": "pink", "plum": "purple", "darkgoldenrod": "brown",
                "maroon": "maroon", "sandybrown": "brown", "tan": "brown",
                "magenta": "purple", "rosybrown": "brown", "pink": "pink",
                "lightblue": "blue", "palevioletred": "pink",
                "mediumseagreen": "green", "linen": "white",
                "darkorange": "orange", "powderblue": "blue",
                "seagreen": "green", "snow": "white", "mediumblue": "blue",
                "midnightblue": "blue", "paleturquoise": "cyan",
                "palegoldenrod": "yellow", "whitesmoke": "white",
                "darkorchid": "purple", "salmon": "red",
                "lemonchiffon": "yellow", "lightgreen": "green",
                "tomato": "orange", "cadetblue": "teal",
                "lightyellow": "yellow", "lavenderblush": "white",
                "purple": "purple", "mediumaquamarine": "cyan",
                "green": "green", "blueviolet": "purple",
                "peachpuff": "yellow"}


def get_rgb_dict(colors, which):
    c = {}
    css3_names = None
    web_hex_to_rgb = None
    web_rgb_to_name = webcolors.rgb_to_name

    for color in colors:
        assert color.startswith('#') and len(color) == 7
        htr = (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        try:
            cn = web_rgb_to_name(htr)
        except ValueError:
            min_colors = {}

            if css3_names is None:
                css3_names = webcolors.css3_hex_to_names.items()
                web_hex_to_rgb = webcolors.hex_to_rgb

            for key, name in css3_names:
                r_c, g_c, b_c = web_hex_to_rgb(key)
                rd = (r_c - htr[0]) * (r_c - htr[0])
                gd = (g_c - htr[1]) * (g_c - htr[1])
                bd = (b_c - htr[2]) * (b_c - htr[2])
                min_colors[(rd + gd + bd)] = name
            cn = min_colors[min(min_colors.keys())]

        if which == 'css21':
            c[color] = convert3To21[cn]
        elif which == 'css3':
            c[color] = cn
        else:
            try:
                c[convert3To21[cn]].append({cn: color})
            except KeyError:
                c[convert3To21[cn]] = [{cn: color}]
    return c


def prepare_output(colors, format):
    ''' Prepares the output determined by what format is given.
    If no format, then list of hex codes is returned '''

    if not format:
        return colors
    elif format == 'css3':
        return get_rgb_dict(colors, 'css3')
    elif format == 'css21':
        return get_rgb_dict(colors, 'css21')
    elif format == 'full':
        return get_rgb_dict(colors, 'full')

    elif format == 'fullest':
        output = {}
        output['hex'] = colors
        output['css3'] = get_rgb_dict(colors, 'css3')
        output['css21'] = get_rgb_dict(colors, 'css21')
        output['tree'] = get_rgb_dict(colors, 'fullest')
        return output


def distance(c1, c2, algo):
    ''' Calculate the visual distance between the two colors. '''
    lc1 = convert_color(sRGBColor(*c1), LabColor)
    lc2 = convert_color(sRGBColor(*c2), LabColor)
    return algo(lc1, lc2)


def extract_colors(imageData, n, format, output, algo):
    """ Determine what the major colors are in the given image. """

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    # algorithm tuning
    N_QUANTIZED = 100       # start with an adaptive palette of this size
    MIN_DISTANCE = 10.0     # min distance to consider two colors different
    MIN_PROMINENCE = 0.01   # ignore if less than this proportion of image
    MIN_SATURATION = 0.05   # ignore if not saturated enough

    if n:
        MAX_COLORS = int(n)
    else:
        MAX_COLORS = 5

    im = Im.open(imageData)

    # get point color count
    if im.mode != 'RGB':
        im = im.convert('RGB')
    im = autocrop(im, WHITE)  # assume white box
    im = im.convert('P', palette=Im.ADAPTIVE,
                    colors=N_QUANTIZED).convert('RGB')
    data = im.getdata()
    dist = Counter(data)
    n_pixels = mul(*im.size)

    # aggregate colors
    to_canonical = {WHITE: WHITE, BLACK: BLACK}
    aggregated = Counter({WHITE: 0, BLACK: 0})
    sorted_cols = sorted(dist.items(), key=itemgetter(1), reverse=True)
    for c, n in sorted_cols:
        if c in aggregated:
            # exact match!
            aggregated[c] += n
        else:
            d, nearest = min((distance(c, alt, algo), alt) for alt in aggregated)
            if d < MIN_DISTANCE:
                # nearby match
                aggregated[nearest] += n
                to_canonical[c] = nearest
            else:
                # no nearby match
                aggregated[c] = n
                to_canonical[c] = c

    # order by prominence
    colors = sorted((Color(c, n / float(n_pixels))
                    for (c, n) in aggregated.items()),
                    key=attrgetter('prominence'),
                    reverse=True)

    colors, bg_color = detect_background(im, colors, to_canonical)

    # keep any color which meets the minimum saturation
    sat_colors = [c for c in colors if meets_min_saturation(c, MIN_SATURATION)]
    if bg_color and not meets_min_saturation(bg_color, MIN_SATURATION):
        bg_color = None
    if sat_colors:
        colors = sat_colors
    else:
        # keep at least one color
        colors = colors[:1]

    # keep any color within 10% of the majority color
    colors = [c for c in colors
              if c.prominence >=
              colors[0].prominence * MIN_PROMINENCE][:MAX_COLORS]

    final_colors_hex = [('#%.02x%.02x%.02x' % color[0]) for color in colors]
    if output == 'json':
        return json.dumps(prepare_output(final_colors_hex, format), indent=4)
    else:
        return prepare_output(final_colors_hex, format)


def norm_color(c):
    r, g, b = c
    return (r / 255.0, g / 255.0, b / 255.0)


def detect_background(im, colors, to_canonical):
    BACKGROUND_PROMINENCE = 0.5
    # more then half the image means background
    if colors[0].prominence >= BACKGROUND_PROMINENCE:
        return colors[1:], colors[0]

    # work out the background color
    w, h = im.size
    points = [(0, 0), (0, h / 2), (0, h - 1), (w / 2, h - 1), (w - 1, h - 1),
              (w - 1, h / 2), (w - 1, 0), (w / 2, 0)]
    edge_dist = Counter(im.getpixel(p) for p in points)

    (majority_col, majority_count), = edge_dist.most_common(1)
    if majority_count >= 3:
        # we have a background color
        canonical_bg = to_canonical[majority_col]
        bg_color, = [c for c in colors if c.value == canonical_bg]
        colors = [c for c in colors if c.value != canonical_bg]
    else:
        # no background color
        bg_color = None

    return colors, bg_color


def meets_min_saturation(c, threshold):
    return colorsys.rgb_to_hsv(*norm_color(c.value))[1] > threshold


def autocrop(im, bgcolor):
    ''' Crop away a border of the given background color.'''

    if im.mode != "RGB":
        im = im.convert("RGB")

    bg = Im.new("RGB", im.size, bgcolor)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()

    if bbox:
        return im.crop(bbox)

    return im  # no contents, don't crop to nothing


# convert RGB to Hex
def rtoh(rgb):
    return '#{}'.format(''.join(('%02x' % p for p in rgb)))


def colorz(imageData, n, format, output):
    ''' Main function to find the color palette using k-means
    clustering method. '''

    img = Im.open(imageData)
    img.thumbnail((200, 200))  # Resize the image for faster processing
    w, h = img.size

    if n:
        n = int(n)
    else:
        n = 5

    # get all points in the image
    points = [Point(color, 3, count) for count, color in img.getcolors(w * h)]

    """ Find the clusters in an image, given n number of clusters and
    difference among the clusters """
    clusters = kmeans(points, n, 10)
    rgbs = [map(int, c.center.coords) for c in clusters]

    # Get the colors
    final_colors_hex = [x for x in map(rtoh, rgbs)]

    # Produce the output
    if output == 'json':
        return json.dumps(prepare_output(final_colors_hex, format), indent=4)
    else:
        return prepare_output(final_colors_hex, format)


def euclidean(p1, p2):
    ''' Get the euclidean distance between two points. '''
    return sqrt(sum([
        ((p1.coords[i] - p2.coords[i]) * (p1.coords[i] - p2.coords[i])) for i in rng(p1.n)
    ]))


def calculate_center(points, n):
    vals = [0.0 for i in rng(n)]
    plen = 0
    for p in points:
        plen += p.ct
        for i in rng(n):
            vals[i] += (p.coords[i] * p.ct)
    return Point([(v / plen) for v in vals], n, 1)


def kmeans(points, k, min_diff):
    ''' Method to perform k-means clustering on the image
    points with k-clusters. '''
    rs = random.sample
    # Form the clusters given k
    clusters = [Cluster([p], p, p.n) for p in rs(points, k)]

    while 1:
        plists = [[] for i in rng(k)]

        for p in points:
            smallest_distance = float('Inf')
            for i in rng(k):
                distance = euclidean(p, clusters[i].center)
                if distance < smallest_distance:
                    smallest_distance = distance
                    idx = i
            plists[idx].append(p)

        diff = 0
        for i in rng(k):
            old = clusters[i]
            center = calculate_center(plists[i], old.n)
            new = Cluster(plists[i], center, old.n)
            clusters[i] = new
            diff = max(diff, euclidean(old.center, new.center))

        if diff < min_diff:
            break
    # Return all the clusters
    return clusters


def palette(**kwargs):
    # Parse all the options
    url = kwargs.get('url', '')
    n = kwargs.get('n', '')
    path = kwargs.get('path', '')
    mode = kwargs.get('mode', '')
    format = kwargs.get('format', '')
    output = kwargs.get('output', '')
    a = kwargs.get('algo', 'delta_e_cie2000')

    if a in Algo:
        if a is 'delta_e_cmc':
            a = delta_e_cmc
        elif a is 'delta_e_cie1976':
            a = delta_e_cie1976
        elif a is 'delta_e_cie1994':
            a = delta_e_cie1994
        else:
            a = delta_e_cie2000
    else:
        print('Not a vaild algorithm!')
        return []

    # If the image is given as a URL
    if url:
        imageFile = requests.get(url)
        imageData = BytesIO(imageFile.content)
        if not mode:
            return extract_colors(imageData, n, format, output, a)
        elif mode.lower() == 'kmeans' or mode.lower() == 'k-means':
            return colorz(imageData, n, format, output)
    # If image is given as a local file path
    elif path:
        if not mode:
            return extract_colors(path, n, format, output, a)
        elif mode.lower() == 'kmeans' or mode.lower() == 'k-means':
            return colorz(path, n, format, output)
    # Unknown format of image
    else:
        print("Unable to get image. Exiting.")
        sys.exit(0)
