# BDTTrainingAnalysisLanguage

This repro is an experiment in [IRIS-HEP](http://iris-hep.org) analysis languages.

The code here will start from an ATLAS derivation (EXOT_15) and feed it into
a BDT training that can differentiate between MJ background and long-lived
particle signal in the jets. This is part of the CalRatio effort.

Goals:

- Python driver file that is clean and easy to read
- Loosely separate the front end from the back end server
- File data format agnostic at some level.
- Split analysis level back-end knowledge and ATLAS level back-end knowledge

Non-Goals:

- No attempt made to solve file-access (e.g. GRID dataset names, etc)
- No attempt is made to solve the local storage problem for temp files.
- Not trying to make the front-end be agnostic to the back-end data format.
- This version is not trying to be religious about any particular concept. This is a proof of principle.
- Not trying to hide some of the boiler plate in this version.
- Not (yet) attempting to run on a farm or large number of files, but will attempt to keep the design in mind because to be useful it clearly will have to.
- Everything is in a single repro - no attempt is made at building a separate library. Not yet. Eventually this should be multiple small useful packages.
- Making the user interface pythonic. This is a test to see if this can be done in python.

Above all, this is an experiment. It is based off many things learned in the [LINTQToROOT](https://github.com/gordonwatts/LINQtoROOT) project.

## Usage

Platform requirements:

- Python 3.7 (not sure exactly what version, but this is the version it was developed under)
- Docker (really should move to singularity if possible)
- pip install uproot jinja2
  - jinja2 is already part of anaconda3
- vsyscall implementation (on Linux hosts, this needs to be either native or emulated)


Tested on:

- Windows 10
- Arch Linux (x86_64 kernel version 4.20.13)

## Implementation

This will have to have C++ parts and Python (numpy) parts.
