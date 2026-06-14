"""
insta_pruner
------------
A Python library that unfollows accounts from a provided list on Instagram,
with influencer filtering and live logging.

Usage:
    from insta_pruner import Pruner

    pruner = Pruner(
        usernames_file="non_followers.txt",
        threshold=5000,
        inactive_months=6
    )
    pruner.run()
"""

from .pruner import Pruner

__version__ = "0.1.2"
__all__ = ["Pruner"]
