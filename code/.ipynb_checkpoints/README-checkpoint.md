# Data Overview

## Maximum Data Sizes

- EV: 215 participants, 100 when filtering out social trial participants
- HH: 4225 residentials

## Folder Structure

- code
- data
- data/aggregate
- data/pv/raw
- data/pv/processed
- etc.

# Sampling and Units

## Raw Data

- HH: 1/2 hour, kWh
- EV: seconds,  kW
- PV: 1 hour,   kW  
- DA: 1 hour,   EUR/MWh
- RG: 1/4 hour, MW

## Resampling

Data was resampled to a common sampling interval of 1/4 hour.


# Predictions

(- Suggestion: Use one day ahead predictions. ausser EV?)

TODO: Do it yourself if you like like we did it for PV for RG, HH?

- DA: evtl. gehandelte Werte als Realisierungen der DA
- EV prediction: ihr problem, nichts von uns vorgegeben.

# Alert

TODO: Data was not checked completly for logical consistency? See as part of the uncertainty. :-)


# Feedback

Please contact us, when you find errors or have ideas for improvements.


# Contact

Dr. Klaus Rheinberger
[Research Center Energy](https://www.fhv.at/en/research/energy/)
[FH Vorarlberg University of Applied Sciences](https://www.fhv.at/)
Hochschulstrasse 1
6850 Dornbirn
Austria

Tel.: +43 5572 792 3811
Email: [klaus.rheinberger@fhv.at](mailto:klaus.rheinberger@fhv.at)
