# colorweave

Extract dominant colors from an image as a palette. Also get names of the colors extracted either using CSS3 standard or CSS2.1.

Works with Python2 and Python3.

## Installation

```python
python setup.py install
```

## Usage

Retrieve dominant colors from an image URL::

```python
from colorweave import palette
print palette(url="image_url")
```
The palette method takes the image from the URL and returns the hex codes of the dominant colors as a list.

#### Use different algorithms
Default algorithm is "delta_e_cie2000"

```python
print palette(url="http://your-url/img.jpg", algo="delta_e_cmc")

print palette(url="http://your-url/img.jpg", algo="delta_e_cie1976")

print palette(url="http://your-url/img.jpg", algo="delta_e_cie1994")

print palette(url="http://your-url/img.jpg", algo="delta_e_cie2000")
```

#### Retrive dominant colors from a local image::

```python
print palette(path="path_to_image")
```

#### Specify number of colors to be returned::

```python
print palette(url="image_url", n=6)
```

#### Return the palette as a JSON object::

```python
print palette(url="image_url", n=6, output="json")
```

#### Select different modes of output::

```python
print palette(url="image_url", n=6)
# Returns the list of dominant color hex codes

print palette(url="image_url", n=6, format="css21")
# Returns a dictionary with each dominant color mapped to its CSS21 color name

print palette(url="image_url", n=6, format="css3")
# Returns a dictionary with each dominant color mapped to its CSS3 color name

print palette(url="image_url", n=6, format="full")
# Returns the nested structure of each CSS3 color mapped to its parent CSS21 color along with hex codes

print palette(url="image_url", n=6, format="fullest")
# Returns everything above together
```

#### Use k-means Clustering for extracting dominant colors::

```python
print palette(url="image_url", n=6, mode="kmeans")
# Returns the list of dominant colors using k-means clustering algorithm (bit slower than the default method)
```
