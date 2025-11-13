Installation
============

Prerequisites
-------------

- CMake 3.20 or higher
- C++20 compatible compiler
- vcpkg for dependency management
- OpenUSD (installed via vcpkg)

Building from Source
--------------------

Clone the repository:

.. code-block:: bash

   git clone --recursive https://github.com/LittleCoinCoin/usd-bio.git
   cd usd-bio

Configure and build:

.. code-block:: bash

   cmake --preset=<preset>
   cmake --build out/build/<preset>

The library will be built in the output directory.
