# Zwo Maker #

The Zwift workout maker for running. ZwoMaker is a command line tool to create
a Zwift workout for your running training. Since the official Zwift workout
creator only works for cycling, ZwoMaker can help you by building a file
from a simple specification.

ZwoMaker is a command line tool. Nothing fancy here, but no need to write an
file by hand anymore.

## Installation ##

You need python 3.x on your machine.

## Running ##

See help `python3 zwomaker.py -h`

## Spec file ##

The spec file is a simple text file. Each line will be parsed and converted
to an Zwift xml element. The pace are enter as % of your 1 mile PR. 
The following element are supported:

|Tag|Description|Format|Example|
|---|---|---|---|
|N|Workout name|`N [name of the workout]`| N My first workout |
|W|Warmup|`W [Distance] [MiP%]:[MiP%]`| W 1000 30:40 |
|I|Intervals|`I [Repeat] [Distance]:[RestDistance] [MiP%]:[Rest MiP%] [Cadence]` | I 2 1000:200 75:20 180 |
|S|SteadyState|`S [Distance] [MiP%] [Cadence]` | S 2000 65 180 |
|R|Ramp|`R [Distance] [MiP%]:[MiP%] [Cadence]` | R 2000 62:67 180 |
|C|Cool down|`C [Distance] [MiP%]:[MiP%]` | C 800 40:20 |

For a 3x 800m with a 4x200m primer set, your spec file would look like this:

```
N 3x800 @ 10K pace
W 2000 40:60
I 4 200:100 75:50 180
I 3 800:200 88:50 180
C 1000 60:40
```

In addition, ZwoMaker will insert messages at every 100m throughout your
workout. The messages are read from a definition file (-m parameter). Three
message types are possible using the following line prefix:

* `M W` - message for warmup
* `M I` - message for intervals, including ramp and steady state
* `M C` - message for cool down

## Examples ##

There are examples available if you need some inspiration to get you
started. The spec files are under the example folder.