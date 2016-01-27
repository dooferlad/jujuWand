# jujuWand
A bunch of tools for debugging and automating Juju

These scripts are here because it is good to share. This isn't my finest work;
it isn't PEP8 complient, it isn't well (at all?) commented and it may not work. You have been warned.

## state.py
Runs through 1+ logs and outputs a table showing what was connected to state servers and when.

In order to use this you will need to hack the hard coded stuff until I make it accept a configuration file.
This is probably:
 * main():
  * input_files
  * output_file (not that I have looked at this output in ages - it may be useless)
  
 * LogChomper
  * update
   * machine_names: Used to translate IP addresses to human readable names in the printed output.
   * translate: Used to translate the IP address of a state server to the index of the connection string in the output.

## wand.py
A very lightweight wrapper around the Juju CLI and the local shell.

While I mostly use this by importing it and using it as an API, it will currently, if just run as a script,
 1. set up a high availability Juju state server cluster in my EC2 account with an ubuntu charm deployed
 2. kill a state server
 3. re-run ensure-availability to heal Jujus state server cluster.

This happens to be what I was playing with at the time. It will probably change or bit-rot.

## realtime_logs.py
If you kill random machines by shutting them down, sometimes it helps to be reading their log files before they
go away!

This script will connect to evey machine in your Juju environment anc capture the output of
tail -f /var/log/juju/machine-?.log. It can miss stuff and if it reconnects to a machine for some reason you will
get duplication. It is just better to have something rather than nothing when debugging sometimes.

## time_check.py
Looks through a Juju log to check for timestamps going in the wrong direction. This does sometimes happen when the
logger target has strange buffering. I didn't know this when I wrote this script and I had spotted it happening and
was investigating. Mostly here for historical curiosity.

You can trust the timestamps in Juju logs - Juju itself adds a timestamp to the log messages before sending them to
whatever is consuming the logs.

## watch.py
Outputs a timestamped list of changes from the current Juju environment that I happened to have been interested in
at the time of writing, for example:
```
2015-11-06 15:37:15.329161 1: started
2015-11-06 15:37:15.329202 0: down
2015-11-06 15:37:15.329217 3: started
2015-11-06 15:37:15.329232 2: started
2015-11-06 15:37:15.329251 1 ubuntu: started
2015-11-06 15:37:15.329272 1 ubuntu workload-status:
```

Leave it running to see when machines and charms appear and disappear and when a charms workload-status changes.