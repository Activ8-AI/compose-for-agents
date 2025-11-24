"""
Top-level package marker for MAOS modules.

This repository previously hosted multiple demo projects.  The new MAOS
automation artifacts (teamwork pipeline, action matrix wiring, etc.) live under
``modules`` to keep them isolated from the existing demos.  Import paths such as
``modules.teamwork_pipeline`` rely on this file to treat the directory as a
package.
"""

__all__ = ["teamwork_pipeline"]
