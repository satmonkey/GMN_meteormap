# GMN meteormap
GMN Meteor Map is a multipurpose trajectory/orbit viewer:

https://www.meteorview.net

based on the data produced by the Global Meteor Network trajectory solver. For more information, visit:

https://globalmeteornetwork.org

https://globalmeteornetwork.org/data/traj_summary_data/daily/

To clone the repository, use:

`git clone https://github.com/satmonkey/GMN_meteormap`

To run the code, create the python virtual environment (tested on Python 3.10) and install the modules as mentioned in the requirements.txt.
Then, you can run the app e.g.:

`panel serve map3.py --static-dirs assets=assets --address 0.0.0.0 --port 8080 --allow-websocket-origin="*" --log-level debug`

Then, point your browser to: http://localhost:8080

This code contains a small sample database, enabling the code to run in a minimalistic way

TODO:

* Groundplot - tooltip or popup (after click on the map), showing the list of stations covering that location
* Groundplot - same as above, highlight the FOVs

