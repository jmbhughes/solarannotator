# Solar Annotator

A tool for annotating solar images with themes. 

## Install
```pip install solarannotator```

## Running and uasage
Execute from the terminal after installing:
```SolarAnnotator```

This launches the main software:
![Screenshot of tool](https://github.com/jmbhughes/solarannotator/blob/master/screenshot.png)

On the left hand side, you will see a preview that can be maniuplated with the controls below. 
It allows for viewing different SUVI channels with different configurations, e.g. one color versus three color. 
When you wish to annotate, simply draw on top of this window after selecting the 
desired theme radio button. 

## Future
This tool is still under development. There are many features coming. 
- [ ] Ability to scale a single color image
- [x] Ability to scale in a three color image   
- [ ] Right click on a region in the thematic map and see its boundary in the preview
- [ ] Left click on a region in the thematic map to re-annotate all the contiguous pixels
- [ ] Undo and redo annotations
- [ ] Overlay HEK and other pre-determined annotations
- [ ] Multiple normalization options
- [x] Differentiate save and save as
- [ ] Add color legend to radio buttons
- [ ] Robustify the thematic map io for better metadata passing
- [ ] 