#!/usr/bin/env python3
"""Empty charm for publishing Bookinfo shared libraries.

This charm does not deploy any workload. It exists solely to
publish shared libraries for the Bookinfo application charms.
"""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import BlockedStatus

logger = logging.getLogger(__name__)


class BookinfoLibsK8sCharm(CharmBase):
    """Charm for publishing Bookinfo shared libraries."""

    def __init__(self, *args):
        super().__init__(*args)
        
        # Set blocked status to indicate this charm doesn't deploy workloads
        self.unit.status = BlockedStatus(
            "This charm is for library publishing only. "
            "It does not deploy any workload."
        )
        
        # Log warning if someone tries to deploy this
        logger.warning(
            "bookinfo-libs-k8s is a library charm and should not be deployed. "
            "Use 'charmcraft fetch-lib' to consume its libraries."
        )


if __name__ == "__main__":
    main(BookinfoLibsK8sCharm)
