# Seed of the World

A project to try to determine what is the seed of our planet Earth.

## Idea

Divide the world into a grid and assign a value to that topographic location. The value can represent things such as elevation or check for body of water.
Use these values to create a representation of the world. We can maybe try to create a seed that can be used to generate the world following a set of rules.

## Lagitudes and latitudes

The world is divided into a grid of 360 degrees of longitude and 180 degrees of latitude. So the grid count would be defined as:

$$
\text{Number of blocks} = \left(\frac{360}{l}\right) \times \left(\frac{180}{l}\right)
$$
where \( l \) is the size of the square side in degrees.

## Elevation

We can use the elevation data where the lowest point in meters is the 0 value and the highest point is 1. So the elevation of "sea level" would not necessarily be 0 but rather a value in between 0 and 1.

## Terrain

Depending on the data source we use, we can apply an analysis of a print of the map to determine the type of terrain. We can use a set of different types of terrain depending on the kind of information we can get.

## Links

Global elevation Map - https://www.arcgis.com/apps/Profile/index.html?appid=f0a2a2a3e1964129b22c715e31282f6c

The TanDEM-X 90m Digital Elevation Model - https://geoservice.dlr.de/web/dataguide/tdm90/

TessaDEM API - https://tessadem.com/ - https://tessadem.com/elevation-api/