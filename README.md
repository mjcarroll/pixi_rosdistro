A simple pixi-rosdistro builder.

```
# Install Pixi

curl -fsSL https://pixi.sh/install.sh | bash

# Clone this

git clone https://github.com/mjcarroll/pixi_rosdistro
cd pixi_rosdistro

# Install dependencies
pixi install

# Sync your workspace (distro can be changed via ros.toml)
pixi run sync

# Build and test your workspace
pixi run colcon build
pixi run colcon test

# Clean up stuff (build/install/log)
pixi run clean
```
