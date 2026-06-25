"""
usdbio_env -- lightweight environment helpers for usd-bio scripts.

Zero USD imports; safe to import before the OpenUSD environment is loaded.
"""

import os


def get_data_dir() -> str:
    """Return the root path to the ShinobuLab data directory.

    Reads ``USDBIO_DATA_DIR`` from the environment.  Raises
    :class:`EnvironmentError` with an actionable message when the variable
    is unset so every consumer fails at this single call-site rather than
    producing a cryptic ``FileNotFoundError`` deep inside a script.

    Example::

        from usdbio_env import get_data_dir
        pdb = os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")
    """
    data_dir = os.environ.get("USDBIO_DATA_DIR")
    if not data_dir:
        raise EnvironmentError(
            "USDBIO_DATA_DIR is not set. "
            "Export the path to your ShinobuLab data directory before running usd-bio scripts.\n"
            "  export USDBIO_DATA_DIR=/path/to/ShinobuLab"
        )
    return data_dir
