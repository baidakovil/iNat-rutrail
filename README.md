# iNat-rutrail

## Description
Aim of this project is to create 89 iNaturalist project (number at early 2024), with each of them linked to one of RuTrail tourist trails. Each project should have map with polygons, shaping areas around tourist trail.  

Having this, each tourist can see which plants and animals, fungi and lichens it can see on the trail.

How does it look on iNaturalist:  
<img src="https://github.com/baidakovil/iNat-rutrail/blob/5456d07fc6a6b5d28b06db4110a5b1fbfb1b5c64/assets/readme/route-logo-sample.png" width=73%></img>  
<img src="https://github.com/baidakovil/iNat-rutrail/blob/5456d07fc6a6b5d28b06db4110a5b1fbfb1b5c64/assets/readme/route-map-sample.png" width=75%></img>

Link to iNaturalist umbrella project:  
https://www.inaturalist.org/projects/rutrail-013aac38-8df3-4c23-a690-b2b2be7955f1


## Scripts

### inat-rutrail_prepare_text.py

Script to create iNat-project textual descriptions. 

Dependencies:  
**transliterate** - used to create latin trail names  
**translate** - used to translate project descriptions to English

Note: description of the project [Мончегорские тропы и Ниттис — Маркированный маршрут RuTrail](https://www.inaturalist.org/projects/rutrail-01f33481-7d7b-45e4-833c-33e3cc07312c) is compilation of six others texts.

### inat_rutrail_generate_polygon.py

Main script to create kml-shapes (polygons) for iNaturalist from gps tracks, provided RuTrail.  

This script can take several tracks to create shape. Since many routes contains additional routes (bypasses, seasonal tracks, trails to sights, variants), this additional routes were downloaded from nakarte.me service, by links provided on rutrail.org trail pages. This files not included in the project.

There is some features:
- working with *.gpx of *.kml input files
- adding several tracks to create polygon. Both adding files or polygons inside single file supported. This functionality mainly provided by Clipper library
- adjusting distance from track to polygon
- maintain level of siplicity (distance error) ot the polygon. Two optional steps here: simplification of the track and/or simplification of the polygon
- removing unnecessary shape circles from resulting shape
- "rotating" start/end of resulting polygons, to create circle polygon with single sequence, as iNaturalist supports only these
- plotting pdfs with both simplificated and original trails

Dependencies:  
**pyclipper** - Cython wrapper of the Clipper library. Used to create shape around tracks
**pyproj** - Python interface to PROJ, cartographic projections and coordinate transformations library. Used to translate longitude-lattitude coordinates to Mercator coordinates, where pyclipper will work (lat-lon is not equidistance coordinates)
**pandas** - used for data manipulations to prepare data to debug plotting
**matplotlib** - used to make debug PDF plots

Note: polygon (shape map) of the project [Мончегорские тропы и Ниттис — Маркированный маршрут RuTrail](https://www.inaturalist.org/projects/rutrail-01f33481-7d7b-45e4-833c-33e3cc07312c) is made-by-hand compilation of two other separated tracks (iNaturalist supports several shapes in single kml-file).


### inat_rutrail_parse_rutrail.py
Script to load track information: description, track, banner photo.

Dependencies:  
**requests** - library to load web-pages
**bs4** -  beautifulsoup4, library that makes it easy to scrape information from web pages. Used to parse RuTrail web-page

### inat_rutrail_stamp_banner.py
Script to create iNat project banner with RuTrail logo.

Dependencies:  
**PIL** - Python Imaging Library. Used to crop images and paste rutrail logo on banner photo
	
### inat_rutrail_stamp_logo.py
Script to create iNat project unique icon with first letters of latin trail name. I found this to be nice.

Dependencies:  
**PIL** - Python Imaging Library. Used to paste text on project logos
	

## Copyright / Responsibility / Liability note

Author of this repository is not associated with RuTrail.  
It have no intensions to make commercial with it.  
Aims of this project is:
* popularization of tourism
* popularization of the healthy lifestyle
* popularization of the responsible attitude to nature