import re
from uuid import uuid4


def unique_string_gen():
    return uuid4().hex


def unique_id():
    return uuid4()


def filter_dict(keys, old_dict, exclude=False):
    """Exclude or Include some keys from the 'old dictionary' and return them in new dict."""
    if exclude:
        new_dict = old_dict
        for k in keys:
            del new_dict[k]
        return new_dict
    else:
        return {k: old_dict[k] for k in keys}


def get_offset_limit(page=0, page_size=5):
    """Return offset and limit for db pagination, page_size is equal to limit and used in formula."""
    skip = page * page_size
    return skip, page_size


def email_censor(email: str):
    email_list = email.split("@")
    name = email_list[0]

    f = name[:3]
    l = name[-3:]
    
    return f + "***" + l + "@" + email_list[1]