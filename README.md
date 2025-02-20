# rmw_zenoh

[![build](https://github.com/ros2/rmw_zenoh/actions/workflows/build.yaml/badge.svg)](https://github.com/ros2/rmw_zenoh/actions/workflows/build.yaml)
[![style](https://github.com/ros2/rmw_zenoh/actions/workflows/style.yaml/badge.svg)](https://github.com/ros2/rmw_zenoh/actions/workflows/style.yaml)

A ROS 2 RMW implementation based on Zenoh that is written using the zenoh-cpp bindings.

## Design

For information about the Design please visit [design](docs/design.md) page.

## Requirements
- [ROS 2](https://docs.ros.org)

> Note: See available distro branches, eg. `jazzy`, for supported ROS 2 distributions.

## Setup

Build `rmw_zenoh_cpp`

>Note: By default, we vendor and compile `zenoh-cpp` with a subset of `zenoh` features.
The `ZENOHC_CARGO_FLAGS` CMake argument may be overwritten with other features included if required.
See [zenoh_cpp_vendor/CMakeLists.txt](./zenoh_cpp_vendor/CMakeLists.txt) for more details.

```bash
# replace <DISTRO> with ROS 2 distro of choice
mkdir ~/ws_rmw_zenoh/src -p && cd ~/ws_rmw_zenoh/src
git clone https://github.com/ros2/rmw_zenoh.git -b <DISTRO>
cd ~/ws_rmw_zenoh
rosdep install --from-paths src --ignore-src --rosdistro <DISTRO> -y
source /opt/ros/<DISTRO>/setup.bash
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
```

## Test

Make sure to source the built workspace using the commands below prior to running any other commands.
```bash
cd ~/ws_rmw_zenoh
source install/setup.bash
```

### Start the Zenoh router
> Note: Manually launching Zenoh router won't be necessary in the future.
```bash
# terminal 1
ros2 run rmw_zenoh_cpp rmw_zenohd
```

> Note: Without the Zenoh router, nodes will not be able to discover each other since multicast discovery is disabled by default in the node's session config. Instead, nodes will receive discovery information about other peers via the Zenoh router's gossip functionality. See more information on the session configs [below](#configuration).

### Terminate ROS 2 daemon started with another RMW
```bash
pkill -9 -f ros && ros2 daemon stop
```
Without this step, ROS 2 CLI commands (e.g. `ros2 node list`) may
not work properly since they would query ROS graph information from the ROS 2 daemon that
may have been started with different a RMW.

### Run the `talker`
```bash
# terminal 2
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
ros2 run demo_nodes_cpp talker
```

### Run the `listener`
```bash
# terminal 2
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
ros2 run demo_nodes_cpp listener
```

The listener node should start receiving messages over the `/chatter` topic.

## Configuration

By default, `Zenoh sessions` created by `rmw_zenoh` will attempt to connect to a Zenoh router to receive discovery information.
To understand more about `Zenoh routers` and `Zenoh sessions`, see [Zenoh documentation](https://zenoh.io/docs/getting-started/deployment/).

### Checking for a Zenoh router.
The `ZENOH_ROUTER_CHECK_ATTEMPTS` environment variable can be used to configure if and how a `Zenoh session` checks for the presence of a `Zenoh router`.
The behavior is explained in the table below.


| ZENOH_ROUTER_CHECK_ATTEMPTS |                                                 Session behavior                                                   |
|:---------------------------:|:------------------------------------------------------------------------------------------------------------------:|
|               0             |                                                             Indefinitely waits for connection to a Zenoh router.   |
|             < 0             |                                                                                        Skips Zenoh router check.   |
|             > 0             | Attempts to connect to a Zenoh router in `ZENOH_ROUTER_CHECK_ATTEMPTS` attempts with 1 second wait between checks. |
|            unset            |                                                                    Equivalent to `1`: the check is made only once. |

If after the configured number of attempts the Node is still not connected to a `Zenoh router`, the initialisation goes on anyway.  
If a `Zenoh router` is started after initialization phase, the Node will automatically connect to it, and autoconnect to other Nodes if gossip scouting is enabled (true with default configuratiuon).

### Session and Router configs
`rmw_zenoh` relies on separate configurations files to configure the `Zenoh router` and `Zenoh session` respectively.
For more information on the topology of Zenoh adopted in `rmw_zenoh`, please see [Design](#design).
Default configuration files are used by `rmw_zenoh` however certain environment variables may be set to provide absolute paths to custom configuration files.
The table below summarizes the default files and the environment variables for the `Zenoh router` and `Zenoh session`.
For a complete list of configurable parameters, see [zenoh/DEFAULT_CONFIG.json5](https://github.com/eclipse-zenoh/zenoh/blob/main/DEFAULT_CONFIG.json5).

|         |                                            Default config                                            |   Envar for custom config  |
|---------|:----------------------------------------------------------------------------------------------------:|:--------------------------:|
| Router  |  [DEFAULT_RMW_ZENOH_ROUTER_CONFIG.json5](rmw_zenoh_cpp/config/DEFAULT_RMW_ZENOH_ROUTER_CONFIG.json5)  |  `ZENOH_ROUTER_CONFIG_URI` |
| Session | [DEFAULT_RMW_ZENOH_SESSION_CONFIG.json5](rmw_zenoh_cpp/config/DEFAULT_RMW_ZENOH_SESSION_CONFIG.json5) | `ZENOH_SESSION_CONFIG_URI` |

For example, to set the path to a custom `Zenoh router` configuration file,
```bash
export ZENOH_ROUTER_CONFIG_URI=$HOME/MY_ZENOH_ROUTER_CONFIG.json5
```

### Connecting multiple hosts
By default, all discovery traffic is local per host, where the host is the PC running a `Zenoh router`.
To bridge communications across two hosts, the `Zenoh router` configuration for one the hosts must be updated to connect to the other `Zenoh router` at startup.
This is done by specifying an endpoint in host's `Zenoh router` configuration file to as seen below.
In this example, the `Zenoh router` will connect to the `Zenoh router` running on a second host with IP address `192.168.1.1` and port `7447`.

```json5
{
  connect: {
    endpoints: ["tcp/192.168.1.1:7447"],
  },
}
```

> Note: To connect multiple hosts, include the endpoints of all `Zenoh routers` in the network.

### Logging

The core of Zenoh is implemented in Rust and uses a logging library that can be configured via a `RUST_LOG` environment variable.
This variable can be configured independently for each Node and the Zenoh router.
For instance:
- `RUST_LOG=zenoh=info` activates information logs about Zenoh initialization and the endpoints it's listening on.
- `RUST_LOG=zenoh=info,zenoh_transport=debug` adds some debug logs about the connectivity events in Zenoh.
- `RUST_LOG=zenoh=info,zenoh::net::routing::queries=trace` adds some trace logs for each query (i.e. calls to services and actions).
- `RUST_LOG=zenoh=debug` activates all the debug logs.

For more information on the `RUST_LOG` syntax, see https://docs.rs/env_logger/latest/env_logger/#enabling-logging.

### Known Issues

### Crash when program terminates

When a program terminates, global and static objects are destructed in the reverse order of their
construction.
The `Thread Local Storage` is one such entity which the `tokio` runtime in Zenoh uses.
If the Zenoh session is closed after this entity is cleared, it causes a panic like seen below.

```
thread '<unnamed>' panicked at /rustc/aedd173a2c086e558c2b66d3743b344f977621a7/library/std/src/thread/local.rs:262:26:
cannot access a Thread Local Storage value during or after destruction: AccessError
```

This can happen with `rmw_zenoh` if the ROS 2 `Context` is not shutdown explicitly before the
program terminates.
In this scenario, the `Context` will be shutdown inside the `Context`'s destructor which then closes the Zenoh session.
Since the ordering of global/static objects is not defined, this often leads to the above panic.

The recommendation is to ensure the `Context` is shutdown before a program terminates.
One way to ensure this is to call `rclcpp::shutdown()` when the program exits.
Note that composable nodes should *never* call `rclcpp::shutdown()`, as the composable node container will automatically do this.

For more details, see https://github.com/ros2/rmw_zenoh/issues/170.
