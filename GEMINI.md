# ROS 2 Rolling Source Workspace (Pixi)

This project provides a reproducible development environment for building **ROS 2 Rolling** from source using [Pixi](https://pixi.sh). It manages system dependencies, build tools, and the ROS 2 source tree across Linux, Windows, and macOS.

## Project Overview

*   **Technologies:** Pixi (Conda/PyPI), ROS 2 Rolling, Colcon, VCS, CMake, Ninja, Rust, Python.
*   **Purpose:** Simplify the complex process of building ROS 2 from source by using Pixi to provide a consistent cross-platform environment without requiring global system changes.
*   **Architecture:**
    *   `pixi.toml`: Central configuration for dependencies, environment variables, and tasks.
    *   `ros2.repos`: Defines the ROS 2 repositories to be cloned into the `src/` directory.
    *   `colcon_defaults_*.yaml`: Platform-specific build and test configurations for `colcon`.
    *   `patches/`: Contains Python scripts for patching source code that requires fixes during the build process (e.g., Ogre, Gazebo).

## Building and Running

The project leverages `pixi tasks` to automate the workflow.

### Initial Setup
1.  **Install Pixi:** If not already installed, visit [pixi.sh](https://pixi.sh).
2.  **Fetch Source Code:**
    ```bash
    pixi run fetch
    ```
    This creates the `src/` directory and populates it with ROS 2 repositories listed in `ros2.repos`.

### Development Workflow
*   **Patch Source:**
    ```bash
    pixi run patch
    ```
    Applies necessary fixes to the source code (automatically called by `build`).
*   **Build the Workspace:**
    ```bash
    pixi run build
    ```
    Compiles all packages using `colcon`. It uses `Ninja` as the build generator and `sccache` for faster subsequent builds.
*   **Run Tests:**
    ```bash
    pixi run test
    ```
*   **Clean Workspace:**
    ```bash
    pixi run clean
    ```
    Removes `build/`, `install/`, and `log/` directories.

### Interactive Shell
To enter the development environment with all ROS 2 tools and dependencies available:
```bash
pixi shell
```

## Development Conventions

*   **Cross-Platform Support:** The environment is designed for `linux-64`, `win-64`, and `osx-arm64`. Platform-specific flags are handled in `pixi.toml`.
*   **Dependency Management:**
    *   **Conda:** Used for system libraries (e.g., `spdlog`, `yaml-cpp`), compilers (`compilers`), and build tools (`cmake`, `ninja`, `rust`).
    *   **PyPI:** Used for ROS-specific tools (e.g., `colcon-core`, `ament-lint`).
*   **Build System:** `colcon` is used with `merge-install` enabled.
*   **Linkers:** High-performance linkers are used where possible (`mold` on Linux, `lld` on macOS).
*   **Caching:** `sccache` is enabled for C/C++ and Rust to speed up builds across different environment configurations.
*   **Skipped Packages:** Some packages (like `lttng`-related tracing tools) are explicitly skipped in `colcon_defaults_linux.yaml` due to missing dependencies in the conda-forge channel.
