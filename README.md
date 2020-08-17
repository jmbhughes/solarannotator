# Solar Annotator
[![CodeFactor](https://www.codefactor.io/repository/github/jmbhughes/solarannotator/badge)](https://www.codefactor.io/repository/github/jmbhughes/solarannotator)
[![PyPI version](https://badge.fury.io/py/solarannotator.svg)](https://badge.fury.io/py/solarannotator)

A tool for annotating solar images with themes. 

## Install
```pip install solarannotator```

## Running and uasage
Execute from the terminal after installing by running 
```SolarAnnotator```

This launches the main software:
![Screenshot of tool](https://github.com/jmbhughes/solarannotator/blob/master/screenshot.png)

On the left hand side, you will see a preview that can be maniuplated with the controls below. 
It allows for viewing different SUVI channels with different configurations, e.g. one color versus three color. 
The preview controls allow you to select the minimum and maximum percentile shown as well as scale
the image by raising all pixels to the selected power.

You interact by drawing on the preview image to create new regions in the thematic map. You can also
relabel those patches by left-clicking in the thematic map with a new theme selected. Finally, you can see
boundaries of regions from the thematic map back in the preview image by right clicking the thematic map. 

## Future
This tool is still under development. There are many features coming. 
- [x] Ability to scale a single color image
- [x] Ability to scale in a three color image   
- [x] Right click on a region in the thematic map and see its boundary in the preview
- [x] Left click on a region in the thematic map to re-annotate all the contiguous pixels
- [x] Undo annotations
- [ ] Redo annotations
- [ ] Overlay HEK and other pre-determined annotations
- [ ] Multiple normalization options
- [x] Differentiate save and save as
- [x] Add color legend to radio buttons
- [ ] Robustify the thematic map io for better metadata passing