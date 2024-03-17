# GMN_meteormap
GMN Meteor Map is a multipurpose trajectory/orbit viewer, based on the data produced by GMN trajectory solver at the UWO, Canada

For more information, visit:

https://globalmeteornetwork.org

https://globalmeteornetwork.org/data/traj_summary_data/daily/

To clone the repository, use:

`git clone https://github.com/satmonkey/GMN_meteormap`

To run the code, install the modules as mentioned in the requirements.txt
Then, you can run the app e.g.:

`panel serve map3.py --static-dirs assets=assets --address 0.0.0.0 --port 8080 --allow-websocket-origin="*" --reuse-sessions --log-level debug`

Then, point your browser to: http://localhost:8080

This code contains a small sample database, enabling the code to run in a minimized way
