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

* ~~Groundplot - tooltip or popup (after click on the map), showing the list of stations covering that location~~
* ~~Groundplot - same as above, highlight the FOVs~~


![2024-04-05 13_12_29-GMN Meteor Map](https://github.com/satmonkey/GMN_meteormap/assets/5328519/c50da0d5-9344-4afe-81d1-35cea3641627)
![2024-04-05 13_12_42-GMN Meteor Map](https://github.com/satmonkey/GMN_meteormap/assets/5328519/004bff65-9b6d-4f1d-b1d1-2697b056ccf0)
![2024-04-05 13_12_58-GMN Meteor Map](https://github.com/satmonkey/GMN_meteormap/assets/5328519/55336e44-89ee-4a16-8f28-e952f1a70c5c)



