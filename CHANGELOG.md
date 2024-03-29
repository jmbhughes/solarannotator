# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), 

## [0.3.1]
### Fixed
* Removes interpolation from thematic map display that was causing a weird outline

## [0.3.0]
### Added
* Support for GONG
### Fixed
* Bug that did not prompt "save as" for new files

## [0.2.15]
### Fixed
* Should save thematic maps as uint8 instead of a larger float format

## [0.2.14]
### Changed
* Only has support for Matplotlib's pyqt5 backend now. 

## [0.2.13]
### Changed
* GUI has a window title of "SolarAnnotator" that gets update with the current file's time when loaded,
previously did not work when a new image was made. Now it does.

## [0.2.12]
### New
* GUI has a window title of "SolarAnnotator" that gets update with the current file's time when loaded
* Minimzie and maximize buttons

## [0.2.11]
### Changed
* GUI no longer has to stay on top of other windows

## [0.2.10]
### Fixed
* Normalization now adjusts to spread the data over the entire data range

## [0.2.9]
### Added
* Added back relabeling by left click after bug fix

### Changed
* Switched to tight layout for better space usage in annotation window

## [0.2.8]
### Removed
* Temporarily removed relabeling by left click on thematic map due to bug

## [0.2.7]
### Added
* Program prompts the user to save before exiting

### Changed
* Preview controls now have three decimals of precision for min, max, and scale
* Thematic map metadata is more complete

### Fixed
* Solar north is now up instead of down.
* Recognizes correctly when a thematic map is initialized

## [0.2.6]
### Added
* Warning box if composite data does not exist
* Scaling for single color images
* Undo of thematic map edits
* Added colored theme background for theme radio buttons
* Added prompting box for downloads
* Font color for theme radio button changes depending on darkness of theme color, e.g. white for black backgrounds

### Changed
* Resized the thematic map annotator window

## [0.2.5]
### Added
* Left click on the thematic map relabels the contiguous region
* Right click on the thematic map draws boundaries on the preview image

## [0.2.4]
First stable release. Not all features added. 

[0.3.1]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.3.1
[0.3.0]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.3.0
[0.2.15]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.15
[0.2.14]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.14
[0.2.13]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.13
[0.2.12]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.12
[0.2.11]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.11
[0.2.10]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.10      
[0.2.9]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.9
[0.2.8]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.8
[0.2.7]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.7
[0.2.6]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.6
[0.2.5]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.5 
[0.2.4]: https://github.com/jmbhughes/solarannotator/releases/tag/v0.2.4