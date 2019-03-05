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
  - This is required by the old build of bash in the atlas/analysisbase image.
  - Depending on your kernel options, this may or may not work automatically. If not, try adding [`vsyscall=emulate`](https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/Documentation/admin-guide/kernel-parameters.txt?h=v4.19.26#n4908 "vsyscall kernel parameter documentation") to your kernel parameters at boot. If that doesn't work, make sure [`X86_VSYSCALL_EMULATION`](https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/arch/x86/Kconfig?h=v4.19.26#n1209 "vsyscall Kconfig option") is enabled in your kernel config.


Tested on:

- Windows 10
- Arch Linux (x86_64 kernel version 4.20.13)

## Implementation

This will have to have C++ parts and Python (numpy) parts.

### Backend Implentation

A new background is required to run on a different file. Or below the sheets, power it from a differet
file format.

Implementing a new executor isn't terribly hard. Here is an untested outline of what must be done.

1. The system finds the proper backend code through the AST note that contans tje get_execcutor method. See the file `xAODLib/AtlasEventStream.py` for this file.

1. This returns the executor found in the bottom of the `atlas_xaod_executor.py`. This drives everything. Almost everything is done in the evaluate method (there are a bunch of helpers). There are two stages.

    1. The qv.visit(ast) is the main line. This starts the traversal of the AST that we need to turn into code. The visitor is based on `python`'s `ast.NodeVisitor` class. As it goes, it tracks what it is looking at. This is tricky. For example, how the `SelectMany` node translates from a collection to a sequence of its items.

    1. The output file is generated using the template engine `jinj2` - though anything can be used.

1. Finally, the code is run in a docker container which maps a temp script directory and the directory containing the data file.

1. The results of this have to be given back to the calling source code. THis is currently a fake burried in the executor.
