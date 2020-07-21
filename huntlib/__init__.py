#!/usr/bin/env python3

import huntlib.util as util
from huntlib.decorators import future_warning
import warnings 

__all__ = ['entropy', 'entropy_per_byte', 'promptCreds', 'edit_distance', 'flatten']

@future_warning("The huntlib.entropy() function has been moved to huntlib.util.entropy(). Please update your code. This compatibility will be removed in a future release.")
def entropy(*args, **kwargs):
    return util.entropy(*args, **kwargs)


@future_warning("The huntlib.entropy_per_byte() function has been moved to huntlib.util.entropy_per_byte(). Please update your code. This compatibility will be removed in a future release.")
def entropy_per_byte(*args, **kwargs):
    return util.entropy_per_byte(*args, **kwargs)


@future_warning("The huntlib.promptCreds() function has been moved to huntlib.util.promptCreds(). Please update your code. This compatibility will be removed in a future release.")
def promptCreds(*args, **kwargs):
    return util.promptCreds(*args, **kwargs)


@future_warning("The huntlib.edit_distance() function has been moved to huntlib.util.edit_distance(). Please update your code. This compatibility will be removed in a future release.")
def edit_distance(*args, **kwargs):
    return util.edit_distance(*args, **kwargs)


