# Zwo Maker #

The Zwift workout maker for running. ZwoMaker is a command line tool to create
a Zwift workout for your running training. Since the official Zwift workout
creator only works for cycling, ZwoMaker can help you by building a file
from a simple specification.

ZwoMaker is a command line tool. Nothing fancy here, but you do not need to
write an XML file by hand by guessing which field works and test them on 
the treadmill. The [zwift-workout-file-reference](https://github.com/h4l/zwift-workout-file-reference/blob/master/zwift_workout_file_tag_reference.md) project on github is probably the best documentation about elements and attributes 
found in a Zwift workout file.

ZwiftInsider has a how-to page for [building your own XML files for running
workouts](https://zwiftinsider.com/create-run-workouts/).
After making half dozen of those manually, with messages inserted in each
interval by following the distance offset, it may come appalling to you. 
Zwomaker tries to solve this problem by offering a simpler format and 
handling the insertion of messages for you.

## Installation ##

You need python 3.x on your machine.

## Usage ##

Create a zwift workout file my_workout.zwo from a spec file my_workout.zwospec:

```bash
> python3 zwomaker.py -s ./my_workout.zwospec -o my_workout.zwo
```

See help `python3 zwomaker.py -h`

ZwoMaker does not copy your file to your Zwift account. You have to follow
[these instructions](https://support.zwift.com/hc/en-us/articles/115005558866?utm_source=ericschlange&utm_campaign=zwift_cycling_affiliate_ericschlange_apr19&utm_medium=affiliate) to make them available on your device. Once there are
copied to one of your device, Zwift will synchronize them to all your
devices.

## Spec file ##

The spec file is a simple text file. Each line will be parsed and converted
to an Zwift XML element. The pace are written as % of your 1 mile best time. 
The following tags are supported:

|Tag|Description|Format|Example|
|---|---|---|---|
|N|Workout name|`N [name of the workout]`| N My first workout |
|T|Tag name|`T [Name of the tag]`| T PersonalPlan|
|W|Warmup|`W [Distance] [MiP%]:[MiP%]`| W 1000 30:40 |
|I|Intervals|`I [Repeat] [Distance]:[RestDistance] [MiP%]:[Rest MiP%] [Cadence]` | I 2 1000:200 75:20 180 |
|S|SteadyState|`S [Distance] [MiP%] [Cadence]` | S 2000 65 180 |
|R|Ramp|`R [Distance] [MiP%]:[MiP%] [Cadence]` | R 2000 62:67 180 |
|C|Cool down|`C [Distance] [MiP%]:[MiP%]` | C 800 40:20 |

For a 3x 800m with a 4x200m primer set, your spec file would look like this:

```text
N 3x800 @ 10K pace
W 2000 40:60
I 4 200:100 75:50 180
I 3 800:200 88:50 180
C 1000 60:40
```

In addition, ZwoMaker will insert a message at every 100m throughout your
workout. The messages are read from a definition file (-m parameter). Three
message types are possible using the following line prefix:

* `M W` - message for warmup
* `M I` - message for intervals, including ramp and steady state
* `M C` - message for cool down

Note that interval messages will be repeated (circular reading) if your
workout has more 100's available than the count of messages.

## Examples ##

There are examples available if you need some inspiration to get you
started. The spec files are under the example folder.

## Speed ##

Using your best time over a mile is not an usual reference for most of the
people. This table gives a rough estimate of different distance pace based 
on the % of your mile pace.

|Distance | Mile pace % |
|---|---|
|5K|93%|
|10K|88%|
|Half-marathon|80%|
|Marathon|75%|
