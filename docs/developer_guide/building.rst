Building USD-Bio
================

Development Setup
-----------------

1. Install prerequisites (see :doc:`../user_guide/installation`)
2. Configure CMake with development options:

.. code-block:: bash

   cmake --preset=<preset> -DBUILD_TESTS=ON -DBUILD_USD_BIO=ON

3. Build the project:

.. code-block:: bash

   cmake --build out/build/<preset>

Running Tests
-------------

After building with ``BUILD_TESTS=ON``:

.. code-block:: bash

   cd out/build/<preset>
   ctest

Building Documentation
----------------------

Install Python dependencies:

.. code-block:: bash

   pip install -r docs/requirements.txt

Generate Doxygen XML:

.. code-block:: bash

   doxygen Doxyfile

Build HTML documentation:

.. code-block:: bash

   sphinx-build docs docs/_build/html

View documentation by opening ``docs/_build/html/index.html``.
